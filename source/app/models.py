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

    # cascading delete for user
    questions = db.relationship('Question', backref='author', lazy=True, cascade="all, delete-orphan")
    answers = db.relationship('Answer', backref='author', lazy=True, cascade="all, delete-orphan")
    likes = db.relationship('AnswerLike', backref='user', lazy=True, cascade="all, delete-orphan")

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
    answer_likes = db.relationship('AnswerLike', backref='answer', lazy='dynamic', cascade="all, delete-orphan")

class AnswerLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'), nullable=False)
    __table_args__ = (db.UniqueConstraint('user_id', 'answer_id', name='_user_answer_uc'),)

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)  # Snapshot of username
    action = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def log(user_or_username, action):
        """
        Accepts: User object or username string
        """
        if isinstance(user_or_username, str):
            username = user_or_username
        else:
            username = user_or_username.username
        new_log = ActivityLog(username=username, action=action)
        db.session.add(new_log)