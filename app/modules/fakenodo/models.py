from app import db


class Fakenodo(db.Model):
    """
    Simple model that represents a simulated deposition in Fakenodo.
    """

    id = db.Column(db.Integer, primary_key=True)
    meta_data = db.Column(db.JSON, nullable=False)
    status = db.Column(db.String(100), nullable=False, default="draft")
    doi = db.Column(db.String(250), unique=True, nullable=True)

    def __repr__(self):
        return f"<Fakenodo {self.id}>"

    def __init__(self, meta_data, doi=None):
        self.meta_data = meta_data
        self.doi = doi
