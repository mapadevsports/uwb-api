from flask import Blueprint, jsonify, request
from src.models.uwb_data import UWBData, UWBDataProcessada, db
from src.models.relatorio import Relatorio
from datetime import datetime
import numpy as np
import math
import logging
import json
# Limite mínimo de variação por eixo para considerar gravação
ERRO_MIN_EIXO_CM = 5.0
ultimo_xy = {}


uwb_bp = Blueprint('uwb', __name__)

class TrilateracaoUWB:
    """
    Classe para calcular posição usando trilateração com correção e mínimos quadrados
    Integrada diretamente na API para melhor performance
    """
    
    def __init__(self):
        # Coordenadas das âncoras serão definidas dinamicamente com base em kx e ky
        # Valores padrão caso kx e ky não estejam disponíveis
        self.ancoras_padrao = {
            'da0': (0, 0),      # Âncora 0: sempre origem (0,0)
            'da1': (114, 0),    # Âncora 1: padrão 114cm no eixo X (será substituído por kx)
            'da2': (0, 114),    # Âncora 2: padrão 114cm no eixo Y (será substituído por ky)
            'da3': (114, 114),  # Âncora 3: opcional
            'da4': (57, 57),    # Âncora 4: opcional
            'da5': (57, 0),     # Âncora 5: opcional
            'da6': (0, 57),     # Âncora 6: opcional
            'da7': (114, 57)    # Âncora 7: opcional
        }
    
    def obter_coordenadas_ancoras(self, kx=None, ky=None):
        """
        Retorna as coordenadas das âncoras baseadas nos valores kx e ky do relatório
        """
        ancoras = self.ancoras_padrao.copy()
        
        if kx is not None and ky is not None:
            try:
                kx_float = float(kx)
                ky_float = float(ky)
                
                # Definir coordenadas conforme especificação do usuário:
                # Âncora 0: sempre (0, 0)
                # Âncora 1: (kx, 0) - kx do relatório no eixo X, 0 no eixo Y
                # Âncora 2: (0, ky) - 0 no eixo X, ky do relatório no eixo Y
                ancoras['da0'] = (0, 0)
                ancoras['da1'] = (kx_float, 0)
                ancoras['da2'] = (0, ky_float)
                
                # Atualizar outras âncoras proporcionalmente se necessário
                ancoras['da3'] = (kx_float, ky_float)
                ancoras['da4'] = (kx_float/2, ky_float/2)
                ancoras['da5'] = (kx_float/2, 0)
                ancoras['da6'] = (0, ky_float/2)
                ancoras['da7'] = (kx_float, ky_float/2)
                
                logging.info(f"[DEBUG] Coordenadas das âncoras atualizadas com kx={kx_float}, ky={ky_float}")
                logging.info(f"[DEBUG] Âncora 0: {ancoras['da0']}, Âncora 1: {ancoras['da1']}, Âncora 2: {ancoras['da2']}")
                
            except (ValueError, TypeError) as e:
                logging.warning(f"[DEBUG] Erro ao converter kx={kx} ou ky={ky} para float: {e}. Usando valores padrão.")
        else:
            logging.info("[DEBUG] kx ou ky não fornecidos, usando coordenadas padrão das âncoras")
        
        return ancoras
    
    def calcular_trilateracao_basica(self, da0: float, da1: float, da2: float, kx=None, ky=None) -> tuple:
        """Trilateração básica com 3 âncoras principais usando coordenadas dinâmicas"""
        try:
            logging.info(f"[DEBUG] Iniciando trilateração básica com da0={da0}, da1={da1}, da2={da2}")
            
            # Verificar distâncias válidas
            if da0 <= 0 or da1 <= 0 or da2 <= 0:
                logging.warning(f"[DEBUG] Distâncias inválidas detectadas: da0={da0}, da1={da1}, da2={da2}")
                return 57.0, 57.0
            
            # Obter coordenadas das âncoras
            ancoras = self.obter_coordenadas_ancoras(kx, ky)
            
            # Coordenadas das âncoras
            x0, y0 = ancoras['da0']  # (0, 0)
            x1, y1 = ancoras['da1']  # (kx, 0)
            x2, y2 = ancoras['da2']  # (0, ky)
            
            logging.info(f"[DEBUG] Coordenadas das âncoras: A0=({x0},{y0}), A1=({x1},{y1}), A2=({x2},{y2})")
            
            # Raios
            r0, r1, r2 = da0, da1, da2
            
            # Cálculo analítico da trilateração
            A = 2 * (x1 - x0)  # 2 * (kx - 0) = 2 * kx
            B = 2 * (y1 - y0)  # 2 * (0 - 0) = 0
            C = r0**2 - r1**2 + x1**2 - x0**2 + y1**2 - y0**2  # r0² - r1² + kx²
            
            D = 2 * (x2 - x0)  # 2 * (0 - 0) = 0
            E = 2 * (y2 - y0)  # 2 * (ky - 0) = 2 * ky
            F = r0**2 - r2**2 + x2**2 - x0**2 + y2**2 - y0**2  # r0² - r2² + ky²
            
            logging.info(f"[DEBUG] Coeficientes do sistema: A={A}, B={B}, C={C}, D={D}, E={E}, F={F}")
            
            # Resolver o sistema:
            if A != 0:  # Se kx != 0
                x = C / A  # x = (r0² - r1² + kx²) / (2*kx)
            else:
                x = 57.0  # Valor padrão se kx = 0
                logging.warning("[DEBUG] A=0, usando valor padrão x=57.0")
            
            if E != 0:  # Se ky != 0
                y = F / E  # y = (r0² - r2² + ky²) / (2*ky)
            else:
                y = 57.0  # Valor padrão se ky = 0
                logging.warning("[DEBUG] E=0, usando valor padrão y=57.0")
            
            logging.info(f"[DEBUG] Trilateração básica resultado: x={x:.2f}, y={y:.2f}")
            return x, y
            
        except Exception as e:
            logging.error(f"[DEBUG] Erro na trilateração básica: {e}")
            return 57.0, 57.0
    
    def calcular_minimos_quadrados(self, distancias: dict, kx=None, ky=None) -> tuple:
        """Mínimos quadrados com todas as âncoras disponíveis usando coordenadas dinâmicas"""
        try:
            logging.info(f"[DEBUG] Iniciando mínimos quadrados com {len(distancias)} âncoras")
            
            # Obter coordenadas das âncoras
            ancoras = self.obter_coordenadas_ancoras(kx, ky)
            
            # Filtrar âncoras válidas
            ancoras_validas = []
            distancias_validas = []
            
            for ancora_id, distancia in distancias.items():
                if (ancora_id in ancoras and 
                    distancia is not None and 
                    distancia > 0):
                    ancoras_validas.append(ancoras[ancora_id])
                    distancias_validas.append(distancia)
                    logging.info(f"[DEBUG] Âncora válida {ancora_id}: coord={ancoras[ancora_id]}, dist={distancia}")
                else:
                    logging.warning(f"[DEBUG] Âncora inválida {ancora_id}: dist={distancia}")
            
            if len(ancoras_validas) < 3:
                logging.warning(f"[DEBUG] Poucas âncoras válidas ({len(ancoras_validas)}), usando trilateração básica")
                # Fallback para trilateração básica
                da0 = distancias.get('da0', 50)
                da1 = distancias.get('da1', 50)
                da2 = distancias.get('da2', 50)
                return self.calcular_trilateracao_basica(da0, da1, da2, kx, ky)
            
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
            
            logging.info(f"[DEBUG] Matriz A: {A}")
            logging.info(f"[DEBUG] Vetor b: {b}")
            
            # Resolver usando pseudo-inversa
            pos = np.linalg.pinv(A) @ b
            
            logging.info(f"[DEBUG] Mínimos quadrados resultado: x={pos[0]:.2f}, y={pos[1]:.2f}")
            return float(pos[0]), float(pos[1])
                
        except Exception as e:
            logging.error(f"[DEBUG] Erro nos mínimos quadrados: {e}")
            # Fallback para trilateração básica
            da0 = distancias.get('da0', 50)
            da1 = distancias.get('da1', 50)
            da2 = distancias.get('da2', 50)
            return self.calcular_trilateracao_basica(da0, da1, da2, kx, ky)
    
    def aplicar_correcao(self, x: float, y: float, kx=None, ky=None) -> tuple:
        """Aplica correções e limites físicos baseados nas dimensões reais"""
        # Usar dimensões baseadas em kx e ky se disponíveis
        max_x = float(kx) if kx is not None else 114.0
        max_y = float(ky) if ky is not None else 114.0
        
        logging.info(f"[DEBUG] Aplicando correção: entrada x={x:.2f}, y={y:.2f}, limites max_x={max_x}, max_y={max_y}")
        
        # Limitar à área física com margem de 2cm
        x_corrigido = max(2.0, min(max_x - 2.0, x))
        y_corrigido = max(2.0, min(max_y - 2.0, y))
        
        logging.info(f"[DEBUG] Correção aplicada: saída x={x_corrigido:.2f}, y={y_corrigido:.2f}")
        
        return x_corrigido, y_corrigido
    
    def processar_distancias(self, da0=None, da1=None, da2=None, da3=None, 
                           da4=None, da5=None, da6=None, da7=None, kx=None, ky=None) -> tuple:
        """
        Processa distâncias e retorna posição X,Y final
        Usa kx e ky para definir as coordenadas das âncoras 1 e 2
        """
        logging.info(f"[DEBUG] Processando distâncias: da0={da0}, da1={da1}, da2={da2}, da3={da3}, da4={da4}, da5={da5}, da6={da6}, da7={da7}")
        
        # Preparar dicionário de distâncias válidas
        distancias = {}
        
        # Usar valores das distâncias medidas (da0, da1, da2, etc.)
        for i, valor in enumerate([da0, da1, da2, da3, da4, da5, da6, da7]):
            if valor is not None and valor > 0:
                distancias[f'da{i}'] = valor
        
        logging.info(f"[DEBUG] Distâncias válidas: {distancias}")
        
        # Contar âncoras válidas
        num_ancoras = len(distancias)
        
        if num_ancoras >= 4:
            logging.info(f"[DEBUG] Usando mínimos quadrados com {num_ancoras} âncoras")
            # Usar mínimos quadrados para melhor precisão
            x, y = self.calcular_minimos_quadrados(distancias, kx, ky)
        else:
            logging.info(f"[DEBUG] Usando trilateração básica com {num_ancoras} âncoras")
            # Usar trilateração básica
            da0_val = distancias.get('da0', 50)
            da1_val = distancias.get('da1', 50)
            da2_val = distancias.get('da2', 50)
            x, y = self.calcular_trilateracao_basica(da0_val, da1_val, da2_val, kx, ky)
        
        # Aplicar correções finais
        x_final, y_final = self.aplicar_correcao(x, y, kx, ky)
        
        logging.info(f"[DEBUG] Posição final calculada: x={x_final:.2f}, y={y_final:.2f}")
        
        return round(x_final, 2), round(y_final, 2)

# Instância global da trilateração
trilateracao = TrilateracaoUWB()

def validar_e_converter_array(range_data, campo_nome="range"):
    """
    Valida e converte dados de array de diferentes formatos para lista de floats
    Suporta: lista, string JSON, string separada por vírgulas
    """
    logging.info(f"[DEBUG] Validando array {campo_nome}: tipo={type(range_data)}, valor={range_data}")
    
    try:
        # Se já é uma lista
        if isinstance(range_data, list):
            logging.info(f"[DEBUG] {campo_nome} já é uma lista")
            resultado = []
            for i, valor in enumerate(range_data):
                try:
                    if valor is None or valor == "":
                        resultado.append(None)
                    else:
                        resultado.append(float(valor))
                except (ValueError, TypeError) as e:
                    logging.warning(f"[DEBUG] Erro ao converter elemento {i} ({valor}) para float: {e}")
                    resultado.append(None)
            return resultado
        
        # Se é uma string, tentar diferentes formatos
        elif isinstance(range_data, str):
            logging.info(f"[DEBUG] {campo_nome} é string, tentando conversões")
            
            # Tentar JSON primeiro
            try:
                array_json = json.loads(range_data)
                if isinstance(array_json, list):
                    logging.info(f"[DEBUG] {campo_nome} convertido de JSON com sucesso")
                    return validar_e_converter_array(array_json, campo_nome)
            except json.JSONDecodeError:
                logging.info(f"[DEBUG] {campo_nome} não é JSON válido")
            
            # Tentar separação por vírgulas
            try:
                elementos = range_data.split(',')
                logging.info(f"[DEBUG] {campo_nome} separado por vírgulas: {elementos}")
                resultado = []
                for elemento in elementos:
                    elemento = elemento.strip()
                    if elemento == "" or elemento.lower() == "null":
                        resultado.append(None)
                    else:
                        resultado.append(float(elemento))
                return resultado
            except (ValueError, TypeError) as e:
                logging.error(f"[DEBUG] Erro ao converter string separada por vírgulas: {e}")
        
        # Se não conseguiu converter
        logging.error(f"[DEBUG] Não foi possível converter {campo_nome} para array válido")
        return None
        
    except Exception as e:
        logging.error(f"[DEBUG] Erro geral na validação do array {campo_nome}: {e}")
        return None

@uwb_bp.route("/uwb/data", methods=["POST"])
def receive_uwb_data():
    """
    Endpoint para receber dados UWB com processamento automático de trilateração
    TAG1 e TAG2 são sempre processadas para calibração
    Outras tags só são processadas se houver relatório ativo
    
    Suporta múltiplos formatos de entrada para arrays:
    - Lista: {"id": "3", "range": [10.5, 20.3, 15.7, ...]}\n    - String JSON: {"id": "3", "range": "[10.5, 20.3, 15.7, ...]"}\n    - String CSV: {"id": "3", "range": "10.5,20.3,15.7,..."}\n    - **NOVO: Array de objetos JSON**: [{"id": "3", "range": [...]}, {"id": "4", "range": [...]}]
    """
    try:
        logging.info(f"[DEBUG] Requisição POST recebida no endpoint /uwb/data")
        logging.info(f"[DEBUG] Content-Type: {request.content_type}")
        raw_data = request.get_data()
        logging.info(f"[DEBUG] Dados brutos: {raw_data}")
        
        data = request.json
        
        if not data:
            logging.error("[DEBUG] Nenhum dado JSON fornecido na requisição")
            return jsonify({'error': 'Nenhum dado JSON fornecido'}), 400
        
        # Se for um array de objetos, processar cada um
        if isinstance(data, list):
            logging.info(f"[DEBUG] Recebido um array de {len(data)} objetos. Processando cada um.")
            results = []
            for item in data:
                try:
                    # Processar cada item individualmente
                    result = process_single_uwb_data_item(item)
                    results.append(result)
                except Exception as e:
                    logging.error(f"[DEBUG] Erro ao processar item do array: {item}. Erro: {e}")
                    results.append({'error': f'Erro ao processar item: {str(e)}', 'item': item})
            
            # Retornar uma lista de resultados
            return jsonify(results), 200 if all('success' in r for r in results) else 207 # 207 Multi-Status
        
        # Se for um único objeto, processar normalmente
        else:
            logging.info(f"[DEBUG] Recebido um único objeto JSON.")
            result = process_single_uwb_data_item(data)
            return jsonify(result), 201 if 'success' in result else 400
            
    except ValueError as e:
        logging.error(f"[DEBUG] Erro de conversão de dados: {e}")
        db.session.rollback()
        return jsonify({
            'error': f'Erro de conversão de dados: {str(e)}',
            'debug_info': {
                'dados_recebidos': str(raw_data),
                'content_type': request.content_type
            }
        }), 400
    except Exception as e:
        logging.error(f"[DEBUG] Erro interno do servidor: {e}")
        db.session.rollback()
        return jsonify({
            'error': f'Erro interno do servidor: {str(e)}',
            'debug_info': {
                'dados_recebidos': str(raw_data),
                'content_type': request.content_type
            }
        }), 500

def process_single_uwb_data_item(data):
    """
    Função auxiliar para processar um único objeto de dados UWB.
    """
    try:
        # Validar campos obrigatórios
        if 'id' not in data:
            logging.error("[DEBUG] Campo 'id' não encontrado nos dados do item")
            return {'error': 'Campo obrigatório: id'}
            
        if 'range' not in data:
            logging.error("[DEBUG] Campo 'range' não encontrado nos dados do item")
            return {'error': 'Campo obrigatório: range'}
        
        tag_id = str(data['id'])
        range_data = data['range']
        
        logging.info(f"[DEBUG] Processando item - Tag ID: {tag_id}, Range data: {range_data} (tipo: {type(range_data)})")
        
        # Validar e converter array de range
        range_values = validar_e_converter_array(range_data, "range")
        
        if range_values is None:
            logging.error(f"[DEBUG] Falha na validação do array range do item: {range_data}")
            return {'error': 'Range deve ser um array válido (lista, JSON string ou CSV string)'}
        
        # Verificar se tem exatamente 8 valores
        if len(range_values) != 8:
            logging.error(f"[DEBUG] Array range do item tem {len(range_values)} elementos, esperado 8")
            return {'error': f'Range deve ter exatamente 8 valores, recebido {len(range_values)}'}
        
        logging.info(f"[DEBUG] Array range do item validado com sucesso: {range_values}")
        
        # Verificar se é TAG1 ou TAG2 (sempre processadas) ou outras tags
        try:
            tag_id_int = int(tag_id)
            logging.info(f"[DEBUG] Tag ID do item convertido para inteiro: {tag_id_int}")
        except ValueError:
            logging.error(f"[DEBUG] Erro ao converter tag_id '{tag_id}' do item para inteiro")
            return {'error': f'ID da tag deve ser um número válido, recebido: {tag_id}'}
        
        if tag_id_int == 1 or tag_id_int == 2:
            logging.info(f"[DEBUG] TAG{tag_id_int} do item identificada como tag de calibração")
            return {
                'success': True,
                'message': f'TAG{tag_id_int} recebida para calibração (não salva no banco)',
                'tag_type': 'calibracao',
                'data': {
                    'tag_number': tag_id,
                    'range': range_values
                },
                'debug_info': {
                    'array_original': range_data,
                    'array_processado': range_values,
                    'tipo_original': str(type(range_data))
                }
            }
        
        # Para outras tags, verificar se há relatório ativo
        logging.info(f"[DEBUG] Verificando relatório ativo para TAG{tag_id_int} do item")
        relatorio_ativo = Relatorio.query.filter(
            Relatorio.inicio_do_relatorio.isnot(None),
            Relatorio.fim_do_relatorio.is_(None)
        ).first()
        
        if not relatorio_ativo:
            logging.warning(f"[DEBUG] Nenhum relatório ativo encontrado para TAG{tag_id_int} do item")
            return {
                'success': False,
                'message': 'Nenhum relatório ativo. Inicie um relatório para processar dados de tags.',
                'tag_number': tag_id,
                'relatorio_ativo': False,
                'debug_info': {
                    'array_original': range_data,
                    'array_processado': range_values,
                    'tipo_original': str(type(range_data))
                }
            }
        
        logging.info(f"[DEBUG] Relatório ativo encontrado para item: {relatorio_ativo.relatorio_number}")
        
        # Criar registro original
        uwb_data = UWBData(
            tag_number=tag_id,
            da0=range_values[0] if range_values[0] is not None else None,
            da1=range_values[1] if range_values[1] is not None else None,
            da2=range_values[2] if range_values[2] is not None else None,
            da3=range_values[3] if range_values[3] is not None else None,
            da4=range_values[4] if range_values[4] is not None else None,
            da5=range_values[5] if range_values[5] is not None else None,
            da6=range_values[6] if range_values[6] is not None else None,
            da7=range_values[7] if range_values[7] is not None else None,
            criado_em=datetime.utcnow()
        )
        
        logging.info(f"[DEBUG] Registro UWBData do item criado: da0={uwb_data.da0}, da1={uwb_data.da1}, da2={uwb_data.da2}, da3={uwb_data.da3}, da4={uwb_data.da4}, da5={uwb_data.da5}, da6={uwb_data.da6}, da7={uwb_data.da7}")
        
        # Salvar dados originais
        db.session.add(uwb_data)
        
        # ===== PROCESSAMENTO AUTOMÁTICO COM TRILATERAÇÃO =====
        try:
            kx_relatorio = relatorio_ativo.kx if relatorio_ativo.kx else None
            ky_relatorio = relatorio_ativo.ky if relatorio_ativo.ky else None
            
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
                        # Verificação de variação mínima em x e y
            global ultimo_xy
            if tag_id in ultimo_xy:
                x_ant, y_ant = ultimo_xy[tag_id]
                dx = abs(x - x_ant)
                dy = abs(y - y_ant)

                if dx < ERRO_MIN_EIXO_CM and dy < ERRO_MIN_EIXO_CM:
                    logging.info(f"[DEBUG] Dados descartados para tag {tag_id} - Δx: {dx:.1f}cm, Δy: {dy:.1f}cm abaixo do limite")
                    db.session.commit()  # Salva apenas os dados crus
                    return {
                        'success': True,
                        'message': 'Dados UWB salvos, mas não processados (movimento pequeno)',
                        'data_original': uwb_data.to_dict(),
                        'descartado_por_movimento': True,
                        'relatorio_id': relatorio_ativo.relatorio_number,
                        'debug_info': {
                            'dx': dx,
                            'dy': dy,
                            'limite_minimo_cm': ERRO_MIN_EIXO_CM
                        }
                    }

            # Atualiza histórico
            ultimo_xy[tag_id] = (x, y)

            
            uwb_data_processada = UWBDataProcessada(
                tag_number=tag_id,
                x=x,
                y=y,
                criado_em=datetime.utcnow()
            )
            
            db.session.add(uwb_data_processada)
            db.session.commit()
            
            logging.info(f"[DEBUG] Dados do item salvos com sucesso - Original ID: {uwb_data.id}, Processado ID: {uwb_data_processada.id}")
            
            return {
                'success': True,
                'message': 'Dados UWB processados com trilateração automática',
                'data_original': uwb_data.to_dict(),
                'data_processada': uwb_data_processada.to_dict(),
                'posicao': {
                    'x': x,
                    'y': y,
                    'unidade': 'cm',
                    'algoritmo': 'trilateracao_minimos_quadrados',
                    'coordenadas_ancoras': {
                    'ancora_0': '(0, 0)', # Âncora 0 é sempre (0,0)
                    'ancora_1': f'({kx_relatorio}, 0)' if kx_relatorio else '(114, 0)',
                    'ancora_2': f'(0, {ky_relatorio})' if ky_relatorio else '(0, 114)'
                }

                },
                'relatorio_id': relatorio_ativo.relatorio_number,
                'relatorio_ativo': True,
                'debug_info': {
                    'array_original': range_data,
                    'array_processado': range_values,
                    'tipo_original': str(type(range_data)),
                    'kx_usado': kx_relatorio,
                    'ky_usado': ky_relatorio,
                    'num_ancoras_validas': len([v for v in range_values if v is not None and v > 0])
                }
            }
            
        except Exception as processing_error:
            logging.error(f"[DEBUG] Erro na trilateração do item: {processing_error}")
            db.session.commit()  # Commit apenas dos dados originais
            
            return {
                'success': True,
                'message': 'Dados UWB salvos (trilateração falhou)',
                'data_original': uwb_data.to_dict(),
                'processing_error': str(processing_error),
                'relatorio_id': relatorio_ativo.relatorio_number,
                'relatorio_ativo': True,
                'debug_info': {
                    'array_original': range_data,
                    'array_processado': range_values,
                    'tipo_original': str(type(range_data)),
                    'erro_trilateracao': str(processing_error)
                }
            }
        
    except Exception as e:
        logging.error(f"[DEBUG] Erro inesperado ao processar item: {e}")
        return {'error': f'Erro inesperado ao processar item: {str(e)}'}

@uwb_bp.route('/uwb/data', methods=['GET'])
def get_uwb_data():
    """Recuperar dados UWB originais"""
    try:
        logging.info("[DEBUG] Requisição GET para recuperar dados UWB")
        uwb_records = UWBData.query.order_by(UWBData.criado_em.desc()).limit(50).all()
        logging.info(f"[DEBUG] {len(uwb_records)} registros UWB encontrados")
        return jsonify([record.to_dict() for record in uwb_records])
    except Exception as e:
        logging.error(f"[DEBUG] Erro ao recuperar dados UWB: {e}")
        return jsonify({'error': f'Erro ao recuperar dados: {str(e)}'}), 500

@uwb_bp.route('/uwb/data/processed', methods=['GET'])
def get_processed_uwb_data():
    """Recuperar dados UWB processados (com coordenadas X,Y)"""
    try:
        logging.info("[DEBUG] Requisição GET para recuperar dados UWB processados")
        processed_records = UWBDataProcessada.query.order_by(UWBDataProcessada.criado_em.desc()).limit(50).all()
        logging.info(f"[DEBUG] {len(processed_records)} registros UWB processados encontrados")
        return jsonify([record.to_dict() for record in processed_records])
    except Exception as e:
        logging.error(f"[DEBUG] Erro ao recuperar dados processados: {e}")
        return jsonify({'error': f'Erro ao recuperar dados processados: {str(e)}'}), 500

@uwb_bp.route('/uwb/test', methods=['POST'])
def test_uwb_endpoint():
    """Endpoint de teste para validar diferentes formatos de array"""
    try:
        logging.info("[DEBUG] Endpoint de teste chamado")
        data = request.json
        
        if not data or 'range' not in data:
            return jsonify({'error': 'Campo range é obrigatório para teste'}), 400
        
        range_data = data['range']
        logging.info(f"[DEBUG] Testando conversão de array: {range_data} (tipo: {type(range_data)})")
        
        # Testar conversão
        range_values = validar_e_converter_array(range_data, "range")
        
        if range_values is None:
            return jsonify({
                'success': False,
                'message': 'Falha na conversão do array',
                'input': range_data,
                'input_type': str(type(range_data))
            }), 400
        
        return jsonify({
            'success': True,
            'message': 'Array convertido com sucesso',
            'input': range_data,
            'input_type': str(type(range_data)),
            'output': range_values,
            'output_length': len(range_values),
            'valid_values': len([v for v in range_values if v is not None and v > 0])
        }), 200
        
    except Exception as e:
        logging.error(f"[DEBUG] Erro no endpoint de teste: {e}")
        return jsonify({
            'error': f'Erro no teste: {str(e)}',
            'input': str(request.get_data())
        }), 500
