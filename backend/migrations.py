from app import app, db
from models import User, File, Summary, Quiz
from werkzeug.security import generate_password_hash

def init_db():
    with app.app_context():
        # Drop all existing tables
        db.drop_all()
        print("Dropped all existing tables")
        
        # Create all tables
        db.create_all()
        print("Created all tables")
        
        # Check if admin user exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            # Create admin user
            admin = User(
                username='admin',
                email='admin@example.com',
                password=generate_password_hash('admin123')
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully")
        else:
            print("Admin user already exists")

if __name__ == '__main__':
    print("Initializing database...")
    init_db()
    print("Database initialization complete!") 