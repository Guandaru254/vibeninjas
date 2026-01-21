# Render Environment Variables Setup

## 📋 Required Environment Variables

### Django Core Settings (Auto-configured by render.yaml)
- ✅ `DJANGO_SETTINGS_MODULE=DopeEvents.settings`
- ✅ `SECRET_KEY` (auto-generated)
- ✅ `DEBUG=False`
- ✅ `ALLOWED_HOSTS=vibeninjas.co.ke,localhost,127.0.0.1`
- ✅ `RENDER_SERVICE_ID=dopeevents-web`

### Cloudinary Configuration (Add manually in Render dashboard)
You need to add these values in your Render service dashboard:

1. **CLOUDINARY_CLOUD_NAME**
   - Get from your Cloudinary dashboard
   - Example: `your-cloud-name`

2. **CLOUDINARY_API_KEY**
   - Get from your Cloudinary dashboard
   - Example: `123456789012345`

3. **CLOUDINARY_API_SECRET**
   - Get from your Cloudinary dashboard
   - Example: `your-api-secret-key`

## 🔧 How to Add Environment Variables in Render

1. **Go to Render Dashboard**: https://dashboard.render.com
2. **Select your service**: `dopeevents-web`
3. **Click "Environment" tab**
4. **Add Cloudinary variables**:
   - Click "Add Environment Variable"
   - Add the three Cloudinary variables above
5. **Save changes**
6. **Redeploy** (automatic or manual)

## 🚀 Deployment Steps

### Option 1: Using render.yaml (Recommended)
1. Push your code to GitHub
2. Go to Render dashboard
3. Click "New +" → "Blueprint"
4. Connect your GitHub repo
5. Render will detect `render.yaml`
6. Click "Apply"

### Option 2: Manual Setup
1. Create Web Service manually
2. Configure build/start commands
3. Add environment variables above
4. Deploy

## 📊 Current Configuration

Your `render.yaml` includes:
- ✅ **Gunicorn** server configuration
- ✅ **Django** settings
- ✅ **Auto-deployment** on git push
- ✅ **Health checks**
- ✅ **Free tier** optimization

## 🎯 Next Steps

1. **Deploy to Render** using render.yaml
2. **Add Cloudinary variables** in dashboard
3. **Test deployment**
4. **Run migrations** (if needed)

## 📝 Notes

- Database is already configured in `settings.py`
- Gunicorn is configured as the WSGI server
- Static files handled by Whitenoise
- Auto-deployment enabled for git pushes
