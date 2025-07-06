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
    """
    Modelo atualizado para armazenar resultados de trilateração
    - x: Coordenada X calculada pela trilateração (substitui da0)
    - y: Coordenada Y calculada pela trilateração (substitui da1)
    - Campos da2-da7 removidos conforme nova estrutura
    """
    __tablename__ = 'distancias_processadas'

    id = db.Column(db.Integer, primary_key=True)
    tag_number = db.Column(db.String(50), nullable=False)
    x = db.Column(db.Float, nullable=True)  # Coordenada X (resultado da trilateração)
    y = db.Column(db.Float, nullable=True)  # Coordenada Y (resultado da trilateração)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<UWBDataProcessada tag={self.tag_number} x={self.x} y={self.y}>'

    def to_dict(self):
        return {
            'id': self.id,
            'tag_number': self.tag_number,
            'x': self.x,
            'y': self.y,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None
        }

    def to_dict_detalhado(self):
        """
        Retorna dicionário com informações detalhadas incluindo metadados
        """
        return {
            'id': self.id,
            'tag_number': self.tag_number,
            'posicao': {
                'x': self.x,
                'y': self.y,
                'unidade': 'cm'
            },
            'metadados': {
                'algoritmo': 'trilateracao_minimos_quadrados',
                'ancoras_utilizadas': ['da0', 'da1', 'da2'],
                'area_maxima': {'x_max': 114, 'y_max': 114}
            },
            'criado_em': self.criado_em.isoformat() if self.criado_em else None
        }

