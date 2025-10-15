# Gunicorn configuration file for Overtime Management Application
import os

# Server socket
bind = "0.0.0.0:5001"

# Worker processes
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = "/home/berant/overtime/logs/gunicorn_access.log"
errorlog = "/home/berant/overtime/logs/gunicorn_error.log"
loglevel = "info"

# Process naming
proc_name = "overtime-app"

# Server mechanics
daemon = False
pidfile = None
user = None
group = None
tmp_upload_dir = None
