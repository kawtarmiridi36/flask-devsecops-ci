# Gunicorn configuration file
import multiprocessing
import os

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = 2
worker_class = "sync"
worker_connections = 1000
timeout = 300  # Increased from 120 to 300 seconds
keepalive = 5
max_requests = 1000
max_requests_jitter = 50

# Logging - CRITICAL: Log to stdout only, no files!
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stdout
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "flask-devsecops"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = "appuser"
group = "appuser"
tmp_upload_dir = None

# SSL
# keyfile = None
# certfile = None

# Debugging
reload = False
spew = False
check_config = False

# Server hooks
def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def pre_fork(server, worker):
    pass

def pre_exec(server):
    server.log.info("Forked child, re-executing.")

def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def worker_abort(worker):
    worker.log.info("worker received SIGABRT signal")
