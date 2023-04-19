#!/bin/sh
python3 manage.py makemigrations user
python3 manage.py makemigrations asset
python3 manage.py makemigrations department
python3 manage.py makemigrations pending
python3 manage.py makemigrations logs
python3 manage.py migrate

# TODO Start: [Student] Run with uWSGI instead
# python3 manage.py runserver 80
uwsgi --module=Aplus.wsgi:application \
     --env DJANGO_SETTINGS_MODULE=Aplus.settings \
     --master \
     --http=0.0.0.0:80 \
     --processes=5 \
     --harakiri=20 \
     --max-requests=5000 \
     --vacuum
# TODO End: [Student] Run with uWSGI instead