# Instruções Completas de Deploy - Sistema UWB

## Resumo da Solução

Criamos uma solução completa que substitui a conexão direta do ESP32 ao PostgreSQL por uma arquitetura mais segura e robusta:

```
ESP32 → HTTP/HTTPS → API Flask → PostgreSQL (Render)
```

### Vantagens desta abordagem:
- ✅ **Segurança**: Credenciais do banco não ficam expostas no ESP32
- ✅ **Confiabilidade**: Conexão HTTP é mais estável que PostgreSQL direto
- ✅ **Flexibilidade**: API pode validar, processar e transformar dados
- ✅ **Monitoramento**: Logs centralizados na API
- ✅ **Escalabilidade**: Múltiplos ESP32 podem usar a mesma API

## Passo 1: Deploy da API no Render

### 1.1 Preparar Repositório Git
1. Crie um repositório no GitHub (ou GitLab/Bitbucket)
2. Faça upload de todos os arquivos da pasta `uwb-api/`
3. Certifique-se de que os seguintes arquivos estão incluídos:
   - `src/` (pasta com código da API)
   - `requirements.txt`
   - `gunicorn.conf.py`
   - `start.sh`
   - `README.md`

### 1.2 Criar Web Service no Render
1. Acesse https://render.com e faça login
2. Clique em **"New +"** → **"Web Service"**
3. Conecte seu repositório Git
4. Configure o serviço:
   - **Name**: `uwb-api` (ou nome de sua escolha)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `./start.sh`

### 1.3 Conectar Banco de Dados
1. No dashboard do Web Service, vá para **"Environment"**
2. Clique em **"Add Environment Variable"**
3. **IMPORTANTE**: Conecte seu banco PostgreSQL existente:
   - Vá para a seção "Environment Variables"
   - Clique em "Add from Database"
   - Selecione seu banco PostgreSQL existente
   - Isso criará automaticamente a variável `DATABASE_URL`

### 1.4 Deploy
1. Clique em **"Create Web Service"**
2. Aguarde o build e deploy (pode levar alguns minutos)
3. Anote a URL gerada (ex: `https://uwb-api-xyz.onrender.com`)

### 1.5 Testar API
Após o deploy, teste se a API está funcionando:

```bash
# Teste de saúde
curl https://sua-api-uwb.onrender.com/api/uwb/health

# Teste de envio de dados
curl -X POST https://sua-api-uwb.onrender.com/api/uwb/data \
     -H "Content-Type: application/json" \
     -d '{"id":"4","range":[6,59,126,0,0,0,0,0]}'
```

## Passo 2: Configurar ESP32

### 2.1 Instalar Bibliotecas Necessárias
No Arduino IDE, instale as seguintes bibliotecas:
- **ArduinoJson** (by Benoit Blanchon)
- **Adafruit GFX Library**
- **Adafruit SSD1306**

### 2.2 Configurar Código Arduino
1. Abra o arquivo `esp32_uwb_http.ino` no Arduino IDE
2. **IMPORTANTE**: Modifique as seguintes linhas:

```cpp
// Configurações Wi-Fi
const char* ssid = "SEU_SSID_WIFI"; // ← Substitua pelo nome da sua rede Wi-Fi
const char* password = "SUA_SENHA_WIFI"; // ← Substitua pela senha da sua rede Wi-Fi

// Configurações da API
const char* API_URL = "https://sua-api-uwb.onrender.com/api/uwb/data"; // ← Substitua pela URL da sua API
const char* HEALTH_URL = "https://sua-api-uwb.onrender.com/api/uwb/health"; // ← Substitua pela URL da sua API
```

### 2.3 Carregar Código no ESP32
1. Conecte o ESP32 ao computador
2. Selecione a placa e porta corretas no Arduino IDE
3. Carregue o código

### 2.4 Monitorar Funcionamento
1. Abra o Monitor Serial (115200 baud)
2. Verifique se o ESP32:
   - Conecta ao Wi-Fi
   - Testa a conexão com a API
   - Envia dados UWB quando recebidos

## Passo 3: Verificar Dados no Banco

### 3.1 Via pgAdmin
1. Conecte-se ao seu banco PostgreSQL no pgAdmin
2. Execute a query:
```sql
SELECT * FROM distancias_uwb ORDER BY criado_em DESC LIMIT 10;
```

### 3.2 Via API
Acesse no navegador:
```
https://sua-api-uwb.onrender.com/api/uwb/data
```

## Estrutura dos Dados

### Formato enviado pelo ESP32:
```json
{
    "id": "4",
    "range": [6, 59, 126, 0, 0, 0, 0, 0]
}
```

### Estrutura na tabela PostgreSQL:
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | SERIAL | ID único do registro |
| tag_number | VARCHAR(50) | Número da tag UWB |
| da0-da7 | DOUBLE PRECISION | Distâncias das 8 âncoras |
| criado_em | TIMESTAMP | Data/hora de criação |

## Troubleshooting

### Problema: ESP32 não conecta à API
**Soluções:**
1. Verifique se a URL da API está correta
2. Teste a API no navegador
3. Verifique se o Wi-Fi está funcionando
4. Verifique se o Render não está em "sleep mode"

### Problema: API retorna erro 500
**Soluções:**
1. Verifique os logs no dashboard do Render
2. Certifique-se de que o banco PostgreSQL está conectado
3. Verifique se a variável `DATABASE_URL` está configurada

### Problema: Dados não aparecem no banco
**Soluções:**
1. Verifique se a tabela `distancias_uwb` foi criada
2. Teste o endpoint da API diretamente
3. Verifique os logs da API no Render

### Problema: Render em "Sleep Mode"
O Render pode colocar serviços gratuitos em sleep após inatividade.
**Soluções:**
1. Upgrade para plano pago
2. Configure um "ping" periódico para manter a API ativa
3. Aceite o delay inicial quando a API "acorda"

## Monitoramento Contínuo

### Logs da API
- Acesse o dashboard do Render
- Vá para "Logs" para ver atividade em tempo real

### Status da API
- Use o endpoint `/api/uwb/health` para verificar se está funcionando
- Configure alertas se necessário

### Dados Recebidos
- Use o endpoint `/api/uwb/data` para ver os últimos dados
- Configure dashboards se necessário

## Próximos Passos (Opcionais)

1. **Dashboard Web**: Criar interface web para visualizar dados
2. **Alertas**: Configurar notificações para falhas
3. **Backup**: Configurar backup automático dos dados
4. **Analytics**: Adicionar análise dos dados de distância
5. **Múltiplos ESP32**: Configurar vários dispositivos

## Suporte

Se encontrar problemas:
1. Verifique os logs no Render
2. Teste os endpoints da API manualmente
3. Verifique o Monitor Serial do ESP32
4. Consulte a documentação do Render: https://render.com/docs

