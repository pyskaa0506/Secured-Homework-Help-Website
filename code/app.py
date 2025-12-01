from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Question, Answer

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret' # session management
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mvp.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ROUTES
@app.route('/')
def index():
    # Show all unsolved questions
    questions = Question.query.filter_by(is_solved=False).all()
    return render_template('index.html', questions=questions)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # password is not hashsed
        u = User(
            username=request.form['username'],
            password=request.form['password'],
            role=request.form['role']
        )
        db.session.add(u)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        # we'll need to secure this password check later
        if user and user.password == request.form['password']:
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash("Wrong login")
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/ask', methods=['GET', 'POST'])
@login_required
def ask():
    if request.method == 'POST':
        bounty = int(request.form['bounty'])
        if current_user.credits >= bounty:
            current_user.credits -= bounty
            q = Question(
                title=request.form['title'],
                content=request.form['content'],
                bounty=bounty,
                user_id=current_user.id
            )
            db.session.add(q)
            db.session.commit()
            return redirect(url_for('index'))
        else:
            flash("Not enough money!")
    return render_template('ask.html')

@app.route('/question/<int:id>', methods=['GET', 'POST'])
@login_required
def question_detail(id):
    q = Question.query.get(id)
    
    if request.method == 'POST':
        ans = Answer(
            content=request.form['content'],
            question_id=q.id,
            user_id=current_user.id
        )
        db.session.add(ans)
        db.session.commit()
        return redirect(url_for('question_detail', id=id))

    return render_template('detail.html', question=q)

@app.route('/accept/<int:answer_id>')
@login_required
def accept_answer(answer_id):
    ans = Answer.query.get(answer_id)
    q = ans.question
    
    # Mark as solved and pay
    if not q.is_solved:
        q.is_solved = True
        ans.is_accepted = True
        helper = User.query.get(ans.user_id)
        helper.credits += q.bounty
        
        db.session.commit()
        
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)