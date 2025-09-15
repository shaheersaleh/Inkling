from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models import Note, Subject
from app import db
from app.services.text_extraction import TextExtractionService
from app.services.ai_classification import SubjectClassificationService
from app.services.vector_embeddings import VectorEmbeddingService
import os
import logging
from datetime import datetime
import uuid
import logging

notes_bp = Blueprint('notes', __name__)

# Initialize services
text_extraction_service = TextExtractionService()
classification_service = SubjectClassificationService()
vector_service = VectorEmbeddingService()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, user_id, subject_name=None):
    """Save uploaded file with organized naming convention"""
    if file and allowed_file(file.filename):
        # Create secure filename
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        
        # Create organized filename: user_id/subject/date_uuid.ext
        date_str = datetime.now().strftime('%Y%m%d')
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{date_str}_{unique_id}.{file_extension}"
        
        # Create directory structure
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(user_id))
        if subject_name:
            upload_dir = os.path.join(upload_dir, secure_filename(subject_name))
        
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        # Return both full path and relative path
        relative_path = os.path.relpath(file_path, current_app.config['UPLOAD_FOLDER'])
        return file_path, relative_path
    return None, None

@notes_bp.route('/notes')
@login_required
def list_notes():
    page = request.args.get('page', 1, type=int)
    subject_id = request.args.get('subject_id', type=int)
    search_query = request.args.get('q', '')
    
    # Base query
    query = Note.query.filter_by(user_id=current_user.id)
    
    # Apply filters
    if subject_id:
        query = query.filter_by(subject_id=subject_id)
    
    if search_query:
        # Use vector search if available, otherwise fall back to SQL search
        if vector_service.enabled:
            search_results = vector_service.search_notes(
                query=search_query,
                user_id=current_user.id,
                n_results=50
            )
            note_ids = [result['note_id'] for result in search_results]
            if note_ids:
                query = query.filter(Note.id.in_(note_ids))
            else:
                # No semantic matches found
                query = query.filter(False)  # Return empty result
        else:
            # Fallback to SQL text search
            query = query.filter(
                Note.title.contains(search_query) | 
                Note.content.contains(search_query)
            )
    
    # Pagination
    notes = query.order_by(Note.updated_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    # Get all subjects for filter dropdown
    subjects = Subject.query.filter_by(user_id=current_user.id).all()
    
    return render_template('notes/list.html', 
                         notes=notes, 
                         subjects=subjects,
                         current_subject_id=subject_id,
                         search_query=search_query)

@notes_bp.route('/notes/create', methods=['GET', 'POST'])
@login_required
def create_note():
    if request.method == 'POST':
        image_file = request.files.get('image')
        
        if not image_file or not image_file.filename:
            flash('Please upload an image', 'error')
            return render_template('notes/create.html', subjects=get_user_subjects())
        
        # Get user subjects for classification
        user_subjects = Subject.query.filter_by(user_id=current_user.id).all()
        subject_names = [s.name for s in user_subjects]
        
        if not subject_names:
            flash('Please create at least one subject before uploading notes', 'error')
            return redirect(url_for('subjects.list_subjects'))
        
        # Save uploaded image first (without subject folder since we don't know yet)
        result = save_uploaded_file(image_file, current_user.id)
        
        if not result:
            flash('Failed to upload image', 'error')
            return render_template('notes/create.html', subjects=get_user_subjects())
        
        full_path, relative_path = result
        
        # Extract and clean text from image
        extracted_text, confidence_score = text_extraction_service.extract_text_from_image(full_path)
        
        if not extracted_text or extracted_text.startswith('Error') or extracted_text == "No text found in image":
            flash('No text could be extracted from the image', 'error')
            # Clean up uploaded file
            import os
            if os.path.exists(full_path):
                os.remove(full_path)
            return render_template('notes/create.html', subjects=get_user_subjects())
        
        # Use multi-subject classification to create multiple notes if needed
        if classification_service.enabled:
            classification_results = classification_service.classify_multi_subject_text(
                extracted_text, subject_names
            )
            logging.info(f"Classification results count: {len(classification_results)}")
            for i, result in enumerate(classification_results):
                logging.info(f"Result {i+1}: Subject={result['subject']}, Title={result['title']}")
        else:
            logging.warning("Classification service not enabled, creating single note")
            # Fallback: create single note with General subject
            from datetime import datetime
            classification_results = [{
                'subject': 'General',
                'title': f"{datetime.now().strftime('%A, %B %d, %Y')} - Notes",
                'content': extracted_text
            }]
        
        created_notes = []
        
        # Create notes for each classification result
        for i, result in enumerate(classification_results):
            subject_name = result['subject']
            
            # Find subject ID
            subject_id = None
            subject = next((s for s in user_subjects if s.name == subject_name), None)
            if subject:
                subject_id = subject.id
            
            # All notes should reference the same original image
            note_image_path = relative_path
            
            # Create note
            note = Note(
                title=result['title'],
                content=result['content'],
                extracted_text=extracted_text,  # Keep original extracted text
                confidence_score=confidence_score,
                original_image_path=note_image_path,  # Same image for all notes
                user_id=current_user.id,
                subject_id=subject_id
            )
            
            try:
                db.session.add(note)
                db.session.commit()
                
                # Add to vector database
                vector_success = vector_service.add_note_embeddings(
                    note.id, note.title, note.content, subject_name, current_user.id, 
                    note.created_at.strftime('%b %d, %Y')
                )
                
                if vector_success:
                    note.is_embedded = True
                    db.session.commit()
                
                created_notes.append(note)
                
            except Exception as e:
                db.session.rollback()
                flash(f'Failed to create note: {result["title"]}', 'error')
        
        if created_notes:
            if len(created_notes) == 1:
                flash('Note created successfully!', 'success')
                return redirect(url_for('notes.view_note', note_id=created_notes[0].id))
            else:
                flash(f'{len(created_notes)} notes created successfully!', 'success')
                return redirect(url_for('notes.list_notes'))
        else:
            flash('Failed to create notes. Please try again.', 'error')
    
    return render_template('notes/create.html', subjects=get_user_subjects())

@notes_bp.route('/notes/auto-process', methods=['POST'])
@login_required
def auto_process_image():
    """Automatically process an image to extract text and create notes"""
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    image_file = request.files['image']
    if not image_file.filename:
        return jsonify({'error': 'No image file selected'}), 400
    
    if not allowed_file(image_file.filename):
        return jsonify({'error': 'Invalid file type. Please upload an image.'}), 400
    
    try:
        # Save uploaded image
        result = save_uploaded_file(image_file, current_user.id)
        
        if not result:
            return jsonify({'error': 'Failed to save uploaded file'}), 500
        
        full_path, relative_path = result
        
        # Extract text from image
        extracted_text, confidence_score = text_extraction_service.extract_text_from_image(full_path)
        
        if not extracted_text.strip():
            return jsonify({'error': 'No text could be extracted from the image'}), 400
        
        if not classification_service.enabled:
            return jsonify({'error': 'AI classification service not available'}), 503
        
        # Get user subjects
        user_subjects = Subject.query.filter_by(user_id=current_user.id).all()
        subject_names = [s.name for s in user_subjects]
        
        if not subject_names:
            return jsonify({'error': 'No subjects found. Please create at least one subject first.'}), 400
        
        # Use multi-subject classification
        classified_notes = classification_service.classify_multi_subject_text(
            extracted_text, subject_names
        )
        
        if not classified_notes:
            return jsonify({'error': 'Failed to classify the extracted text'}), 500
        
        created_notes = []
        
        # Create notes for each classified subject
        for i, note_data in enumerate(classified_notes):
            # Find the subject
            note_subject_id = None
            if note_data['subject'] != "General":
                subject_obj = next((s for s in user_subjects if s.name == note_data['subject']), None)
                if subject_obj:
                    note_subject_id = subject_obj.id
            
            # Create the note
            note = Note(
                title=note_data['title'],
                content=note_data['content'],
                extracted_text=extracted_text if len(classified_notes) == 1 else note_data['content'],
                confidence_score=confidence_score,
                original_image_path=relative_path if i == 0 else None,  # Only attach image to first note
                user_id=current_user.id,
                subject_id=note_subject_id
            )
            
            db.session.add(note)
            db.session.flush()  # Get the note ID
            
            # Add to vector database
            subject_name_for_vector = note_data['subject'] if note_data['subject'] != "General" else ''
            vector_success = vector_service.add_note_embeddings(
                note.id, note.title, note.content, subject_name_for_vector, current_user.id
            )
            
            if vector_success:
                note.is_embedded = True
            
            created_notes.append({
                'id': note.id,
                'title': note.title,
                'content': note.content,
                'subject': note_data['subject'],
                'subject_id': note_subject_id
            })
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully created {len(created_notes)} notes from the image',
            'notes': created_notes,
            'extracted_text': extracted_text,
            'confidence_score': confidence_score
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error in auto-process: {e}")
        return jsonify({'error': f'Failed to process image: {str(e)}'}), 500

@notes_bp.route('/notes/<int:note_id>')
@login_required
def view_note(note_id):
    note = Note.query.filter_by(
        id=note_id,
        user_id=current_user.id
    ).first_or_404()
    
    # Get similar notes
    similar_notes = []
    if vector_service.enabled:
        similar_results = vector_service.get_similar_notes(
            note_id=note_id,
            user_id=current_user.id,
            n_results=5
        )
        if similar_results:
            similar_note_ids = [r['note_id'] for r in similar_results]
            similar_notes_query = Note.query.filter(Note.id.in_(similar_note_ids)).all()
            # Combine with relevance scores
            similar_notes = []
            for result in similar_results:
                note_obj = next((n for n in similar_notes_query if n.id == result['note_id']), None)
                if note_obj:
                    similar_notes.append({
                        'note': note_obj,
                        'relevance_score': result['relevance_score']
                    })
    
    return render_template('notes/view.html', note=note, similar_notes=similar_notes)

@notes_bp.route('/notes/<int:note_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_note(note_id):
    note = Note.query.filter_by(
        id=note_id,
        user_id=current_user.id
    ).first_or_404()
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content', '')
        subject_id = request.form.get('subject_id', type=int)
        
        if not title:
            flash('Note title is required', 'error')
            return render_template('notes/edit.html', note=note, subjects=get_user_subjects())
        
        # Update note
        note.title = title
        note.content = content
        note.subject_id = subject_id if subject_id else None
        
        try:
            db.session.commit()
            
            # Update vector embeddings
            subject_name = ''
            if subject_id:
                subject = Subject.query.get(subject_id)
                if subject:
                    subject_name = subject.name
            
            vector_success = vector_service.add_note_embeddings(
                note.id, note.title, note.content, subject_name, current_user.id
            )
            
            if vector_success:
                note.is_embedded = True
                db.session.commit()
            
            flash('Note updated successfully!', 'success')
            return redirect(url_for('notes.view_note', note_id=note.id))
            
        except Exception as e:
            db.session.rollback()
            flash('Failed to update note. Please try again.', 'error')
    
    subjects = get_user_subjects()
    return render_template('notes/edit.html', note=note, subjects=subjects)

@notes_bp.route('/notes/<int:note_id>/delete', methods=['POST'])
@login_required
def delete_note(note_id):
    note = Note.query.filter_by(
        id=note_id,
        user_id=current_user.id
    ).first_or_404()
    
    try:
        # Remove from vector database
        vector_service.remove_note_embeddings(note_id)
        
        # Delete image file if exists
        if note.original_image_path and os.path.exists(note.original_image_path):
            os.remove(note.original_image_path)
        
        # Delete note from database
        db.session.delete(note)
        db.session.commit()
        
        flash('Note deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Failed to delete note. Please try again.', 'error')
    
    return redirect(url_for('notes.list_notes'))

@notes_bp.route('/api/search')
@login_required
def api_search():
    """API endpoint for real-time search"""
    query = request.args.get('q', '')
    subject_id = request.args.get('subject_id', type=int)
    
    if not query.strip():
        return jsonify([])
    
    results = []
    
    if vector_service.enabled:
        # Use semantic search
        subject_filter = None
        if subject_id:
            subject = Subject.query.get(subject_id)
            if subject and subject.user_id == current_user.id:
                subject_filter = subject.name
        
        search_results = vector_service.search_notes(
            query=query,
            user_id=current_user.id,
            n_results=10,
            subject_filter=subject_filter
        )
        
        # Get full note objects
        if search_results:
            note_ids = [r['note_id'] for r in search_results]
            notes = Note.query.filter(Note.id.in_(note_ids)).all()
            
            for result in search_results:
                note = next((n for n in notes if n.id == result['note_id']), None)
                if note:
                    results.append({
                        'id': note.id,
                        'title': note.title,
                        'content': note.content[:200] + '...' if len(note.content) > 200 else note.content,
                        'subject': note.subject.name if note.subject else 'No Subject',
                        'relevance_score': result['relevance_score'],
                        'url': url_for('notes.view_note', note_id=note.id)
                    })
    else:
        # Fallback to SQL search
        query_filter = Note.query.filter_by(user_id=current_user.id)
        
        if subject_id:
            query_filter = query_filter.filter_by(subject_id=subject_id)
        
        notes = query_filter.filter(
            Note.title.contains(query) | Note.content.contains(query)
        ).limit(10).all()
        
        for note in notes:
            results.append({
                'id': note.id,
                'title': note.title,
                'content': note.content[:200] + '...' if len(note.content) > 200 else note.content,
                'subject': note.subject.name if note.subject else 'No Subject',
                'url': url_for('notes.view_note', note_id=note.id)
            })
    
    return jsonify(results)

def get_user_subjects():
    """Helper function to get current user's subjects"""
    return Subject.query.filter_by(user_id=current_user.id).order_by(Subject.name).all()

@notes_bp.route('/notes/api/list')
@login_required
def api_list_notes():
    """API endpoint to get user's notes for the side panel"""
    try:
        notes = Note.query.filter_by(user_id=current_user.id)\
                         .order_by(Note.updated_at.desc())\
                         .limit(50).all()
        
        notes_data = []
        for note in notes:
            # Get images for this note
            images = []
            if note.original_image_path:
                images.append({
                    'url': url_for('main.uploaded_file', filename=note.original_image_path.replace('uploads/', ''))
                })
            
            notes_data.append({
                'id': note.id,
                'title': note.title,
                'content': note.content[:100] + '...' if note.content and len(note.content) > 100 else note.content,
                'subject_name': note.subject.name if note.subject else None,
                'created_at': note.created_at.isoformat(),
                'updated_at': note.updated_at.isoformat(),
                'images': images
            })
        
        return jsonify({
            'success': True,
            'notes': notes_data
        })
    except Exception as e:
        current_app.logger.error(f"Error in api_list_notes: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load notes'
        }), 500

@notes_bp.route('/notes/<int:note_id>/api')
@login_required
def api_get_note(note_id):
    """API endpoint to get a specific note's details"""
    try:
        note = Note.query.filter_by(id=note_id, user_id=current_user.id).first()
        
        if not note:
            return jsonify({
                'success': False,
                'error': 'Note not found'
            }), 404
        
        # Get images for this note
        images = []
        if note.original_image_path:
            images.append({
                'url': url_for('main.uploaded_file', filename=note.original_image_path.replace('uploads/', ''))
            })
        
        note_data = {
            'id': note.id,
            'title': note.title,
            'content': note.content,
            'subject_name': note.subject.name if note.subject else None,
            'created_at': note.created_at.isoformat(),
            'updated_at': note.updated_at.isoformat(),
            'images': images
        }
        
        return jsonify({
            'success': True,
            'note': note_data
        })
    except Exception as e:
        current_app.logger.error(f"Error in api_get_note: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load note'
        }), 500
