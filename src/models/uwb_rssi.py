# src/models/uwb_rssi.py
from src.models.user import db
from datetime import datetime

class UWBDataRSSI(db.Model):
    __tablename__ = 'distancias_uwb_rssi'

    id = db.Column(db.Integer, primary_key=True)
    tag_number = db.Column(db.String(50), nullable=False)

    # Distâncias por âncora (até 8)
    da0 = db.Column(db.Float, nullable=True)
    da1 = db.Column(db.Float, nullable=True)
    da2 = db.Column(db.Float, nullable=True)
    da3 = db.Column(db.Float, nullable=True)
    da4 = db.Column(db.Float, nullable=True)
    da5 = db.Column(db.Float, nullable=True)
    da6 = db.Column(db.Float, nullable=True)
    da7 = db.Column(db.Float, nullable=True)

    # RSSI por âncora (até 8)
    rssi0 = db.Column(db.Float, nullable=True)
    rssi1 = db.Column(db.Float, nullable=True)
    rssi2 = db.Column(db.Float, nullable=True)
    rssi3 = db.Column(db.Float, nullable=True)
    rssi4 = db.Column(db.Float, nullable=True)
    rssi5 = db.Column(db.Float, nullable=True)
    rssi6 = db.Column(db.Float, nullable=True)
    rssi7 = db.Column(db.Float, nullable=True)

    criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<UWBDataRSSI tag={self.tag_number} id={self.id}>'
{"status":500,"name":"Error","message":"Input buffer contains unsupported image format"}