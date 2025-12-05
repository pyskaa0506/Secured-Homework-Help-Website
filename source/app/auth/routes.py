from flask import render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, current_user
from app import db
from app.auth import auth
from app.models import User, ActivityLog
import re


def validate_password(password):
    """
    Returns: is_valid, error_message
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if len(password) > 128:
        return False, "Password must be less than 128 characters."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number."
    return True, None


def validate_username(username):
    """
    Returns: is_valid, error_message
    """
    if len(username) < 3:
        return False, "Username must be at least 3 characters long."
    if len(username) > 50:
        return False, "Username must be less than 50 characters."
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscores."
    return True, None


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Validate input exists
        if not username or not password:
            flash('Please enter both username and password.')
            return render_template('login.html')
        
        user = User.query.filter_by(username=username).first()
        
        # Use constant-time comparison via check_password
        # Even if user doesn't exist, we still "check" to prevent timing attacks
        if user and user.check_password(password):
            login_user(user)
            ActivityLog.log(user, "Logged in")
            
            # Daily login reward
            if user.claim_daily_reward(20):
                ActivityLog.log(user, "Claimed daily login reward (+20 cr)")
                flash("Welcome back! You received 20 credits as a daily login reward!")
            
            db.session.commit()
            return redirect(url_for('main.index'))
        else:
            flash('Invalid username or password.')
            
    return render_template('login.html')


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', 'student')
        
        # Validate username
        is_valid, error = validate_username(username)
        if not is_valid:
            flash(error)
            return render_template('register.html')
        
        # Validate password
        is_valid, error = validate_password(password)
        if not is_valid:
            flash(error)
            return render_template('register.html')
        
        # Confirm password match
        if password != confirm_password:
            flash('Passwords do not match.')
            return render_template('register.html')
        
        # Validate role
        if role not in ['student', 'helper']:
            flash('Invalid role selected.')
            return render_template('register.html')
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return render_template('register.html')
        
        # Create user with hashed password
        user = User(
            username=username,
            role=role
        )
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.flush()
            ActivityLog.log(user, f"Registered as {user.role}")
            db.session.commit()
            flash('Registration successful! Please login.')
            return redirect(url_for('auth.login'))
        except Exception:
            db.session.rollback()
            flash('An error occurred. Please try again.')
            
    return render_template('register.html')

@auth.route('/logout')
def logout():
    if current_user.is_authenticated:
        ActivityLog.log(current_user, "Logged out")
        db.session.commit()
    logout_user()
    return redirect(url_for('main.index'))