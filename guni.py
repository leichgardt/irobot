# server
bind = '0.0.0.0:8000'
worker_class = 'uviworker.IrobotUviWorker'
workers = 4
threads = 2
user = 'www-data'  # remove on development
group = 'www-data'  # remove on development
max_requests = 200
max_requests_jitter = 50
timeout = 60
keepalive = 5
preload_app = False

# security
limit_request_line = 8190
limit_request_field_size = 32768

# logging
syslog = True
syslog_prefix = 'irobot_web'
accesslog = '/var/log/irobot-web.access.log'
errorlog = '/var/log/irobot-web.errors.log'
disable_redirect_access_to_syslog = False
