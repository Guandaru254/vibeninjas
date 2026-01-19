# Production Deployment Guide - DopeEvents

## 🚀 Deploying to Render with Supabase & Cloudinary

### Prerequisites
- Render account (https://render.com)
- Supabase account (https://supabase.com)
- Cloudinary account (https://cloudinary.com)
- Domain name (optional)

---

## 📋 Step-by-Step Setup

### 1. Supabase Database Setup

1. **Create Supabase Project**
   - Go to https://supabase.com
   - Click "New Project"
   - Choose organization and project name
   - Set database password (save it!)
   - Choose region closest to your users

2. **Get Database Credentials**
   - Go to Settings → Database
   - Copy connection string
   - Extract these values:
     ```
     SUPABASE_DB_NAME=postgres
     SUPABASE_DB_USER=postgres.your-project-ref
     SUPABASE_DB_PASSWORD=your-password
     SUPABASE_DB_HOST=db.your-project-ref.supabase.co
     SUPABASE_DB_PORT=5432
     ```

### 2. Cloudinary Setup

1. **Create Cloudinary Account**
   - Go to https://cloudinary.com
   - Sign up for free tier
   - Create cloud (give it a name)

2. **Get Cloudinary Credentials**
   - Dashboard → Account Details
   - Copy these values:
     ```
     CLOUDINARY_CLOUD_NAME=your-cloud-name
     CLOUDINARY_API_KEY=your-api-key
     CLOUDINARY_API_SECRET=your-api-secret
     CLOUDINARY_URL=cloudinary://api-key:api-secret@cloud-name
     ```

### 3. Render Deployment

1. **Connect Repository**
   - Go to Render dashboard
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select your DopeEvents repo

2. **Configure Build Settings**
   ```
   Build Command: pip install -r requirements.txt
   Start Command: gunicorn DopeEvents.wsgi:application
   Runtime: Python 3
   ```

3. **Set Environment Variables**
   - Copy all variables from `.env.production`
   - Go to Render → Environment tab
   - Add each environment variable
   - **Important**: Set `DEBUG=False`

4. **Database Migration**
   - After first deploy, go to Render → Shell
   - Run: `python migrate_to_supabase.py`
   - Create superuser: `python manage.py createsuperuser`

---

## 🔧 Configuration Files

### requirements.txt
```txt
django>=4.2.0,<5.0
djangorestframework>=3.14.0
django-cors-headers>=4.0.0
psycopg2-binary>=2.9.0
supabase>=2.0.0
python-dotenv>=1.0.0
cloudinary>=1.35.0
Pillow>=10.0.0
django-allauth>=0.54.0
gunicorn>=21.0.0
whitenoise>=6.5.0
crispy-bootstrap5>=0.7
django-filter>=23.0
```

### render.yaml (Optional)
```yaml
services:
  - type: web
    name: dope-events
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn DopeEvents.wsgi:application
    envVars:
      - key: DEBUG
        value: False
      - key: DATABASE_URL
        fromDatabase:
          name: dope-events-db
          property: connectionString
```

---

## 🔄 Migration Process

### From Development to Production

1. **Backup Local Data**
   ```bash
   python manage.py dumpdata > local_data.json
   ```

2. **Run Migration Script**
   ```bash
   python migrate_to_supabase.py
   ```

3. **Verify Data**
   ```bash
   python manage.py shell
   >>> from events.models import User
   >>> User.objects.count()
   ```

---

## 🛠️ Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Check Supabase credentials
   - Verify IP whitelist in Supabase
   - Ensure SSL is enabled

2. **Cloudinary Upload Error**
   - Verify Cloudinary credentials
   - Check upload permissions
   - Ensure file size limits

3. **Static Files Not Loading**
   - Run: `python manage.py collectstatic`
   - Check STATIC_URL settings
   - Verify Cloudinary static storage

4. **CSS/JS Not Working**
   - Check ALLOWED_HOSTS
   - Verify CSRF_TRUSTED_ORIGINS
   - Clear browser cache

---

## 🔒 Security Checklist

- [ ] Set `DEBUG=False` in production
- [ ] Use strong `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set up `CSRF_TRUSTED_ORIGINS`
- [ ] Enable HTTPS (automatic on Render)
- [ ] Use environment variables for secrets
- [ ] Regular database backups
- [ ] Monitor Cloudinary usage

---

## 📊 Monitoring

### Render Monitoring
- Automatic health checks
- Log viewing in dashboard
- Metrics and alerts

### Supabase Monitoring
- Database performance
- Query analytics
- Storage usage

### Cloudinary Monitoring
- Image optimization
- Bandwidth usage
- Storage quotas

---

## 🚀 Performance Optimization

1. **Database Optimization**
   - Use PostgreSQL indexes
   - Optimize queries
   - Enable connection pooling

2. **Image Optimization**
   - Cloudinary auto-optimization
   - WebP format support
   - Responsive images

3. **Caching**
   - Redis for session storage
   - Database query caching
   - Static file caching

---

## 💡 Pro Tips

1. **Use Render's Preview Environments** for testing
2. **Set up custom domain** for branding
3. **Configure email services** for notifications
4. **Monitor costs** on all platforms
5. **Regular backups** of database and media

---

## 🆘 Support

- **Render**: https://render.com/docs
- **Supabase**: https://supabase.com/docs
- **Cloudinary**: https://cloudinary.com/documentation
- **Django**: https://docs.djangoproject.com
