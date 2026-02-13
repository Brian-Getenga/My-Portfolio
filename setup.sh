#!/bin/bash

# Portfolio Setup Script
echo "========================================="
echo "Brian Getenga Portfolio - Quick Setup"
echo "========================================="
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | grep -Po '(?<=Python )(.+)')
echo "✓ Python version: $python_version"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
echo "✓ Virtual environment created"
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip
echo "✓ pip upgraded"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    
    # Generate secret key
    secret_key=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
    
    # Update secret key in .env
    sed -i "s/your-secret-key-here-change-in-production/$secret_key/" .env
    
    echo "✓ .env file created with generated SECRET_KEY"
    echo ""
    echo "⚠️  IMPORTANT: Please update the following in your .env file:"
    echo "   - EMAIL_HOST_USER"
    echo "   - EMAIL_HOST_PASSWORD"
    echo ""
else
    echo "✓ .env file already exists"
    echo ""
fi

# Create logs directory
mkdir -p logs
echo "✓ Logs directory created"
echo ""

# Run migrations
echo "Running database migrations..."
python manage.py makemigrations
python manage.py migrate
echo "✓ Migrations completed"
echo ""

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput
echo "✓ Static files collected"
echo ""

# Create superuser
echo "========================================="
echo "Create Admin Account"
echo "========================================="
echo ""
python manage.py createsuperuser
echo ""

echo "========================================="
echo "✓ Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Update email settings in .env file"
echo "2. Add your profile image and resume to media folder"
echo "3. Run: python manage.py runserver"
echo "4. Visit: http://127.0.0.1:8000"
echo "5. Admin panel: http://127.0.0.1:8000/admin"
echo ""
echo "For deployment instructions, see DEPLOYMENT.md"
echo ""
echo "Happy coding! 🚀"
echo ""
