from app import create_app, db
from app.models import User

app = create_app()

# For first time setup
with app.app_context():
    db.drop_all()
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password='123', role='admin', credits=100)
        db.session.add(admin)
        db.session.commit()
        print("Admin created: user='admin', pass='123'")
        
    if not User.query.filter_by(username='helper').first():
        helper = User(username='helper', password='123', role='helper', credits=979)
        db.session.add(helper)
        db.session.commit()
        print("Helper created: user='helper', pass='123'")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')