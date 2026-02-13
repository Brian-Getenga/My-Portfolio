# 📸 Image Setup Guide

## Required Images for Your Portfolio

### 1. Profile Image
- **Location**: Upload via Admin → Site Settings
- **Recommended Size**: 400x400px (square)
- **Format**: JPG or PNG
- **Purpose**: Hero section, about section, footer
- **Tips**: Professional headshot with good lighting

### 2. Project Images
- **Location**: Upload via Admin → Projects
- **Recommended Size**: 1200x800px (3:2 ratio)
- **Format**: JPG or PNG (WebP for best performance)
- **Purpose**: Project cards and detail pages
- **Quantity**: At least 3-6 featured projects

**Naming Convention**:
```
project-name-main.jpg
project-name-screenshot-1.jpg
project-name-screenshot-2.jpg
```

### 3. Blog Post Images
- **Location**: Upload via Admin → Blog Posts
- **Recommended Size**: 1200x630px (OG image size)
- **Format**: JPG or PNG
- **Purpose**: Blog listing and article headers
- **Tips**: Use relevant, high-quality images

### 4. Testimonial Images
- **Location**: Upload via Admin → Testimonials
- **Recommended Size**: 200x200px (square)
- **Format**: JPG or PNG
- **Purpose**: Client testimonial cards
- **Tips**: Professional headshots of clients/colleagues

### 5. Resume/CV File
- **Location**: Upload via Admin → Site Settings
- **Format**: PDF
- **Purpose**: Downloadable CV for visitors
- **Naming**: Brian_Getenga_Resume.pdf

## Using Placeholder Images (Development)

### Free Image Sources:
1. **Unsplash** (https://unsplash.com)
   - High-quality, free stock photos
   - Perfect for project screenshots

2. **Lorem Picsum** (https://picsum.photos)
   - Random placeholder images
   - Usage: `https://picsum.photos/1200/800`

3. **UI Faces** (https://uifaces.co)
   - Avatar placeholders
   - For testimonials

4. **Pexels** (https://pexels.com)
   - Free stock photos
   - Great for backgrounds

## Image Optimization

### Before Uploading:
1. **Resize images** to recommended dimensions
2. **Compress** using:
   - TinyPNG (https://tinypng.com)
   - Squoosh (https://squoosh.app)
   - ImageOptim (Mac)

3. **Convert to WebP** for best performance (optional)

### Tools:
```bash
# Install ImageMagick
brew install imagemagick  # Mac
apt install imagemagick   # Linux

# Convert and resize
convert input.jpg -resize 1200x800 -quality 85 output.jpg

# Bulk convert to WebP
for img in *.jpg; do 
    cwebp "$img" -o "${img%.jpg}.webp"
done
```

## Quick Setup with Example Images

### Using Your Original HTML Images:

Your original portfolio had these images:
- `hero.jpeg` - Profile/Hero image
- `parking.jpg` - Parking System project
- `pharmacy.jpg` - Online Pharmacy project
- `password.jpg` - Password Manager project
- `contact.jpg` - Contact page image
- `wd.jpg` - Web Development blog
- `al.jpg` - Analytics blog
- `cs.jpg` - Cybersecurity blog

**To use these**:
1. Create `media/profile/` folder
2. Copy `hero.jpeg` → `media/profile/brian.jpg`
3. Create `media/projects/` folder
4. Copy project images → `media/projects/`
5. Create `media/blog/` folder
6. Copy blog images → `media/blog/`

## Directory Structure

```
media/
├── profile/
│   └── brian.jpg (your hero.jpeg)
├── projects/
│   ├── parking-system.jpg
│   ├── online-pharmacy.jpg
│   ├── password-manager.jpg
│   └── ... (more project images)
├── blog/
│   ├── web-development.jpg
│   ├── data-analytics.jpg
│   ├── cybersecurity.jpg
│   └── ... (more blog images)
├── testimonials/
│   ├── client-1.jpg
│   ├── client-2.jpg
│   └── ... (client photos)
├── resume/
│   └── Brian_Getenga_Resume.pdf
└── uploads/  (CKEditor uploads)
```

## Initial Data Setup Script

Create this script `load_initial_images.py` in your project root:

```python
import os
from django.core.files import File
from core.models import SiteSettings, Project, BlogPost

def setup_initial_data():
    # Update site settings
    settings = SiteSettings.load()
    
    # Add profile image
    if os.path.exists('media/profile/brian.jpg'):
        with open('media/profile/brian.jpg', 'rb') as f:
            settings.profile_image.save('brian.jpg', File(f), save=True)
    
    # Create sample projects
    projects_data = [
        {
            'title': 'Parking System',
            'description': 'A parking system automates vehicle entry, exit, payments...',
            'technologies': 'Bootstrap, HTML, CSS, JavaScript, PHP',
            'image': 'media/projects/parking-system.jpg',
            'github_url': 'https://github.com/Brian-Getenga/Parking-System',
        },
        # Add more projects...
    ]
    
    for proj_data in projects_data:
        if os.path.exists(proj_data['image']):
            project = Project.objects.create(
                title=proj_data['title'],
                description=proj_data['description'],
                technologies=proj_data['technologies'],
                github_url=proj_data['github_url'],
                status='completed',
                featured=True
            )
            with open(proj_data['image'], 'rb') as f:
                project.featured_image.save(
                    os.path.basename(proj_data['image']), 
                    File(f), 
                    save=True
                )

if __name__ == '__main__':
    setup_initial_data()
    print("Initial data loaded successfully!")
```

Run with:
```bash
python manage.py shell < load_initial_images.py
```

## Image Best Practices

### For Web Performance:
1. **Use appropriate formats**:
   - JPG for photos
   - PNG for graphics with transparency
   - WebP for best compression (modern browsers)
   - SVG for icons and logos

2. **Implement lazy loading** (already included in templates)

3. **Use responsive images**:
```html
<picture>
  <source srcset="image.webp" type="image/webp">
  <source srcset="image.jpg" type="image/jpeg">
  <img src="image.jpg" alt="Description">
</picture>
```

4. **Add proper alt text** for SEO and accessibility

### For SEO:
- Use descriptive filenames: `django-portfolio-project.jpg` not `IMG_1234.jpg`
- Add alt text to all images
- Use appropriate image dimensions
- Compress images without losing quality

## Common Issues & Solutions

### Issue: Images not displaying
**Solution**: 
1. Check `MEDIA_URL` and `MEDIA_ROOT` in settings
2. Ensure media folder exists
3. Run `python manage.py collectstatic`
4. Check file permissions

### Issue: Upload errors
**Solution**:
1. Check `FILE_UPLOAD_MAX_MEMORY_SIZE` in settings
2. Ensure media folder has write permissions
3. Check disk space

### Issue: Images load slowly
**Solution**:
1. Compress images before upload
2. Use WebP format
3. Implement lazy loading (already done)
4. Use CDN for production

## Production Image Hosting

### Option 1: AWS S3 (Recommended)
```python
# settings.py
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
```

### Option 2: Cloudinary
```python
# Install: pip install django-cloudinary-storage
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET')
}

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
```

### Option 3: DigitalOcean Spaces
Similar to AWS S3 but cheaper for smaller projects.

## Quick Start Checklist

- [ ] Upload profile image
- [ ] Upload at least 3 project images
- [ ] Upload resume PDF
- [ ] Add 2-3 blog post images
- [ ] Add 2-3 testimonial images (optional)
- [ ] Test image uploads in admin
- [ ] Verify images display on frontend
- [ ] Check mobile image loading
- [ ] Compress all images
- [ ] Add proper alt text

## Need Help?

If you need help sourcing or creating images:
1. Use Canva (https://canva.com) for quick graphics
2. Hire on Fiverr for professional designs
3. Use screenshot tools for project images
4. Contact: briangetenga3@gmail.com

---

**Remember**: Good images make a great first impression! 📸✨
