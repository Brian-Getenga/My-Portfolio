# Production Deployment Guide

This guide covers deploying your Django portfolio to various hosting platforms.

## Table of Contents
1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Heroku Deployment](#heroku-deployment)
3. [DigitalOcean Deployment](#digitalocean-deployment)
4. [AWS Deployment](#aws-deployment)
5. [Domain Setup](#domain-setup)
6. [SSL Certificate](#ssl-certificate)

## Pre-Deployment Checklist

Before deploying, ensure you've completed these steps:

### 1. Update Settings for Production

Create a `.env` file with production values:
```env
DEBUG=False
SECRET_KEY=your-new-secret-key-generate-a-strong-one
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://user:password@host:port/database
EMAIL_HOST_USER=your-production-email
EMAIL_HOST_PASSWORD=your-production-password
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### 2. Generate New Secret Key

```python
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### 3. Test Locally with Production Settings

```bash
DEBUG=False python manage.py runserver
```

### 4. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 5. Run Migrations

```bash
python manage.py migrate
```

## Heroku Deployment

### Step 1: Install Heroku CLI

Download from: https://devcenter.heroku.com/articles/heroku-cli

### Step 2: Login to Heroku

```bash
heroku login
```

### Step 3: Create Heroku App

```bash
heroku create your-portfolio-name
```

### Step 4: Add PostgreSQL Database

```bash
heroku addons:create heroku-postgresql:mini
```

### Step 5: Set Environment Variables

```bash
heroku config:set SECRET_KEY='your-secret-key'
heroku config:set DEBUG=False
heroku config:set ALLOWED_HOSTS='your-app-name.herokuapp.com'
heroku config:set EMAIL_HOST_USER='your-email'
heroku config:set EMAIL_HOST_PASSWORD='your-password'
```

### Step 6: Deploy

```bash
git init
git add .
git commit -m "Initial commit"
heroku git:remote -a your-portfolio-name
git push heroku main
```

### Step 7: Run Migrations

```bash
heroku run python manage.py migrate
```

### Step 8: Create Superuser

```bash
heroku run python manage.py createsuperuser
```

### Step 9: Access Your App

```bash
heroku open
```

## DigitalOcean Deployment

### Prerequisites
- DigitalOcean account
- SSH key set up

### Step 1: Create Droplet

1. Go to DigitalOcean Dashboard
2. Create → Droplets
3. Choose Ubuntu 22.04 LTS
4. Select plan (minimum $6/month recommended)
5. Add SSH key
6. Create Droplet

### Step 2: Connect to Server

```bash
ssh root@your-droplet-ip
```

### Step 3: Update System

```bash
apt update && apt upgrade -y
```

### Step 4: Install Dependencies

```bash
# Install Python and pip
apt install python3 python3-pip python3-venv postgresql postgresql-contrib nginx -y

# Install supervisor for process management
apt install supervisor -y
```

### Step 5: Create Database

```bash
sudo -u postgres psql

CREATE DATABASE portfolio_db;
CREATE USER portfolio_user WITH PASSWORD 'your_password';
ALTER ROLE portfolio_user SET client_encoding TO 'utf8';
ALTER ROLE portfolio_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE portfolio_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE portfolio_db TO portfolio_user;
\q
```

### Step 6: Set Up Application

```bash
# Create app directory
mkdir -p /var/www/portfolio
cd /var/www/portfolio

# Clone or upload your code
git clone your-repository-url .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
nano .env
# Add your production environment variables
```

### Step 7: Configure Gunicorn

Create supervisor config:
```bash
nano /etc/supervisor/conf.d/portfolio.conf
```

Add:
```ini
[program:portfolio]
directory=/var/www/portfolio
command=/var/www/portfolio/venv/bin/gunicorn portfolio.wsgi:application --bind 127.0.0.1:8000
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/portfolio.err.log
stdout_logfile=/var/log/portfolio.out.log
```

Update supervisor:
```bash
supervisorctl reread
supervisorctl update
supervisorctl start portfolio
```

### Step 8: Configure Nginx

```bash
nano /etc/nginx/sites-available/portfolio
```

Add:
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /var/www/portfolio;
    }

    location /media/ {
        root /var/www/portfolio;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site:
```bash
ln -s /etc/nginx/sites-available/portfolio /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

### Step 9: Set Up SSL with Certbot

```bash
apt install certbot python3-certbot-nginx -y
certbot --nginx -d your-domain.com -d www.your-domain.com
```

## AWS Deployment (EC2 + RDS)

### Step 1: Launch EC2 Instance

1. Go to AWS Console → EC2
2. Launch Instance
3. Choose Ubuntu Server 22.04 LTS
4. Select t2.micro or larger
5. Configure security groups (ports 22, 80, 443)
6. Launch and download key pair

### Step 2: Set Up RDS Database

1. Go to RDS → Create Database
2. Choose PostgreSQL
3. Configure settings
4. Create database

### Step 3: Connect and Deploy

Follow similar steps to DigitalOcean deployment, but use RDS endpoint for database connection.

### Step 4: Configure S3 for Media Files

```python
# Add to settings.py
if os.environ.get('USE_S3') == 'True':
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
```

## Domain Setup

### 1. Point Domain to Server

Add A record in your DNS settings:
```
Type: A
Name: @
Value: your-server-ip
TTL: 3600

Type: A
Name: www
Value: your-server-ip
TTL: 3600
```

### 2. Wait for DNS Propagation

Can take up to 48 hours, typically 1-4 hours.

## SSL Certificate

### Using Let's Encrypt (Free)

```bash
certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### Auto-Renewal

Certbot automatically sets up renewal. Test it:
```bash
certbot renew --dry-run
```

## Post-Deployment

### 1. Test Everything

- Homepage loads correctly
- Admin panel accessible
- Contact form sends emails
- Projects display properly
- Blog posts load
- Static files serve correctly

### 2. Monitor Logs

```bash
# Application logs
tail -f /var/log/portfolio.err.log
tail -f /var/log/portfolio.out.log

# Nginx logs
tail -f /var/nginx/access.log
tail -f /var/nginx/error.log
```

### 3. Set Up Monitoring

Consider using:
- Sentry for error tracking
- Google Analytics for visitor tracking
- UptimeRobot for uptime monitoring

### 4. Regular Backups

Set up daily database backups:
```bash
pg_dump portfolio_db > backup_$(date +%Y%m%d).sql
```

## Troubleshooting

### Static Files Not Loading

```bash
python manage.py collectstatic --clear --noinput
chmod -R 755 /var/www/portfolio/staticfiles
```

### Database Connection Issues

Check DATABASE_URL format:
```
postgresql://user:password@host:5432/database
```

### Permission Errors

```bash
chown -R www-data:www-data /var/www/portfolio
```

### Email Not Sending

1. Check SMTP settings in .env
2. Verify port 587 is open
3. Test with Python:
```python
python manage.py shell
from django.core.mail import send_mail
send_mail('Test', 'Body', 'from@example.com', ['to@example.com'])
```

## Maintenance

### Updating the Application

```bash
cd /var/www/portfolio
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
supervisorctl restart portfolio
```

### Database Backup

```bash
pg_dump -U portfolio_user portfolio_db > backup.sql
```

### Database Restore

```bash
psql -U portfolio_user portfolio_db < backup.sql
```

## Support

For issues or questions:
- Email: briangetenga3@gmail.com
- GitHub: https://github.com/Brian-Getenga

---

**Good luck with your deployment! 🚀**
