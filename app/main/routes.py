from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app import db
from app.main import main
from app.models import Question, Answer, User

@main.route('/')
def index():
    questions = Question.query.filter_by(is_solved=False).all()
    return render_template('index.html', questions=questions)

@main.route('/ask', methods=['GET', 'POST'])
@login_required
def ask():
    if current_user.role != 'student':
        flash('Only students can ask questions.')
        return redirect(url_for('main.index'))

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
            return redirect(url_for('main.index'))
        else:
            flash('Insufficient credits.')

    return render_template('ask.html')

@main.route('/question/<int:q_id>', methods=['GET', 'POST'])
@login_required
def question_detail(q_id):
    q = Question.query.get_or_404(q_id)

    if request.method == 'POST':
        # Submit Answer Logic
        if current_user.role == 'helper':
            ans = Answer(
                content=request.form['content'],
                question_id=q.id,
                user_id=current_user.id
            )
            db.session.add(ans)
            db.session.commit()
        else:
            flash("Only helpers can answer.")
        return redirect(url_for('main.question_detail', q_id=q.id))

    return render_template('detail.html', question=q)

@main.route('/accept/<int:a_id>')
@login_required
def accept_answer(a_id):
    ans = Answer.query.get_or_404(a_id)
    q = ans.question

    if current_user.id != q.user_id:
        abort(403)

    if not q.is_solved:
        q.is_solved = True
        ans.is_accepted = True
        
        # Transfer credits to helper
        helper = User.query.get(ans.user_id)
        helper.credits += q.bounty
        
        db.session.commit()
        
    return redirect(url_for('main.index'))