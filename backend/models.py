from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    files = db.relationship('File', backref='user', lazy=True, cascade='all, delete-orphan')
    summaries = db.relationship('Summary', backref='user', lazy=True, cascade='all, delete-orphan')
    quizzes = db.relationship('Quiz', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f'<User {self.username}>'

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)  # Size in bytes
    upload_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<File {self.filename}>'

class Summary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Optional: Add reference to the file if summary was generated from a file
    file_id = db.Column(db.Integer, db.ForeignKey('file.id'), nullable=True)
    file = db.relationship('File', backref='summaries')

    def __repr__(self):
        return f'<Summary {self.topic}>'

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    questions = db.Column(db.JSON, nullable=False)  # Store questions as JSON
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Optional: Add reference to the file if quiz was generated from a file
    file_id = db.Column(db.Integer, db.ForeignKey('file.id'), nullable=True)
    file = db.relationship('File', backref='quizzes')

    def __repr__(self):
        return f'<Quiz {self.title}>' 