#!/usr/bin/env bash
# exit on error
set -o errexit

# Install all your python packages
pip install -r requirements.txt

# Collect your CSS, JS, and image files for WhiteNoise
python manage.py collectstatic --no-input

# Run your database migrations on the Render PostgreSQL database
python manage.py migrate
