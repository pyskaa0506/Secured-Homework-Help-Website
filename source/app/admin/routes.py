from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.admin import admin
from app.models import User, Question, ActivityLog

@admin.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('main.index'))
        
    users = User.query.all()
    questions = Question.query.all()
    logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(50).all()
    
    return render_template('admin.html', users=users, questions=questions, logs=logs)

@admin.route('/delete_user/<int:user_id>')
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('main.index'))
    
    user = User.query.get(user_id)
    if user and user.id != current_user.id:
        username = user.username
        db.session.delete(user)
        ActivityLog.log(current_user, f"Deleted user: {username}")
        db.session.commit()
        flash(f'User {username} deleted.')
        
    return redirect(url_for('admin.dashboard'))

@admin.route('/delete_question/<int:q_id>')
@login_required
def delete_question(q_id):
    if current_user.role != 'admin':
        return redirect(url_for('main.index'))
    
    q = Question.query.get(q_id)
    if q:
        title = q.title
        db.session.delete(q)
        ActivityLog.log(current_user, f"Deleted question: {title}")
        db.session.commit()
        flash('Question deleted.')
        
    return redirect(url_for('admin.dashboard'))