from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)  # Store hash, not plaintext
    role = db.Column(db.String(20), nullable=False)  # 'student', 'helper', 'admin'
    credits = db.Column(db.Integer, default=100)
    last_login_reward = db.Column(db.Date, nullable=True)

    # cascading delete for user
    questions = db.relationship('Question', backref='author', lazy=True, cascade="all, delete-orphan")
    answers = db.relationship('Answer', backref='author', lazy=True, cascade="all, delete-orphan")
    likes = db.relationship('AnswerLike', backref='user', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        """
        Hash password using PBKDF2 with SHA256.
        Werkzeug automatically handles salting.
        """
        self.password_hash = generate_password_hash(
            password,
            method='pbkdf2:sha256',
            salt_length=16
        )

    def check_password(self, password):
        """
        Verify password against stored hash.
        Returns True if password matches, False otherwise.
        Uses constant-time comparison to prevent timing attacks.
        """
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def claim_daily_reward(self, amount=20):
        """
        True if reward claimed, False if already claimed today
        """
        today = date.today()
        if self.last_login_reward is None or self.last_login_reward < today:
            self.credits += amount
            self.last_login_reward = today
            return True
        return False

    def get_helper_rank(self):
        """
        Returns (rank_name, badge_class) based on credits.
        Only applicable for helpers.
        """
        if self.role != 'helper':
            return None, None
        
        if self.credits >= 1000:
            return "Defeated Athena in Trivia", "bg-danger text-white"
        elif self.credits >= 300:
            return "Odin's Heir", "bg-purple text-white"
        elif self.credits >= 200:
            return "Knowledge Owl", "bg-info text-dark"
        else:
            return "Newbie Helper", "bg-secondary text-white"

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
    """
    Logs store snapshot of current username.
    Please watch out if ever adding change username feature
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
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