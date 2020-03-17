../scripts/wait.sh db:5432 -t 60
python manage.py migrate --noinput
# python manage.py runserver 0.0.0.0:8000
uwsgi ../uwsgi.ini