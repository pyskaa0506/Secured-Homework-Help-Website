from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet
import pyotp
import os


def _get_fernet():
    """Get Fernet cipher for encrypting TOTP secrets."""
    key = os.environ.get('TOTP_ENCRYPTION_KEY')
    if not key:
        raise RuntimeError("TOTP_ENCRYPTION_KEY environment variable is required")
    return Fernet(key.encode())


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    credits = db.Column(db.Integer, default=100)
    last_login_reward = db.Column(db.Date, nullable=True)
    
    # 2FA fields, encrypted secret
    _totp_secret_encrypted = db.Column('totp_secret', db.String(256), nullable=True)
    is_2fa_enabled = db.Column(db.Boolean, default=False)

    # cascading delete for user
    questions = db.relationship('Question', backref='author', lazy=True, cascade="all, delete-orphan")
    answers = db.relationship('Answer', backref='author', lazy=True, cascade="all, delete-orphan")
    likes = db.relationship('AnswerLike', backref='user', lazy=True, cascade="all, delete-orphan")

    @property
    def totp_secret(self):
        """Decrypt and return TOTP secret."""
        if not self._totp_secret_encrypted:
            return None
        try:
            f = _get_fernet()
            return f.decrypt(self._totp_secret_encrypted.encode()).decode()
        except Exception:
            return None

    @totp_secret.setter
    def totp_secret(self, value):
        """Encrypt and store TOTP secret."""
        if value is None:
            self._totp_secret_encrypted = None
        else:
            f = _get_fernet()
            self._totp_secret_encrypted = f.encrypt(value.encode()).decode()

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
        """Verify password against stored hash."""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def generate_totp_secret(self):
        """Generate a new TOTP secret for the user."""
        secret = pyotp.random_base32()
        self.totp_secret = secret  # Will be encrypted by setter
        return secret

    def get_totp_uri(self):
        """Get the provisioning URI for authenticator apps."""
        secret = self.totp_secret  # Will be decrypted by getter
        if not secret:
            return None
        return pyotp.totp.TOTP(secret).provisioning_uri(
            name=self.username,
            issuer_name="HomeworkHelp"
        )

    def verify_totp(self, token):
        """Verify a TOTP token."""
        secret = self.totp_secret  # Will be decrypted by getter
        if not secret:
            return False
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)

    def claim_daily_reward(self, amount=20):
        """True if reward claimed, False if already claimed today."""
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
        """Accepts: User object or username string."""
        if isinstance(user_or_username, str):
            username = user_or_username
        else:
            username = user_or_username.username
        new_log = ActivityLog(username=username, action=action)
        db.session.add(new_log)