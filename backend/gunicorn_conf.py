# gunicorn_conf.py
import os

# allow the PORT environment variable to override the hard-coded port
bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"
workers = 1
timeout = 600
keepalive = 60