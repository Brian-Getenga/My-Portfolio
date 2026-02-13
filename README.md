# Brian Getenga - Modern Portfolio Website

A production-ready Django portfolio website with modern design, advanced features, and optimized performance.

## 🚀 Features

### Core Features
- ✅ Responsive Design with Tailwind CSS
- ✅ Dark/Light Mode Toggle
- ✅ Smooth Animations & Transitions
- ✅ Contact Form with Email Integration
- ✅ Project Showcase with Filtering
- ✅ Blog System with Rich Text Editor
- ✅ Newsletter Subscription
- ✅ Testimonials Section
- ✅ Skills & Experience Timeline
- ✅ SEO Optimized
- ✅ Performance Optimized (90+ Lighthouse Score)
- ✅ Admin Dashboard
- ✅ Analytics Integration
- ✅ Sitemap & RSS Feed
- ✅ File Compression & Caching
- ✅ Social Media Integration
- ✅ Multi-language Support Ready

### Advanced Features
- 📧 Working Email System (Contact Form + Newsletter)
- 🔒 Security Headers & CSRF Protection
- 📊 Admin Analytics Dashboard
- 🖼️ Image Optimization
- 📱 Progressive Web App (PWA) Ready
- 🚀 CDN Ready
- 📈 Google Analytics Integration
- 🔍 Advanced Search Functionality
- 💬 Comment System for Blog Posts
- 📥 Resume/CV Download
- 🎨 Customizable Themes
- 📊 Visitor Analytics
- 🔔 Real-time Notifications

## 📋 Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Git
- Virtual environment (recommended)

## 🛠️ Installation & Setup

### 1. Clone or Extract the Project

```bash
cd brian_portfolio_django
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the root directory:

```env
# Django Settings
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite by default, PostgreSQL for production)
DATABASE_URL=sqlite:///db.sqlite3

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com

# Security (Production)
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False

# Analytics (Optional)
GOOGLE_ANALYTICS_ID=UA-XXXXXXXXX-X

# AWS S3 (Optional - for media files)
USE_S3=False
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=
AWS_S3_REGION_NAME=us-east-1
```

### 5. Initialize Database

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser

```bash
python manage.py createsuperuser
```

Follow the prompts to create your admin account.

### 7. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 8. Load Initial Data (Optional)

```bash
python manage.py loaddata initial_data.json
```

### 9. Run Development Server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000` in your browser.

## 📧 Email Setup

### Gmail Setup (Recommended for Testing)

1. Go to your Google Account settings
2. Enable 2-Factor Authentication
3. Generate an App Password:
   - Go to Security → 2-Step Verification → App passwords
   - Generate a new app password for "Mail"
4. Use this password in your `.env` file for `EMAIL_HOST_PASSWORD`

### Production Email Options

- **SendGrid**: `EMAIL_HOST=smtp.sendgrid.net`
- **Mailgun**: Configure via their SMTP settings
- **AWS SES**: Best for production with AWS hosting

## 🚀 Production Deployment

### Prepare for Production

1. **Update .env file:**
```env
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

2. **Change SECRET_KEY:**
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

3. **Use PostgreSQL:**
```env
DATABASE_URL=postgresql://user:password@localhost:5432/portfolio_db
```

### Deploy to Heroku

```bash
# Install Heroku CLI
heroku login
heroku create your-portfolio-name

# Add PostgreSQL
heroku addons:create heroku-postgresql:mini

# Set environment variables
heroku config:set SECRET_KEY=your-secret-key
heroku config:set DEBUG=False
heroku config:set EMAIL_HOST_USER=your-email
heroku config:set EMAIL_HOST_PASSWORD=your-password

# Deploy
git push heroku main
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
```

### Deploy to DigitalOcean/AWS/VPS

Use the included `deployment_guide.md` for detailed instructions.

## 📁 Project Structure

```
brian_portfolio_django/
├── portfolio/              # Main Django project
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── core/                   # Main application
│   ├── models.py          # Database models
│   ├── views.py           # View logic
│   ├── forms.py           # Form definitions
│   ├── urls.py            # URL routing
│   ├── admin.py           # Admin configuration
│   └── templates/         # HTML templates
├── static/                 # Static files
│   ├── css/               # Stylesheets
│   ├── js/                # JavaScript files
│   └── images/            # Images
├── media/                  # User uploads
├── templates/              # Global templates
│   └── base.html
├── requirements.txt        # Python dependencies
├── manage.py              # Django CLI
├── .env                   # Environment variables
├── .gitignore
└── README.md
```

## 🎨 Customization

### Change Colors

Edit `static/css/custom.css` or update Tailwind config in `tailwind.config.js`.

### Update Content

1. Login to admin panel: `http://localhost:8000/admin`
2. Update:
   - Projects
   - Blog Posts
   - Skills
   - Experience
   - Testimonials
   - About section

### Add New Sections

1. Update `core/models.py` to add new models
2. Create templates in `core/templates/`
3. Add views in `core/views.py`
4. Update URLs in `core/urls.py`

## 🧪 Testing

```bash
# Run tests
python manage.py test

# Check code coverage
coverage run --source='.' manage.py test
coverage report
```

## 📊 Performance Optimization

- ✅ Static file compression enabled
- ✅ Image optimization with Pillow
- ✅ Browser caching configured
- ✅ Database query optimization
- ✅ Lazy loading for images
- ✅ Minified CSS/JS in production
- ✅ CDN integration ready

## 🔒 Security Features

- CSRF Protection
- XSS Prevention
- SQL Injection Protection
- Secure Password Hashing
- HTTPS Redirect (Production)
- Security Headers
- Rate Limiting (via middleware)

## 📝 Admin Panel Features

Access at: `http://localhost:8000/admin`

- Dashboard with analytics
- Manage projects, blog posts, skills
- View contact form submissions
- Newsletter subscribers management
- Site settings configuration
- User management

## 🐛 Troubleshooting

### Static Files Not Loading

```bash
python manage.py collectstatic --clear --noinput
```

### Database Issues

```bash
python manage.py flush
python manage.py migrate --run-syncdb
```

### Email Not Sending

- Check `.env` configuration
- Verify Gmail app password
- Check spam folder
- Enable "Less secure app access" (if not using app password)

## 📚 Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Deployment Guide](./deployment_guide.md)
- [API Documentation](./api_docs.md)

## 🤝 Support

For issues or questions:
- Email: briangetenga3@gmail.com
- GitHub: https://github.com/Brian-Getenga

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Credits

Developed by Brian Getenga
- Portfolio: https://briangetenga.com
- LinkedIn: https://www.linkedin.com/in/brian-getenga-7678b3251/
- GitHub: https://github.com/Brian-Getenga

---

**Version:** 1.0.0  
**Last Updated:** February 2026  
**Status:** Production Ready ✅
