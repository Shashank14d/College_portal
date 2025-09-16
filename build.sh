#!/usr/bin/env bash
# exit on error
set -o errexit

cd "College Project"
pip install -r requirements.txt

python manage.py collectstatic --no-input