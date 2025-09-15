from flask import Blueprint, render_template, redirect, url_for, send_from_directory, current_app, abort
from flask_login import login_required, current_user
from app.models import Note, Subject
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Get recent notes
    recent_notes = Note.query.filter_by(user_id=current_user.id)\
                            .order_by(Note.updated_at.desc())\
                            .limit(5)\
                            .all()
    
    # Get subjects count
    subjects_count = Subject.query.filter_by(user_id=current_user.id).count()
    
    # Get total notes count
    notes_count = Note.query.filter_by(user_id=current_user.id).count()
    
    return render_template('main/dashboard.html', 
                         recent_notes=recent_notes,
                         subjects_count=subjects_count,
                         notes_count=notes_count)

@main_bp.route('/uploads/<path:filename>')
@login_required
def uploaded_file(filename):
    """Serve uploaded files securely"""
    import logging
    import os
    
    logging.info(f"Requested file: {filename}")
    logging.info(f"Current working directory: {os.getcwd()}")
    logging.info(f"Current user: {current_user.id}")
    
    # Security check: ensure the file belongs to the current user
    user_path = str(current_user.id)
    is_user_file = filename.startswith(user_path + '/')
    is_user_profile = filename.startswith(f'profiles/profile_{current_user.id}_')
    
    logging.info(f"User path: {user_path}")
    logging.info(f"Is user file: {is_user_file}")
    logging.info(f"Is user profile: {is_user_profile}")
    
    if not (is_user_file or is_user_profile):
        logging.warning(f"Access denied for file: {filename} by user: {current_user.id}")
        abort(403)  # Forbidden if trying to access another user's files
    
    upload_directory = current_app.config['UPLOAD_FOLDER']
    
    # Ensure absolute path for upload directory
    if not os.path.isabs(upload_directory):
        upload_directory = os.path.join(os.getcwd(), upload_directory)
    
    full_path = os.path.join(upload_directory, filename)
    
    logging.info(f"Upload directory: {upload_directory}")
    logging.info(f"Looking for file at: {full_path}")
    logging.info(f"File exists: {os.path.exists(full_path)}")
    
    # Check if file exists
    if not os.path.exists(full_path):
        logging.error(f"File not found: {full_path}")
        abort(404)
    
    # Use the absolute upload directory and the relative filename
    return send_from_directory(upload_directory, filename)

@main_bp.route('/debug/note/<int:note_id>')
@login_required
def debug_note(note_id):
    """Debug route to check note data"""
    from app.models import Note
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        abort(403)
    
    debug_info = {
        'note_id': note.id,
        'title': note.title,
        'original_image_path': note.original_image_path,
        'upload_folder': current_app.config['UPLOAD_FOLDER'],
        'file_exists': os.path.exists(os.path.join(current_app.config['UPLOAD_FOLDER'], note.original_image_path)) if note.original_image_path else False
    }
    
    return f"<pre>{debug_info}</pre>"
