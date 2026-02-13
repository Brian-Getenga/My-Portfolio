# 🚀 QUICK START GUIDE - Brian Getenga Portfolio

## ⚡ Super Fast Setup (5 Minutes)

### Option 1: Automatic Setup (Recommended)

#### For Linux/Mac:
```bash
cd brian_portfolio_django
chmod +x setup.sh
./setup.sh
```

#### For Windows:
```bash
cd brian_portfolio_django
setup.bat
```

### Option 2: Manual Setup

```bash
# 1. Navigate to project
cd brian_portfolio_django

# 2. Create virtual environment
python -m venv venv

# 3. Activate it
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Copy environment file
cp .env.example .env

# 6. Generate secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
# Copy output and update SECRET_KEY in .env

# 7. Run migrations
python manage.py makemigrations
python manage.py migrate

# 8. Create admin user
python manage.py createsuperuser

# 9. Collect static files
python manage.py collectstatic --noinput

# 10. Run server
python manage.py runserver
```

## 🎯 Access Your Portfolio

- **Homepage**: http://127.0.0.1:8000
- **Admin Panel**: http://127.0.0.1:8000/admin

## 📧 Email Configuration

### Gmail Setup (Recommended for Development)

1. Enable 2-Factor Authentication on your Google Account
2. Generate App Password:
   - Go to: https://myaccount.google.com/security
   - Navigate to: Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
3. Update `.env`:
```env
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-digit-app-password
```

### Testing Email

```python
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'It works!', 'from@example.com', ['to@example.com'])
```

## 🎨 Customization

### 1. Update Site Settings

Login to admin panel and go to: **Site Settings**

Update:
- Site name and description
- Profile image (upload your photo)
- Resume file (upload your CV)
- Contact information
- Social media links
- Statistics (years of experience, projects, clients)

### 2. Add Your Content

#### Projects
Go to **Projects** in admin and click "Add Project"
- Upload project images
- Add description and technologies
- Link to GitHub and live demo

#### Blog Posts
Go to **Blog Posts** and create articles
- Rich text editor included
- Add tags for categorization
- Set as featured for homepage

#### Skills
Add your skills in the **Skills** section
- Choose icon from FontAwesome
- Set proficiency level
- Categorize (Frontend, Backend, etc.)

#### Experience
Document your work history in **Experience**
- Add achievements per role
- Mark current positions

#### Testimonials
Add client testimonials in **Testimonials**
- Upload client photos
- Set featured testimonials for homepage

### 3. Customize Design

All styling uses Tailwind CSS (no custom CSS files needed!)

To change colors, edit `templates/base.html`:
```javascript
tailwind.config = {
    theme: {
        extend: {
            colors: {
                primary: {
                    // Change these values
                    500: '#3b82f6',
                    600: '#2563eb',
                }
            }
        }
    }
}
```

## 🌐 Production Deployment

### Quick Deploy to Heroku

```bash
# Install Heroku CLI
# https://devcenter.heroku.com/articles/heroku-cli

# Login
heroku login

# Create app
heroku create your-portfolio-name

# Add database
heroku addons:create heroku-postgresql:mini

# Set environment variables
heroku config:set SECRET_KEY='your-secret-key'
heroku config:set DEBUG=False
heroku config:set EMAIL_HOST_USER='your-email'
heroku config:set EMAIL_HOST_PASSWORD='your-password'

# Deploy
git init
git add .
git commit -m "Initial commit"
git push heroku main

# Run migrations
heroku run python manage.py migrate

# Create admin
heroku run python manage.py createsuperuser

# Open app
heroku open
```

## ✅ Features Checklist

- ✅ Responsive Design (Mobile, Tablet, Desktop)
- ✅ Dark/Light Mode Toggle
- ✅ Smooth Animations (AOS Library)
- ✅ Contact Form with Email Notifications
- ✅ Newsletter Subscription
- ✅ Project Showcase with Filtering
- ✅ Blog System with Rich Text Editor
- ✅ Skills & Experience Timeline
- ✅ Client Testimonials
- ✅ SEO Optimized (Meta tags, Sitemaps)
- ✅ Admin Dashboard for Content Management
- ✅ Image Upload & Management
- ✅ Tag System for Projects & Blog
- ✅ Search Functionality
- ✅ Social Media Integration
- ✅ Resume/CV Download
- ✅ Analytics Ready (Google Analytics)
- ✅ Performance Optimized
- ✅ Security Headers
- ✅ CSRF Protection
- ✅ SSL Ready
- ✅ Database Migrations
- ✅ Static File Management
- ✅ Email Templates
- ✅ Error Logging

## 🔧 Common Issues & Solutions

### Issue: "No module named 'django'"
**Solution**: Activate virtual environment first
```bash
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```

### Issue: "SMTP Authentication Error"
**Solution**: 
1. Use Gmail App Password, not regular password
2. Enable "Less secure app access" if not using 2FA
3. Check EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in .env

### Issue: "Static files not found"
**Solution**:
```bash
python manage.py collectstatic --clear --noinput
```

### Issue: "Database is locked"
**Solution**: Close all other Django processes
```bash
pkill -f runserver
python manage.py runserver
```

## 📚 Additional Resources

- **Full Documentation**: See README.md
- **Deployment Guide**: See DEPLOYMENT.md
- **Django Docs**: https://docs.djangoproject.com/
- **Tailwind CSS**: https://tailwindcss.com/docs

## 🆘 Support

Need help? Contact:
- Email: briangetenga3@gmail.com
- LinkedIn: https://www.linkedin.com/in/brian-getenga-7678b3251/
- GitHub: https://github.com/Brian-Getenga

## 🎉 You're All Set!

Your modern, production-ready portfolio is now running!

Next steps:
1. ✅ Customize content in admin panel
2. ✅ Add your projects and blog posts
3. ✅ Test contact form and newsletter
4. ✅ Deploy to production (see DEPLOYMENT.md)
5. ✅ Share with the world! 🚀

---

**Built with ❤️ by Brian Getenga**
**Django + Tailwind CSS + Modern Web Technologies**
