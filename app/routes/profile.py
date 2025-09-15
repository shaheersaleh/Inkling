from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, send_file, Response
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import io
from app import db
from app.models import User

profile = Blueprint('profile', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@profile.route('/profile')
@login_required
def view_profile():
    """Display user profile page"""
    return render_template('profile/view.html', user=current_user)

@profile.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile"""
    if request.method == 'POST':
        try:
            # Update username
            new_username = request.form.get('username', '').strip()
            if new_username and new_username != current_user.username:
                # Check if username already exists
                existing_user = User.query.filter_by(username=new_username).first()
                if existing_user:
                    flash('Username already exists. Please choose a different one.', 'danger')
                    return render_template('profile/edit.html', user=current_user)
                
                current_user.username = new_username
            
            # Handle profile image upload
            if 'profile_image' in request.files:
                file = request.files['profile_image']
                if file and file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    # Create unique filename
                    filename = f"profile_{current_user.id}_{filename}"
                    
                    # Ensure upload directory exists
                    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profiles')
                    os.makedirs(upload_folder, exist_ok=True)
                    
                    # Save file
                    file_path = os.path.join(upload_folder, filename)
                    file.save(file_path)
                    
                    # Read file data for database storage
                    with open(file_path, 'rb') as f:
                        image_data = f.read()
                    
                    # Update user profile image path and binary data
                    current_user.profile_image = f"profiles/{filename}"
                    current_user.profile_image_data = image_data
                    current_user.profile_image_mimetype = file.content_type
            
            # Update other profile fields
            current_user.email = request.form.get('email', current_user.email)
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile.view_profile'))
            
        except Exception as e:
            current_app.logger.error(f"Profile update error: {str(e)}")
            flash('An error occurred while updating your profile.', 'danger')
            db.session.rollback()
    
    return render_template('profile/edit.html', user=current_user)

@profile.route('/profile/delete', methods=['POST'])
@login_required
def delete_profile():
    """Delete user account"""
    try:
        # Delete user's profile image if exists
        if current_user.profile_image:
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.profile_image)
            if os.path.exists(image_path):
                os.remove(image_path)
        
        # Delete user account
        db.session.delete(current_user)
        db.session.commit()
        
        flash('Your account has been deleted successfully.', 'info')
        return redirect(url_for('auth.login'))
        
    except Exception as e:
        current_app.logger.error(f"Account deletion error: {str(e)}")
        flash('An error occurred while deleting your account.', 'danger')
        db.session.rollback()
        return redirect(url_for('profile.view_profile'))

@profile.route('/profile/image/<int:user_id>')
def profile_image(user_id):
    """Serve profile image from database"""
    user = User.query.get_or_404(user_id)
    
    if not user.profile_image_data:
        # Return default avatar or 404
        return '', 404
    
    return Response(
        user.profile_image_data,
        mimetype=user.profile_image_mimetype or 'image/jpeg',
        headers={
            'Cache-Control': 'public, max-age=3600',
            'Content-Disposition': f'inline; filename="profile_{user_id}.jpg"'
        }
    )
