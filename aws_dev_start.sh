#!/usr/bin/env bash
export FLASK_ENV=development
export APP_CONFIG_FILE=$(pwd)/config/development.py
export FLASK_RUN_PORT=8090
flask run -h 0.0.0.0 -p 8090

# python manage.py runserver
