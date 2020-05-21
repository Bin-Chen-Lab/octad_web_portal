#!/usr/bin/env bash
export FLASK_ENV=development
export APP_CONFIG_FILE=$(pwd)/config/development.py
flask run -h localhost.localdomain -p 5000
# python manage.py runserver
