from app import db


class Flamapy(db.Model):
    """
    Minimal placeholder model for Flamapy records. The module only needs a SQLAlchemy
    model so repositories/services can be instantiated without import errors.
    """

    __tablename__ = "flamapy"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, default="flamapy")

    def __repr__(self):
        return f"Flamapy<{self.id}:{self.name}>"
