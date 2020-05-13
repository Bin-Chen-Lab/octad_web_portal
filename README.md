## Run Applicataion

service mysql restart

sudo systemctl restart nginx

export APP_CONFIG_FILE=/var/www/html/octad_web_portal/config/production.py

nohup uwsgi --socket 127.0.0.1:5002 --plugin /usr/lib/uwsgi/plugins/python27_plugin.so --module app --callab app --enable-threads --master --processes 16 --close-on-exec &
