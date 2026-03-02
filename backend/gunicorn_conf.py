# gunicorn_conf.py
bind = "0.0.0.0:10000"
workers = 1
timeout = 600
keepalive = 60