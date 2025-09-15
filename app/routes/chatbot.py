from flask import Blueprint, request, jsonify, render_template, current_app
from flask_login import login_required, current_user
from app.services.rag_chatbot import RAGChatbotService
from app.models import Chat, ChatMessage, Note
from app import db
import json

chatbot_bp = Blueprint('chatbot', __name__)

# Initialize chatbot service
chatbot_service = RAGChatbotService()

@chatbot_bp.route('/chatbot')
@login_required
def chatbot_interface():
    """Render the chatbot interface with three-panel layout"""
    # Get user's chats
    chats = Chat.query.filter_by(user_id=current_user.id).order_by(Chat.updated_at.desc()).all()
    
    # Get current chat ID from query params
    current_chat_id = request.args.get('chat_id', type=int)
    current_chat = None
    if current_chat_id:
        current_chat = Chat.query.filter_by(id=current_chat_id, user_id=current_user.id).first()
    
    # Get recent notes for image viewer
    recent_notes = Note.query.filter_by(user_id=current_user.id).order_by(Note.updated_at.desc()).limit(10).all()
    
    suggestions = chatbot_service.get_suggested_questions(current_user.id)
    return render_template('chatbot/interface.html', 
                         suggestions=suggestions,
                         chats=chats, 
                         current_chat=current_chat,
                         recent_notes=recent_notes)

@chatbot_bp.route('/chatbot/new', methods=['POST'])
@login_required
def new_chat():
    """Create a new chat session"""
    try:
        data = request.get_json()
        title = data.get('title', 'New Chat Session')
        
        # Create new chat
        chat = Chat(user_id=current_user.id, title=title)
        db.session.add(chat)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'chat_id': chat.id,
            'title': chat.title
        })
        
    except Exception as e:
        current_app.logger.error(f"New chat error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to create new chat'}), 500

@chatbot_bp.route('/chatbot/chat/<int:chat_id>/delete', methods=['DELETE'])
@login_required
def delete_chat(chat_id):
    """Delete a specific chat"""
    try:
        chat = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first()
        if not chat:
            return jsonify({'error': 'Chat not found'}), 404
        
        db.session.delete(chat)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        current_app.logger.error(f"Delete chat error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to delete chat'}), 500

@chatbot_bp.route('/chatbot/ask', methods=['POST'])
@login_required
def ask_question():
    """Handle chatbot questions via API"""
    try:
        data = request.get_json()
        
        if not data or 'question' not in data:
            return jsonify({'error': 'Question is required'}), 400
        
        question = data['question'].strip()
        chat_id = data.get('chat_id')
        
        if not question:
            return jsonify({'error': 'Question cannot be empty'}), 400
        
        # Get or create chat
        chat = None
        if chat_id:
            chat = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first()
        
        if not chat:
            # Create new chat with AI-generated title
            title = chatbot_service.generate_chat_title(question)
            chat = Chat(user_id=current_user.id, title=title)
            db.session.add(chat)
            db.session.flush()  # Get the ID
        
        # Save user message
        user_message = ChatMessage(
            chat_id=chat.id,
            content=question,
            is_user=True
        )
        db.session.add(user_message)
        
        # Get answer from RAG service
        result = chatbot_service.search_and_answer(
            question=question,
            user_id=current_user.id
        )
        
        # Save AI response
        ai_message = ChatMessage(
            chat_id=chat.id,
            content=result['answer'],
            is_user=False,
            sources=json.dumps([src['note_id'] for src in result.get('sources', [])])
        )
        db.session.add(ai_message)
        
        # Update chat timestamp
        chat.updated_at = db.func.now()
        
        db.session.commit()
        
        # Add chat info to result
        result['chat_id'] = chat.id
        result['chat_title'] = chat.title
        result['message_id'] = ai_message.id
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Chatbot error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to process question'}), 500

@chatbot_bp.route('/chatbot/chat/<int:chat_id>/messages')
@login_required
def get_chat_messages(chat_id):
    """Get messages for a specific chat"""
    try:
        chat = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first()
        if not chat:
            return jsonify({'error': 'Chat not found'}), 404
        
        messages = []
        for message in chat.messages:
            message_data = {
                'id': message.id,
                'content': message.content,
                'is_user': message.is_user,
                'created_at': message.created_at.isoformat(),
                'sources': []
            }
            
            if message.sources and not message.is_user:
                source_ids = json.loads(message.sources)
                sources = Note.query.filter(Note.id.in_(source_ids)).all()
                message_data['sources'] = [{
                    'note_id': note.id,
                    'title': note.title,
                    'excerpt': note.content[:150] + '...' if len(note.content) > 150 else note.content
                } for note in sources]
            
            messages.append(message_data)
        
        return jsonify({
            'success': True,
            'messages': messages,
            'chat_title': chat.title
        })
        
    except Exception as e:
        current_app.logger.error(f"Get messages error: {str(e)}")
        return jsonify({'error': 'Failed to get messages'}), 500

@chatbot_bp.route('/chatbot/note/<int:note_id>')
@login_required
def get_note_details(note_id):
    """Get detailed information about a specific note"""
    try:
        note = Note.query.filter_by(id=note_id, user_id=current_user.id).first()
        if not note:
            return jsonify({'error': 'Note not found'}), 404
        
        return jsonify({
            'success': True,
            'note': {
                'id': note.id,
                'title': note.title,
                'content': note.content,
                'image_path': note.original_image_path,
                'subject': note.subject.name if note.subject else None,
                'created_at': note.created_at.isoformat(),
                'updated_at': note.updated_at.isoformat()
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Get note details error: {str(e)}")
        return jsonify({'error': 'Failed to get note details'}), 500

@chatbot_bp.route('/chatbot/notes-viewer')
@login_required
def notes_viewer():
    """Render the notes viewer page in a new window"""
    return render_template('chatbot/notes_viewer.html')

@chatbot_bp.route('/chatbot/view-note/<int:note_id>')
@login_required
def view_note_popup(note_id):
    """View a specific note in a popup window"""
    try:
        note = Note.query.filter_by(id=note_id, user_id=current_user.id).first()
        if not note:
            return "Note not found", 404
        
        return render_template('chatbot/note_popup.html', note=note)
        
    except Exception as e:
        current_app.logger.error(f"View note popup error: {str(e)}")
        return "Error loading note", 500

@chatbot_bp.route('/chatbot/suggestions')
@login_required
def get_suggestions():
    """Get suggested questions"""
    suggestions = chatbot_service.get_suggested_questions(current_user.id)
    return jsonify({'suggestions': suggestions})
