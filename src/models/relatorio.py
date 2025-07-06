from src.models.user import db
from datetime import datetime

class Relatorio(db.Model):
    __tablename__ = 'relatorio'
    
    id = db.Column(db.Integer, primary_key=True)
    inicio_do_relatorio = db.Column(db.DateTime, nullable=True)
    fim_do_relatorio = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='inativo', nullable=False)  # 'ativo', 'inativo', 'finalizado'
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<Relatorio id={self.id} status={self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'inicio_do_relatorio': self.inicio_do_relatorio.isoformat() if self.inicio_do_relatorio else None,
            'fim_do_relatorio': self.fim_do_relatorio.isoformat() if self.fim_do_relatorio else None,
            'status': self.status,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None
        }

