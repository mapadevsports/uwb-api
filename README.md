# API UWB para ESP32

Esta é uma API Flask que recebe dados de distância UWB de dispositivos ESP32 e os armazena em um banco de dados PostgreSQL.

## Funcionalidades

- Recebe dados UWB via HTTP POST
- Armazena dados no PostgreSQL (Render) ou SQLite (desenvolvimento local)
- Suporte a CORS para requisições do ESP32
- Endpoints para consulta de dados

## Endpoints da API

### POST /api/uwb/data
Recebe dados UWB do ESP32.

**Formato esperado:**
```json
{
    "id": "4",
    "range": [6, 59, 126, 0, 0, 0, 0, 0]
}
```

**Resposta de sucesso:**
```json
{
    "success": true,
    "message": "Dados UWB salvos com sucesso",
    "data": {
        "id": 1,
        "tag_number": "4",
        "da0": 6.0,
        "da1": 59.0,
        "da2": 126.0,
        "da3": 0.0,
        "da4": 0.0,
        "da5": 0.0,
        "da6": 0.0,
        "da7": 0.0,
        "criado_em": "2025-06-28T04:57:08.306308"
    }
}
```

### GET /api/uwb/data
Retorna os últimos 50 registros de dados UWB.

### GET /api/uwb/data/{tag_number}
Retorna os últimos 50 registros de uma tag específica.

### GET /api/uwb/health
Verifica se a API está funcionando.

## Deploy no Render

### Pré-requisitos
1. Conta no Render (https://render.com)
2. Banco de dados PostgreSQL já criado no Render
3. Código da API em um repositório Git

### Passos para Deploy

1. **Criar Web Service no Render:**
   - Acesse o dashboard do Render
   - Clique em "New +" → "Web Service"
   - Conecte seu repositório Git

2. **Configurações do Web Service:**
   - **Name:** `uwb-api` (ou nome de sua escolha)
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `./start.sh`

3. **Variáveis de Ambiente:**
   - O Render automaticamente fornecerá a variável `DATABASE_URL` se você conectar o banco PostgreSQL
   - Certifique-se de que o banco PostgreSQL está conectado ao Web Service

4. **Conectar Banco de Dados:**
   - No dashboard do Web Service, vá para "Environment"
   - Adicione o banco PostgreSQL existente
   - O Render automaticamente criará a variável `DATABASE_URL`

5. **Deploy:**
   - Clique em "Create Web Service"
   - O Render fará o build e deploy automaticamente

### Estrutura do Banco de Dados

A API criará automaticamente a tabela `distancias_uwb` com a seguinte estrutura:

```sql
CREATE TABLE distancias_uwb (
    id SERIAL PRIMARY KEY,
    tag_number VARCHAR(50) NOT NULL,
    da0 DOUBLE PRECISION,
    da1 DOUBLE PRECISION,
    da2 DOUBLE PRECISION,
    da3 DOUBLE PRECISION,
    da4 DOUBLE PRECISION,
    da5 DOUBLE PRECISION,
    da6 DOUBLE PRECISION,
    da7 DOUBLE PRECISION,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Desenvolvimento Local

1. **Instalar dependências:**
   ```bash
   cd uwb-api
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Executar localmente:**
   ```bash
   python src/main.py
   ```

3. **Testar API:**
   ```bash
   # Health check
   curl http://localhost:5000/api/uwb/health
   
   # Enviar dados UWB
   curl -X POST http://localhost:5000/api/uwb/data \
        -H "Content-Type: application/json" \
        -d '{"id":"4","range":[6,59,126,0,0,0,0,0]}'
   ```

## Configuração do ESP32

Após o deploy, você receberá uma URL do Render (ex: `https://uwb-api-xyz.onrender.com`).

Use esta URL no código do ESP32 para enviar dados:
```cpp
const char* API_URL = "https://uwb-api-xyz.onrender.com/api/uwb/data";
```

## Monitoramento

- Logs estão disponíveis no dashboard do Render
- Use o endpoint `/api/uwb/health` para verificar se a API está funcionando
- Use o endpoint `/api/uwb/data` para verificar se os dados estão sendo salvos

