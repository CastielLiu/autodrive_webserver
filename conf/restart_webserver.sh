#!/bin/bash

# 重启nginx_uwsgi
uwsgi --stop nginx_uwsgi.pid
sleep 0.5
uwsgi --stop nginx_uwsgi.pid
sleep 0.5
uwsgi --ini nginx_uwsgi.ini

# 重启daphne
supervisorctl restart daphne