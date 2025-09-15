# Gunicorn configuration file for College Portal production deployment

import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Timeout settings
timeout = 30
keepalive = 2
graceful_timeout = 30

# Logging
accesslog = "/var/log/college_portal/access.log"
errorlog = "/var/log/college_portal/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "college_portal"

# User and group
user = "www-data"
group = "www-data"

# Temporary directory
tmp_upload_dir = "/tmp"

# SSL (uncomment if using HTTPS)
# keyfile = "/etc/ssl/private/college_portal.key"
# certfile = "/etc/ssl/certs/college_portal.crt"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Performance tuning
worker_tmp_dir = "/dev/shm"
forwarded_allow_ips = "*"

# Environment variables
raw_env = [
    "DJANGO_SETTINGS_MODULE=college_portal.settings",
    "PYTHONPATH=/var/www/college_portal",
]

# Pre-fork application loading
def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def pre_exec(server):
    server.log.info("Forked child, re-executing.")

def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_worker_init(worker):
    worker.log.info("Worker initialized (pid: %s)", worker.pid)

def worker_abort(worker):
    worker.log.info("Worker aborted (pid: %s)", worker.pid)

def post_worker_exit(server, worker):
    server.log.info("Worker exited (pid: %s)", worker.pid)

# Health check endpoint
def health_check(environ, start_response):
    status = '200 OK'
    response_headers = [('Content-type', 'text/plain')]
    start_response(status, response_headers)
    return [b'OK']

# Custom middleware for health checks
def health_check_middleware(environ, start_response):
    if environ.get('PATH_INFO') == '/health/':
        return health_check(environ, start_response)
    return None












