from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False) # TODO: hash passwords
    role = db.Column(db.String(20), nullable=False) # 'student', 'helper', 'admin'
    credits = db.Column(db.Integer, default=100)

    # cascasing delete for user
    questions = db.relationship('Question', backref='author', lazy=True, cascade="all, delete-orphan")
    answers = db.relationship('Answer', backref='author', lazy=True, cascade="all, delete-orphan")

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    bounty = db.Column(db.Integer, default=10)
    is_solved = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    answers = db.relationship('Answer', backref='question', lazy=True, cascade="all, delete-orphan")

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    is_accepted = db.Column(db.Boolean, default=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    likes = db.Column(db.Integer, default=0)

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Nullable for system events
    username = db.Column(db.String(50)) # Snapshot of name in case user is deleted
    action = db.Column(db.String(100), nullable=False) # e.g., "Deleted User", "Posted Question"
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Helper method to log events easily
    @staticmethod
    def log(user, action):
        new_log = ActivityLog(user_id=user.id, username=user.username, action=action)
        db.session.add(new_log)
        db.session.commit()