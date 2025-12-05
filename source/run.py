from app import create_app, db
from app.models import User
import os

app = create_app()

# For first time setup
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin_password = os.environ.get('ADMIN_PASSWORD', 'Admin123!')  # Change in production
        admin = User(username='admin', role='admin', credits=100)
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()
        print("Admin created: user='admin'")
        
    if not User.query.filter_by(username='helper').first():
        helper_password = os.environ.get('HELPER_PASSWORD', 'Helper123!')  # Change in production
        helper = User(username='helper', role='helper', credits=979)
        helper.set_password(helper_password)
        db.session.add(helper)
        db.session.commit()
        print("Helper created: user='helper'")

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug_mode, host='0.0.0.0')