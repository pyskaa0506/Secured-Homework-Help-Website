from flask import render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, current_user
from app import db
from app.auth import auth
from app.models import User, ActivityLog

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        # Insecure plain text check
        if user and user.password == password:
            login_user(user)
            ActivityLog.log(user, "Logged in")
            return redirect(url_for('main.index'))
        else:
            flash('Login Failed. Check details.')
            
    return render_template('login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        user = User(
            username=request.form['username'],
            password=request.form['password'],
            role=request.form['role']
        )
        try:
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('auth.login'))
        except:
            flash('Username already exists.')
            
    return render_template('register.html')

@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))