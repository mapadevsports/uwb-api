from flask import Blueprint, jsonify, request
from src.models.uwb_data import UWBData, UWBDataProcessada, db
from src.models.relatorio import Relatorio
from datetime import datetime
import numpy as np
import math
import logging

uwb_bp = Blueprint('uwb', __name__)

class TrilateracaoUWB:
    """
    Classe para calcular posição usando trilateração com correção e mínimos quadrados
    Integrada diretamente na API para melhor performance
    """
    
    def __init__(self):
        # Coordenadas das âncoras conforme especificação
        self.ancoras = {
            'da0': (0, 0),      # Âncora 0: origem
            'da1': (114, 0),    # Âncora 1: 114cm no eixo X
            'da2': (0, 114),    # Âncora 2: 114cm no eixo Y
            'da3': (114, 114),  # Âncora 3: opcional
            'da4': (57, 57),    # Âncora 4: opcional
            'da5': (57, 0),     # Âncora 5: opcional
            'da6': (0, 57),     # Âncora 6: opcional
            'da7': (114, 57)    # Âncora 7: opcional
        }
    
    def calcular_trilateracao_basica(self, da0: float, da1: float, da2: float) -> tuple:
        """Trilateração básica com 3 âncoras principais"""
        try:
            # Verificar distâncias válidas
            if da0 <= 0 or da1 <= 0 or da2 <= 0:
                return 57.0, 57.0
            
            # Cálculo analítico
            A = 2 * 114  # 2 * (x1 - x0)
            B = 2 * 114  # 2 * (y2 - y0)
            C = da0**2 - da1**2 + 114**2  # r0² - r1² + x1²
            D = da0**2 - da2**2 + 114**2  # r0² - r2² + y2²
            
            x = C / A if A != 0 else 57.0
            y = D / B if B != 0 else 57.0
            
            return x, y
            
        except Exception as e:
            logging.warning(f"Erro na trilateração básica: {e}")
            return 57.0, 57.0
    
    def calcular_minimos_quadrados(self, distancias: dict) -> tuple:
        """Mínimos quadrados com todas as âncoras disponíveis"""
        try:
            # Filtrar âncoras válidas
            ancoras_validas = []
            distancias_validas = []
            
            for ancora_id, distancia in distancias.items():
                if (ancora_id in self.ancoras and 
                    distancia is not None and 
                    distancia > 0):
                    ancoras_validas.append(self.ancoras[ancora_id])
                    distancias_validas.append(distancia)
            
            if len(ancoras_validas) < 3:
                # Fallback para trilateração básica
                da0 = distancias.get('da0', 50)
                da1 = distancias.get('da1', 50)
                da2 = distancias.get('da2', 50)
                return self.calcular_trilateracao_basica(da0, da1, da2)
            
            # Método matricial dos mínimos quadrados
            n = len(ancoras_validas)
            x0, y0 = ancoras_validas[0]
            r0 = distancias_validas[0]
            
            A = np.zeros((n-1, 2))
            b = np.zeros(n-1)
            
            for i in range(1, n):
                xi, yi = ancoras_validas[i]
                ri = distancias_validas[i]
                
                A[i-1, 0] = 2 * (xi - x0)
                A[i-1, 1] = 2 * (yi - y0)
                b[i-1] = ri**2 - r0**2 - xi**2 + x0**2 - yi**2 + y0**2
            
            # Resolver usando pseudo-inversa
            pos = np.linalg.pinv(A) @ b
            return float(pos[0]), float(pos[1])
                
        except Exception as e:
            logging.warning(f"Erro nos mínimos quadrados: {e}")
            # Fallback para trilateração básica
            da0 = distancias.get('da0', 50)
            da1 = distancias.get('da1', 50)
            da2 = distancias.get('da2', 50)
            return self.calcular_trilateracao_basica(da0, da1, da2)
    
    def aplicar_correcao(self, x: float, y: float) -> tuple:
        """Aplica correções e limites físicos"""
        # Limitar à área física (0-114cm)
        x_corrigido = max(2.0, min(112.0, x))  # Margem de 2cm
        y_corrigido = max(2.0, min(112.0, y))
        
        return x_corrigido, y_corrigido
    
    def processar_distancias(self, da0=None, da1=None, da2=None, da3=None, 
                           da4=None, da5=None, da6=None, da7=None, kx=None, ky=None) -> tuple:
        """
        Processa distâncias e retorna posição X,Y final
        Se kx e ky forem fornecidos, usa esses valores em vez de da1 e da2
        """
        # Preparar dicionário de distâncias válidas
        distancias = {}
        
        # Se Kx e Ky foram fornecidos, usar esses valores
        if kx is not None and ky is not None:
            try:
                kx_float = float(kx)
                ky_float = float(ky)
                # Usar Kx como da1 e Ky como da2
                distancias['da0'] = da0 if da0 is not None and da0 > 0 else 50
                distancias['da1'] = kx_float
                distancias['da2'] = ky_float
                logging.info(f"Usando Kx={kx_float} como da1 e Ky={ky_float} como da2 para trilateração")
            except (ValueError, TypeError):
                logging.warning(f"Erro ao converter Kx={kx} ou Ky={ky} para float, usando valores originais")
                # Fallback para valores originais
                for i, valor in enumerate([da0, da1, da2, da3, da4, da5, da6, da7]):
                    if valor is not None and valor > 0:
                        distancias[f'da{i}'] = valor
        else:
            # Usar valores originais se Kx/Ky não fornecidos
            for i, valor in enumerate([da0, da1, da2, da3, da4, da5, da6, da7]):
                if valor is not None and valor > 0:
                    distancias[f'da{i}'] = valor
        
        # Contar âncoras válidas
        num_ancoras = len(distancias)
        
        if num_ancoras >= 4:
            # Usar mínimos quadrados para melhor precisão
            x, y = self.calcular_minimos_quadrados(distancias)
        else:
            # Usar trilateração básica
            da0_val = distancias.get('da0', 50)
            da1_val = distancias.get('da1', 50)
            da2_val = distancias.get('da2', 50)
            x, y = self.calcular_trilateracao_basica(da0_val, da1_val, da2_val)
        
        # Aplicar correções finais
        x_final, y_final = self.aplicar_correcao(x, y)
        
        return round(x_final, 2), round(y_final, 2)

# Instância global da trilateração
trilateracao = TrilateracaoUWB()

@uwb_bp.route('/uwb/data', methods=['POST'])
def receive_uwb_data():
    """
    Endpoint para receber dados UWB com processamento automático de trilateração
    TAG1 e TAG2 são sempre processadas para calibração
    Outras tags só são processadas se houver relatório ativo
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({'error': 'Nenhum dado JSON fornecido'}), 400
        
        # Validar campos obrigatórios
        if 'id' not in data or 'range' not in data:
            return jsonify({'error': 'Campos obrigatórios: id, range'}), 400
        
        tag_id = str(data['id'])
        range_values = data['range']
        
        # Validar range
        if not isinstance(range_values, list) or len(range_values) != 8:
            return jsonify({'error': 'Range deve ser uma lista com exatamente 8 valores'}), 400
        
        # Verificar se é TAG1 ou TAG2 (sempre processadas) ou outras tags
        tag_id_int = int(tag_id)
        
        if tag_id_int == 1 or tag_id_int == 2:
            # TAG1 e TAG2 são sempre aceitas para calibração, mas não salvas no banco
            return jsonify({
                'success': True,
                'message': f'TAG{tag_id_int} recebida para calibração (não salva no banco)',
                'tag_type': 'calibracao',
                'data': {
                    'tag_number': tag_id,
                    'range': range_values
                }
            }), 200
        
        # Para outras tags, verificar se há relatório ativo
        relatorio_ativo = Relatorio.query.filter(
            Relatorio.inicio_do_relatorio.isnot(None),
            Relatorio.fim_do_relatorio.is_(None)
        ).first()
        
        if not relatorio_ativo:
            return jsonify({
                'success': False,
                'message': 'Nenhum relatório ativo. Inicie um relatório para processar dados de tags.',
                'tag_number': tag_id,
                'relatorio_ativo': False
            }), 400
        
        # Criar registro original
        uwb_data = UWBData(
            tag_number=tag_id,
            da0=float(range_values[0]) if range_values[0] is not None else None,
            da1=float(range_values[1]) if range_values[1] is not None else None,
            da2=float(range_values[2]) if range_values[2] is not None else None,
            da3=float(range_values[3]) if range_values[3] is not None else None,
            da4=float(range_values[4]) if range_values[4] is not None else None,
            da5=float(range_values[5]) if range_values[5] is not None else None,
            da6=float(range_values[6]) if range_values[6] is not None else None,
            da7=float(range_values[7]) if range_values[7] is not None else None,
            criado_em=datetime.utcnow()
        )
        
        # Salvar dados originais
        db.session.add(uwb_data)
        
        # ===== PROCESSAMENTO AUTOMÁTICO COM TRILATERAÇÃO =====
        try:
            # Obter valores Kx e Ky do relatório ativo
            kx_relatorio = relatorio_ativo.kx if relatorio_ativo.kx else None
            ky_relatorio = relatorio_ativo.ky if relatorio_ativo.ky else None
            
            if kx_relatorio and ky_relatorio:
                logging.info(f"Usando Kx={kx_relatorio} e Ky={ky_relatorio} do relatório {relatorio_ativo.relatorio_number}")
            else:
                logging.info("Kx/Ky não disponíveis no relatório, usando valores originais da leitura")
            
            # Calcular posição X,Y usando trilateração com Kx/Ky do relatório
            x, y = trilateracao.processar_distancias(
                da0=uwb_data.da0,
                da1=uwb_data.da1,
                da2=uwb_data.da2,
                da3=uwb_data.da3,
                da4=uwb_data.da4,
                da5=uwb_data.da5,
                da6=uwb_data.da6,
                da7=uwb_data.da7,
                kx=kx_relatorio,
                ky=ky_relatorio
            )
            
            # Criar registro processado com coordenadas X,Y
            uwb_data_processada = UWBDataProcessada(
                tag_number=tag_id,
                x=x,
                y=y,
                criado_em=datetime.utcnow()
            )
            
            db.session.add(uwb_data_processada)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Dados UWB processados com trilateração automática',
                'data_original': uwb_data.to_dict(),
                'data_processada': uwb_data_processada.to_dict(),
                'posicao': {
                    'x': x,
                    'y': y,
                    'unidade': 'cm',
                    'algoritmo': 'trilateracao_minimos_quadrados'
                },
                'relatorio_id': relatorio_ativo.relatorio_number,
                'relatorio_ativo': True
            }), 201
            
        except Exception as processing_error:
            # Se trilateração falhar, ainda salva dados originais
            logging.error(f"Erro na trilateração: {processing_error}")
            db.session.commit()  # Commit apenas dos dados originais
            
            return jsonify({
                'success': True,
                'message': 'Dados UWB salvos (trilateração falhou)',
                'data_original': uwb_data.to_dict(),
                'processing_error': str(processing_error),
                'relatorio_id': relatorio_ativo.relatorio_number,
                'relatorio_ativo': True
            }), 201
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': f'Erro de conversão de dados: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

@uwb_bp.route('/uwb/data', methods=['GET'])
def get_uwb_data():
    """Recuperar dados UWB originais"""
    try:
        uwb_records = UWBData.query.order_by(UWBData.criado_em.desc()).limit(50).all()
        return jsonify([record.to_dict() for record in uwb_records])
    except Exception as e:
        return jsonify({'error': f'Erro ao recuperar dados: {str(e)}'}), 500

@uwb_bp.route('/uwb/posicoes', methods=['GET'])
def get_posicoes():
    """Recuperar posições calculadas (dados processados)"""
    try:
        posicoes = UWBDataProcessada.query.order_by(UWBDataProcessada.criado_em.desc()).limit(50).all()
        return jsonify([record.to_dict_detalhado() for record in posicoes])
    except Exception as e:
        return jsonify({'error': f'Erro ao recuperar posições: {str(e)}'}), 500

@uwb_bp.route('/uwb/posicoes/<tag_number>', methods=['GET'])
def get_posicoes_by_tag(tag_number):
    """Recuperar posições de uma tag específica"""
    try:
        posicoes = UWBDataProcessada.query.filter_by(tag_number=tag_number).order_by(UWBDataProcessada.criado_em.desc()).limit(50).all()
        return jsonify([record.to_dict_detalhado() for record in posicoes])
    except Exception as e:
        return jsonify({'error': f'Erro ao recuperar posições: {str(e)}'}), 500

@uwb_bp.route('/uwb/posicao-atual/<tag_number>', methods=['GET'])
def get_posicao_atual(tag_number):
    """Recuperar última posição conhecida de uma tag"""
    try:
        posicao = UWBDataProcessada.query.filter_by(tag_number=tag_number).order_by(UWBDataProcessada.criado_em.desc()).first()
        if posicao:
            return jsonify(posicao.to_dict_detalhado())
        else:
            return jsonify({'error': 'Tag não encontrada'}), 404
    except Exception as e:
        return jsonify({'error': f'Erro ao recuperar posição atual: {str(e)}'}), 500

@uwb_bp.route('/uwb/health', methods=['GET'])
def health_check():
    """Health check com informações do sistema"""
    return jsonify({
        'status': 'OK',
        'message': 'API UWB com trilateração automática ativa',
        'features': [
            'trilateracao_automatica',
            'minimos_quadrados', 
            'correcao_posicao',
            'dados_originais',
            'posicoes_calculadas'
        ],
        'ancoras_configuradas': {
            'da0': '(0, 0)',
            'da1': '(114, 0)',
            'da2': '(0, 114)',
            'da3': '(114, 114) - opcional',
            'da4': '(57, 57) - opcional',
            'da5': '(57, 0) - opcional',
            'da6': '(0, 57) - opcional',
            'da7': '(114, 57) - opcional'
        },
        'area_trabalho': '114x114 cm',
        'timestamp': datetime.utcnow().isoformat()
    })

@uwb_bp.route('/uwb/teste-trilateracao', methods=['POST'])
def teste_trilateracao():
    """Endpoint para testar trilateração com dados customizados"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Dados necessários para teste'}), 400
        
        # Extrair distâncias do JSON
        distancias = {}
        for i in range(8):
            key = f'da{i}'
            if key in data and data[key] is not None:
                distancias[key] = float(data[key])
        
        # Calcular posição
        x, y = trilateracao.processar_distancias(**distancias)
        
        return jsonify({
            'entrada': distancias,
            'resultado': {
                'x': x,
                'y': y,
                'unidade': 'cm'
            },
            'metadados': {
                'ancoras_utilizadas': len(distancias),
                'algoritmo': 'trilateracao_minimos_quadrados' if len(distancias) >= 4 else 'trilateracao_basica'
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro no teste: {str(e)}'}), 500

# Manter endpoint manual para compatibilidade (opcional)
@uwb_bp.route('/uwb/reprocessar', methods=['POST'])
def reprocessar_dados():
    """Reprocessar dados existentes com trilateração"""
    try:
        # Buscar dados não processados
        dados_nao_processados = db.session.query(UWBData).filter(
            ~db.session.query(UWBDataProcessada).filter(
                UWBDataProcessada.tag_number == UWBData.tag_number,
                UWBDataProcessada.criado_em >= UWBData.criado_em
            ).exists()
        ).all()
        
        processados = 0
        for dado in dados_nao_processados:
            # Calcular posição usando trilateração
            x, y = trilateracao.processar_distancias(
                da0=dado.da0, da1=dado.da1, da2=dado.da2, da3=dado.da3,
                da4=dado.da4, da5=dado.da5, da6=dado.da6, da7=dado.da7
            )
            
            # Criar registro processado
            nova_posicao = UWBDataProcessada(
                tag_number=dado.tag_number,
                x=x,
                y=y,
                criado_em=datetime.utcnow()
            )
            
            db.session.add(nova_posicao)
            processados += 1

        db.session.commit()
        return jsonify({
            'status': 'reprocessamento concluído',
            'registros_processados': processados,
            'algoritmo': 'trilateracao_minimos_quadrados'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

