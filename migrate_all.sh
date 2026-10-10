#!/bin/bash

# Database migration execution script

# Generate database migration files
echo "Generating database migrations..."
python manage.py makemigrations

# Execute database migrations
echo "Executing database migrations..."
python manage.py migrate

echo "Database migrations completed!"