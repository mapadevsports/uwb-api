from src.models.user import db
from datetime import datetime

class Relatorio(db.Model):
    __tablename__ = 'relatorio'
    
    relatorio_number = db.Column(db.Integer, primary_key=True)  # Usando relatorio_number como PK
    inicio_do_relatorio = db.Column(db.DateTime, nullable=True)
    fim_do_relatorio = db.Column(db.DateTime, nullable=True)
    # Removendo colunas que não existem na tabela real
    # status = db.Column(db.String(20), default='inativo', nullable=False)
    # criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    # atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<Relatorio relatorio_number={self.relatorio_number}>'

    def to_dict(self):
        return {
            'relatorio_number': self.relatorio_number,
            'inicio_do_relatorio': self.inicio_do_relatorio.isoformat() if self.inicio_do_relatorio else None,
            'fim_do_relatorio': self.fim_do_relatorio.isoformat() if self.fim_do_relatorio else None
        }
    
    @property
    def status(self):
        """Propriedade calculada para determinar o status baseado nos timestamps"""
        if self.inicio_do_relatorio and not self.fim_do_relatorio:
            return 'ativo'
        elif self.inicio_do_relatorio and self.fim_do_relatorio:
            return 'finalizado'
        else:
            return 'inativo'

