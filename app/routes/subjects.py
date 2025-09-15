from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import Subject
from app import db

subjects_bp = Blueprint('subjects', __name__)

@subjects_bp.route('/subjects')
@login_required
def list_subjects():
    subjects = Subject.query.filter_by(user_id=current_user.id)\
                           .order_by(Subject.created_at.desc())\
                           .all()
    return render_template('subjects/list.html', subjects=subjects)

@subjects_bp.route('/subjects/create', methods=['GET', 'POST'])
@login_required
def create_subject():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        color = request.form.get('color', '#3B82F6')
        
        if not name:
            flash('Subject name is required', 'error')
            return render_template('subjects/create.html')
        
        # Check if subject name already exists for this user
        existing_subject = Subject.query.filter_by(
            name=name, 
            user_id=current_user.id
        ).first()
        
        if existing_subject:
            flash('Subject with this name already exists', 'error')
            return render_template('subjects/create.html')
        
        subject = Subject(
            name=name,
            description=description,
            color=color,
            user_id=current_user.id
        )
        
        try:
            db.session.add(subject)
            db.session.commit()
            flash('Subject created successfully!', 'success')
            return redirect(url_for('subjects.list_subjects'))
        except Exception as e:
            db.session.rollback()
            flash('Failed to create subject. Please try again.', 'error')
    
    return render_template('subjects/create.html')

@subjects_bp.route('/subjects/<int:subject_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_subject(subject_id):
    subject = Subject.query.filter_by(
        id=subject_id, 
        user_id=current_user.id
    ).first_or_404()
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        color = request.form.get('color', '#3B82F6')
        
        if not name:
            flash('Subject name is required', 'error')
            return render_template('subjects/edit.html', subject=subject)
        
        # Check if subject name already exists for this user (excluding current subject)
        existing_subject = Subject.query.filter_by(
            name=name, 
            user_id=current_user.id
        ).filter(Subject.id != subject_id).first()
        
        if existing_subject:
            flash('Subject with this name already exists', 'error')
            return render_template('subjects/edit.html', subject=subject)
        
        subject.name = name
        subject.description = description
        subject.color = color
        
        try:
            db.session.commit()
            flash('Subject updated successfully!', 'success')
            return redirect(url_for('subjects.list_subjects'))
        except Exception as e:
            db.session.rollback()
            flash('Failed to update subject. Please try again.', 'error')
    
    return render_template('subjects/edit.html', subject=subject)

@subjects_bp.route('/subjects/<int:subject_id>/delete', methods=['POST'])
@login_required
def delete_subject(subject_id):
    subject = Subject.query.filter_by(
        id=subject_id, 
        user_id=current_user.id
    ).first_or_404()
    
    try:
        # Delete associated notes will be handled by cascade
        db.session.delete(subject)
        db.session.commit()
        flash('Subject deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Failed to delete subject. Please try again.', 'error')
    
    return redirect(url_for('subjects.list_subjects'))
