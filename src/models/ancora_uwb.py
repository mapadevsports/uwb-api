from src.models.user import db
from datetime import datetime

class AncoraUWB(db.Model):
    __tablename__ = 'ancoras_uwb'
    id = db.Column(db.Integer, primary_key=True)
    ancora_id = db.Column(db.String(50), unique=True, nullable=False)
    x = db.Column(db.Float, nullable=False)
    y = db.Column(db.Float, nullable=False)
    ultima_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<AncoraUWB {self.ancora_id} - X:{self.x}, Y:{self.y}>"

