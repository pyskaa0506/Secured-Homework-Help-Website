from flask import render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.auth import auth
from app.models import User, ActivityLog
from datetime import datetime, timedelta
import re
import pyotp
import qrcode
import io
import base64


def validate_password(password):
    """Returns: is_valid, error_message"""
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
    """Returns: is_valid, error_message"""
    if len(username) < 3:
        return False, "Username must be at least 3 characters long."
    if len(username) > 50:
        return False, "Username must be less than 50 characters."
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscores."
    return True, None


def generate_qr_code(uri):
    """Generate a base64-encoded QR code image."""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return base64.b64encode(buffer.getvalue()).decode()


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Please enter both username and password.')
            return render_template('login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # Check if 2FA is enabled
            if user.is_2fa_enabled:
                # Store user ID and timestamp in session for 2FA verification
                session['2fa_user_id'] = user.id
                session['2fa_timestamp'] = datetime.utcnow().isoformat()
                return redirect(url_for('auth.verify_2fa'))
            
            # No 2FA, proceed with login
            login_user(user)
            ActivityLog.log(user, "Logged in")
            
            if user.claim_daily_reward(20):
                ActivityLog.log(user, "Claimed daily login reward (+20 cr)")
                flash("Welcome back! You received 20 credits as a daily login reward!")
            
            db.session.commit()
            return redirect(url_for('main.index'))
        else:
            flash('Invalid username or password.')
            
    return render_template('login.html')


@auth.route('/verify-2fa', methods=['GET', 'POST'])
def verify_2fa():
    """Verify 2FA token during login."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    user_id = session.get('2fa_user_id')
    timestamp_str = session.get('2fa_timestamp')
    
    if not user_id or not timestamp_str:
        flash('Please login first.')
        return redirect(url_for('auth.login'))
    
    # 5 min expiration for 2FA
    try:
        timestamp = datetime.fromisoformat(timestamp_str)
        if datetime.utcnow() - timestamp > timedelta(minutes=5):
            session.pop('2fa_user_id', None)
            session.pop('2fa_timestamp', None)
            flash('2FA session expired. Please login again.')
            return redirect(url_for('auth.login'))
    except (ValueError, TypeError):
        session.pop('2fa_user_id', None)
        session.pop('2fa_timestamp', None)
        flash('Session error. Please login again.')
        return redirect(url_for('auth.login'))
    
    user = User.query.get(user_id)
    if not user:
        session.pop('2fa_user_id', None)
        session.pop('2fa_timestamp', None)
        flash('Session expired. Please login again.')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        token = request.form.get('token', '').strip()
        
        if user.verify_totp(token):
            # Clear 2FA session data
            session.pop('2fa_user_id', None)
            session.pop('2fa_timestamp', None)
            
            # Complete login
            login_user(user)
            ActivityLog.log(user, "Logged in (2FA verified)")
            
            if user.claim_daily_reward(20):
                ActivityLog.log(user, "Claimed daily login reward (+20 cr)")
                flash("Welcome back! You received 20 credits as a daily login reward!")
            
            db.session.commit()
            return redirect(url_for('main.index'))
        else:
            flash('Invalid authentication code. Please try again.')
    
    return render_template('verify_2fa.html')


@auth.route('/setup-2fa', methods=['GET', 'POST'])
@login_required
def setup_2fa():
    """Setup 2FA for the current user."""
    if current_user.is_2fa_enabled:
        flash('2FA is already enabled.')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        token = request.form.get('token', '').strip()
        
        # Verify the token before enabling 2FA
        if current_user.verify_totp(token):
            current_user.is_2fa_enabled = True
            ActivityLog.log(current_user, "Enabled 2FA")
            db.session.commit()
            flash('Two-factor authentication has been enabled!')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid code. Please try again.')
    
    # Generate new secret if not exists
    if not current_user.totp_secret:
        current_user.generate_totp_secret()
        db.session.commit()
    
    # Generate QR code
    uri = current_user.get_totp_uri()
    qr_code = generate_qr_code(uri)
    
    return render_template('setup_2fa.html', 
                           qr_code=qr_code, 
                           secret=current_user.totp_secret)


@auth.route('/disable-2fa', methods=['GET', 'POST'])
@login_required
def disable_2fa():
    """Disable 2FA for the current user."""
    if not current_user.is_2fa_enabled:
        flash('2FA is not enabled.')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        token = request.form.get('token', '').strip()
        password = request.form.get('password', '')
        
        # Require both password and current 2FA token
        if not current_user.check_password(password):
            flash('Invalid password.')
            return render_template('disable_2fa.html')
        
        if not current_user.verify_totp(token):
            flash('Invalid authentication code.')
            return render_template('disable_2fa.html')
        
        current_user.is_2fa_enabled = False
        current_user.totp_secret = None
        ActivityLog.log(current_user, "Disabled 2FA")
        db.session.commit()
        flash('Two-factor authentication has been disabled.')
        return redirect(url_for('main.index'))
    
    return render_template('disable_2fa.html')


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', 'student')
        
        is_valid, error = validate_username(username)
        if not is_valid:
            flash(error)
            return render_template('register.html')
        
        is_valid, error = validate_password(password)
        if not is_valid:
            flash(error)
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.')
            return render_template('register.html')
        
        if role not in ['student', 'helper']:
            flash('Invalid role selected.')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return render_template('register.html')
        
        user = User(username=username, role=role)
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
    # Clear any 2FA session data
    session.pop('2fa_user_id', None)
    session.pop('2fa_timestamp', None)
    return redirect(url_for('main.index'))