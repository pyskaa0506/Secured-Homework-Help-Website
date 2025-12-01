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
    # Fetch last 20 logs, newest first
    logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(20).all()
    
    return render_template('admin.html', users=users, questions=questions, logs=logs)

@admin.route('/delete_user/<int:user_id>')
@login_required
def delete_user(user_id):
    if current_user.role != 'admin': return redirect(url_for('main.index'))
    
    user = User.query.get(user_id)
    if user and user.id != current_user.id:
        db.session.delete(user)
        db.session.commit()
        flash(f'User {user.username} deleted.')
        
    return redirect(url_for('admin.dashboard'))

@admin.route('/delete_question/<int:q_id>')
@login_required
def delete_question(q_id):
    if current_user.role != 'admin': return redirect(url_for('main.index'))
    
    q = Question.query.get(q_id)
    if q:
        db.session.delete(q)
        db.session.commit()
        flash('Question deleted.')
        
    return redirect(url_for('admin.dashboard'))