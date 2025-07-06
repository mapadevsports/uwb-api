# Configuração do Gunicorn para produção no Render
import os

# Bind to the port provided by Render
bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"

# Worker configuration
workers = 2
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "uwb-api"

# Server mechanics
preload_app = True
max_requests = 1000
max_requests_jitter = 50

