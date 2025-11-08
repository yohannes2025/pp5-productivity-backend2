#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status.
set -o errexit

# 1. Install project dependencies from requirements.txt
echo "Installing project dependencies..."
pip install -r requirements.txt

# 2. Run Django commands using the virtual environment's Python
echo "Collecting static files..."
python manage.py collectstatic --no-input # Collect static files
python manage.py makemigrations # Only needed if models changed locally
python manage.py migrate # Apply database migrations

# 3. Create Superuser (Crucial for live admin access)
# The || true ensures the script doesn't crash if the user already exists
echo "Creating superuser (skips if exists)..."
python manage.py createsuperuser --no-input || true

echo "Build process completed successfully!"