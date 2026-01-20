# Heroku Deployment Guide for DopeEvents

## Prerequisites
1. Heroku CLI installed
2. Heroku account
3. Git repository set up

## Deployment Steps

### 1. Install Heroku CLI
```bash
# Download and install from https://devcenter.heroku.com/articles/heroku-cli
```

### 2. Login to Heroku
```bash
heroku login
```

### 3. Create Heroku App
```bash
heroku create your-app-name
```

### 4. Set Environment Variables
```bash
# Set Django settings
heroku config:set DEBUG=False
heroku config:set SECRET_KEY=your-secret-key-here

# Set database (if using Heroku Postgres)
heroku addons:create heroku-postgresql:hobby-dev

# Set Supabase credentials (if using Supabase)
heroku config:set SUPABASE_DB_NAME=your-db-name
heroku config:set SUPABASE_DB_USER=your-db-user
heroku config:set SUPABASE_DB_PASSWORD=your-db-password
heroku config:set SUPABASE_DB_HOST=your-db-host
heroku config:set SUPABASE_DB_PORT=5432

# Set Cloudinary credentials (if using Cloudinary)
heroku config:set CLOUDINARY_CLOUD_NAME=your-cloud-name
heroku config:set CLOUDINARY_API_KEY=your-api-key
heroku config:set CLOUDINARY_API_SECRET=your-api-secret

# Set email configuration
heroku config:set EMAIL_HOST=smtp.gmail.com
heroku config:set EMAIL_PORT=587
heroku config:set EMAIL_HOST_USER=your-email@gmail.com
heroku config:set EMAIL_HOST_PASSWORD=your-app-password
heroku config:set DEFAULT_FROM_EMAIL=noreply@events.com

# Set M-Pesa credentials
heroku config:set CONSUMER_KEY=your-consumer-key
heroku config:set CONSUMER_SECRET=your-consumer-secret
heroku config:set SHORTCODE=your-shortcode
heroku config:set PASSKEY=your-passkey
heroku config:set BASE_URL=https://api.safaricom.co.ke
heroku config:set CALLBACK_URL=https://your-app-name.herokuapp.com/mpesa/callback

# Set Stripe credentials
heroku config:set STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key
heroku config:set STRIPE_SECRET_KEY=your-stripe-secret-key

# Set Twilio credentials
heroku config:set TWILIO_ACCOUNT_SID=your-twilio-sid
heroku config:set TWILIO_AUTH_TOKEN=your-twilio-token
heroku config:set TWILIO_PHONE_NUMBER=your-twilio-number
```

### 5. Deploy to Heroku
```bash
# Add files to git
git add .
git commit -m "Configure for Heroku deployment"

# Push to Heroku
git push heroku master
```

### 6. Run Migrations
```bash
heroku run python manage.py migrate
```

### 7. Create Superuser
```bash
heroku run python manage.py createsuperuser
```

### 8. Open the App
```bash
heroku open
```

## Important Notes

### Database Configuration
- **Option 1**: Use Heroku Postgres (recommended for production)
- **Option 2**: Use Supabase (already configured in settings)

### Static Files
- Static files are handled by WhiteNoise
- Media files are handled by Cloudinary (if configured)

### Environment Variables
Make sure to set all required environment variables in Heroku dashboard or via CLI before deployment.

### Debug Mode
Always set `DEBUG=False` in production.

### Allowed Hosts
The django-heroku package automatically configures ALLOWED_HOSTS for Heroku.

## Troubleshooting

### Application Error
```bash
heroku logs --tail
```

### Database Connection Issues
```bash
heroku config:get DATABASE_URL
```

### Static Files Not Loading
```bash
heroku run python manage.py collectstatic --noinput
```

## Post-Deployment Checklist
- [ ] All environment variables set
- [ ] Database migrations applied
- [ ] Superuser created
- [ ] Static files collected
- [ ] Test payment integrations
- [ ] Test email functionality
- [ ] Verify all pages load correctly
