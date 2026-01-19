# Render Deployment Guide - Secure Setup

## 🔐 Security First

Your `.gitignore` file is now configured to protect sensitive data. The `render.yaml` file uses `sync: false` which means you'll need to set these environment variables manually in Render.

---

## 🚀 Step-by-Step Deployment

### 1. Push to GitHub
```bash
git add .
git commit -m "Secure configuration ready for Render"
git push origin main
```

### 2. Create Render Web Service
1. Go to [render.com](https://render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Select your `DopeEvents` repo
5. Render will detect your `render.yaml`

### 3. Set Environment Variables in Render

**CRITICAL:** You must set these environment variables in your Render dashboard:

#### Database Configuration
```
DATABASE_URL = postgresql://postgres:YOUR_PASSWORD@YOUR_SUPABASE_HOST:5432/postgres
SUPABASE_DB_NAME = postgres
SUPABASE_DB_USER = postgres
SUPABASE_DB_PASSWORD = YOUR_SUPABASE_PASSWORD
SUPABASE_DB_HOST = YOUR_SUPABASE_HOST
SUPABASE_DB_PORT = 5432
```

#### Cloudinary Configuration
```
CLOUDINARY_CLOUD_NAME = YOUR_CLOUDINARY_CLOUD_NAME
CLOUDINARY_API_KEY = YOUR_CLOUDINARY_API_KEY
CLOUDINARY_API_SECRET = YOUR_CLOUDINARY_API_SECRET
CLOUDINARY_URL = cloudinary://YOUR_API_KEY:YOUR_API_SECRET@YOUR_CLOUD_NAME
```

#### Django Configuration
```
DEBUG = False
ALLOWED_HOSTS = localhost,127.0.0.1,your-app-name.onrender.com
CSRF_TRUSTED_ORIGINS = https://your-app-name.onrender.com
```

#### Optional Services (set as needed)
```
EMAIL_HOST = smtp.gmail.com
EMAIL_PORT = 587
EMAIL_HOST_USER = your-email@gmail.com
EMAIL_HOST_PASSWORD = your-app-password
DEFAULT_FROM_EMAIL = noreply@yourdomain.com

CONSUMER_KEY = your-mpesa-consumer-key
CONSUMER_SECRET = your-mpesa-consumer-secret
SHORTCODE = your-mpesa-shortcode
PASSKEY = your-mpesa-passkey
BASE_URL = https://api.safaricom.co.ke
CALLBACK_URL = https://your-app-name.onrender.com/mpesa/callback

STRIPE_PUBLISHABLE_KEY = pk_live_your-stripe-publishable-key
STRIPE_SECRET_KEY = sk_live_your-stripe-secret-key

TWILIO_ACCOUNT_SID = your-twilio-account-sid
TWILIO_AUTH_TOKEN = your-twilio-auth-token
TWILIO_PHONE_NUMBER = your-twilio-phone-number
```

### 4. Deploy and Run Migrations
1. Click "Create Web Service" in Render
2. Wait for deployment to complete
3. Go to your service → "Shell"
4. Run migrations:
   ```bash
   python manage.py migrate
   ```
5. Create superuser:
   ```bash
   python manage.py createsuperuser
   ```

---

## 🔒 Security Notes

### ✅ What's Protected
- All environment files are in `.gitignore`
- No secrets in `render.yaml`
- API keys and passwords not exposed in code

### ⚠️ Important Reminders
- **Never** commit `.env` files
- **Never** share your Render environment variables
- **Always** use environment variables for secrets
- **Regularly** rotate your API keys and passwords

### 🛡️ Best Practices
1. Use different keys for development and production
2. Enable two-factor authentication on all accounts
3. Monitor your Cloudinary and Supabase usage
4. Set up alerts for unusual activity

---

## 🎯 Post-Deployment Checklist

- [ ] App loads at `https://your-app.onrender.com`
- [ ] Admin panel works at `/admin`
- [ ] User registration works
- [ ] Image uploads work (Cloudinary)
- [ ] Database operations work (Supabase)
- [ ] Email sending works (if configured)
- [ ] M-Pesa integration works (if configured)
- [ ] Stripe integration works (if configured)

---

## 🆘 Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Verify all Supabase environment variables
   - Check Supabase project is active
   - Ensure IP whitelist allows Render

2. **Cloudinary Upload Error**
   - Verify Cloudinary credentials
   - Check Cloudinary account status
   - Ensure file size limits

3. **Static Files Not Loading**
   - Run `python manage.py collectstatic` in Render shell
   - Check Cloudinary static storage

4. **CSRF Token Error**
   - Verify `CSRF_TRUSTED_ORIGINS` includes your Render URL
   - Check `ALLOWED_HOSTS` configuration

### Getting Help
- Render docs: https://render.com/docs
- Supabase docs: https://supabase.com/docs  
- Cloudinary docs: https://cloudinary.com/documentation

---

## 🔄 Updating Your App

When making changes:
1. Test locally
2. Run `python security_check.py`
3. Commit and push
4. Render will auto-deploy
5. Run migrations if needed

Your secrets are safe and your app is ready for production! 🚀
