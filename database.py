# database.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Scheme(db.Model):
    __tablename__ = "schemes"
    sr_no = db.Column(db.Integer, primary_key=True)
    scheme_name = db.Column(db.String)
    scheme_link = db.Column(db.String)
    details = db.Column(db.String)
    benefits = db.Column(db.String)
    eligibility = db.Column(db.String)
    application_process = db.Column(db.String)
    documents_required = db.Column(db.String)
    category = db.Column(db.String)
    state = db.Column(db.String)
    summary = db.Column(db.Text, nullable=True)

def init_db(app):
    db.init_app(app)