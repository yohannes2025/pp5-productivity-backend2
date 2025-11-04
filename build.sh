#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install project dependencies from requirements.txt
echo "Installing project dependencies..."
pip install -r requirements.txt

# Run collectstatic to gather all static files
echo "Collecting static files..."
python manage.py collectstatic --no-input

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

python manage.py createsuperuser --no-input

echo "Build process completed successfully!"