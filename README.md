# OCTAD web portal

## Run Application

```bash
# mysql restart not usually necessary
service mysql restart

export FLASK_ENV=production
export FLASK_RUN_PORT=80
export APP_ROOT=/var/www/html/octad_web_portal
export APP_CONFIG_FILE=$APP_ROOT/config/production.py


cd $APP_ROOT
nohup uwsgi --socket 127.0.0.1:5002 --plugin /usr/lib/uwsgi/plugins/python27_plugin.so --module app --callab app --enable-threads --master --processes 16 --close-on-exec --pidfile ./octad.pid &
sudo systemctl restart nginx
```

### To restart the server after updating the code

```bash
export APP_ROOT=/var/www/html/octad_web_portal
uwsgi --restart $APP_ROOT/octad.pid
```
