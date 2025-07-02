from src.models.user import db
from datetime import datetime

class UWBData(db.Model):
    __tablename__ = 'distancias_uwb'
    
    id = db.Column(db.Integer, primary_key=True)
    tag_number = db.Column(db.String(50), nullable=False)
    da0 = db.Column(db.Float, nullable=True)
    da1 = db.Column(db.Float, nullable=True)
    da2 = db.Column(db.Float, nullable=True)
    da3 = db.Column(db.Float, nullable=True)
    da4 = db.Column(db.Float, nullable=True)
    da5 = db.Column(db.Float, nullable=True)
    da6 = db.Column(db.Float, nullable=True)
    da7 = db.Column(db.Float, nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<UWBData tag={self.tag_number} id={self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'tag_number': self.tag_number,
            'da0': self.da0,
            'da1': self.da1,
            'da2': self.da2,
            'da3': self.da3,
            'da4': self.da4,
            'da5': self.da5,
            'da6': self.da6,
            'da7': self.da7,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None
        }
class UWBDataProcessada(db.Model):
    __tablename__ = 'distancias_processadas'

    id = db.Column(db.Integer, primary_key=True)
    tag_number = db.Column(db.String(50), nullable=False)
    da0 = db.Column(db.Float, nullable=True)
    da1 = db.Column(db.Float, nullable=True)
    da2 = db.Column(db.Float, nullable=True)
    da3 = db.Column(db.Float, nullable=True)
    da4 = db.Column(db.Float, nullable=True)
    da5 = db.Column(db.Float, nullable=True)
    da6 = db.Column(db.Float, nullable=True)
    da7 = db.Column(db.Float, nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<UWBDataProcessada tag={self.tag_number} id={self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'tag_number': self.tag_number,
            'da0': self.da0,
            'da1': self.da1,
            'da2': self.da2,
            'da3': self.da3,
            'da4': self.da4,
            'da5': self.da5,
            'da6': self.da6,
            'da7': self.da7,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None
        }

