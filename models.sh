#!/bin/sh
python3 manage.py makemigrations user
python3 manage.py makemigrations asset
python3 manage.py makemigrations department
python3 manage.py makemigrations pending
python3 manage.py migrate