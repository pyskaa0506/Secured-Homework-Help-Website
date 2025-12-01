from app import create_app, db
from app.models import User

app = create_app()

# For first time setup
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password='123', role='admin', credits=100)
        db.session.add(admin)
        db.session.commit()
        print("Admin created: user='admin', pass='123'")

if __name__ == '__main__':
    app.run(debug=True)