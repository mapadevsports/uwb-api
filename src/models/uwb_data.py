from src.models.user import db
from datetime import datetime

class UWBData(db.Model):
    __tablename__ = 'distancias_uwb'
    
    id = db.Column(db.Integer, primary_key=True)
    tag_number = db.Column(db.String(50), nullable=False)
    X = db.Column(db.Float, nullable=True)
    Y = db.Column(db.Float, nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<UWBData tag={self.tag_number} id={self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'tag_number': self.tag_number,
            'X': self.X,
            'Y': self.Y,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None
        }
