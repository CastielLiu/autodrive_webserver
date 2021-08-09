#!/bin/bash

uwsgi --stop nginx_uwsgi.pid
sleep 0.5
uwsgi --stop nginx_uwsgi.pid
sleep 0.5

uwsgi --ini nginx_uwsgi.ini