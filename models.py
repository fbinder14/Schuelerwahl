from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class SchoolSettings(db.Model):
    __tablename__ = "school_settings"

    id = db.Column(db.Integer, primary_key=True)
    school_name = db.Column(db.String(200), default="")
    logo_filename = db.Column(db.String(200))


class Election(db.Model):
    __tablename__ = "elections"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    max_votes = db.Column(db.Integer, default=3)
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    candidates = db.relationship("Candidate", backref="election", cascade="all, delete-orphan")
    voting_codes = db.relationship("VotingCode", backref="election", cascade="all, delete-orphan")
    votes = db.relationship("Vote", backref="election", cascade="all, delete-orphan")
    school_classes = db.relationship("SchoolClass", backref="election", cascade="all, delete-orphan")


class Candidate(db.Model):
    __tablename__ = "candidates"

    id = db.Column(db.Integer, primary_key=True)
    election_id = db.Column(db.Integer, db.ForeignKey("elections.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    class_name = db.Column(db.String(50))
    description = db.Column(db.Text)
    photo_filename = db.Column(db.String(200))

    votes = db.relationship("Vote", backref="candidate", cascade="all, delete-orphan")


class VotingCode(db.Model):
    __tablename__ = "voting_codes"

    id = db.Column(db.Integer, primary_key=True)
    election_id = db.Column(db.Integer, db.ForeignKey("elections.id"), nullable=False)
    code = db.Column(db.String(8), unique=True, nullable=False, index=True)
    is_used = db.Column(db.Boolean, default=False)
    used_at = db.Column(db.DateTime)
    class_name = db.Column(db.String(50))


class SchoolClass(db.Model):
    __tablename__ = "school_classes"

    id = db.Column(db.Integer, primary_key=True)
    election_id = db.Column(db.Integer, db.ForeignKey("elections.id"), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    student_count = db.Column(db.Integer, nullable=False)


class Vote(db.Model):
    __tablename__ = "votes"
    # Bewusst KEIN Bezug zu voting_codes -> Anonymität

    id = db.Column(db.Integer, primary_key=True)
    election_id = db.Column(db.Integer, db.ForeignKey("elections.id"), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey("candidates.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
