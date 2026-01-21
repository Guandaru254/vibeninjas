# DopeEvents Django Project

A clean, organized Django events management application.

## Project Structure

```
DopeEvents/
├── .env                    # Environment variables (local)
├── .env.development         # Development environment
├── .env.production          # Production environment
├── .gitignore              # Git ignore rules
├── requirements.txt         # Python dependencies
├── env/                   # Virtual environment
└── DopeEvents/            # Django project
    ├── manage.py           # Django management script
    ├── DopeEvents/        # Django configuration
    │   ├── settings.py     # Main settings
    │   ├── urls.py        # URL routing
    │   └── wsgi.py        # WSGI configuration
    ├── events/            # Events app
    ├── payments/          # Payments app
    ├── analytics/         # Analytics app
    ├── seller_merchandise/ # Merchandise app
    ├── static/           # Static files
    ├── media/            # Media files
    └── templates/        # HTML templates
```

## Quick Start

### 1. Setup Virtual Environment
```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
Copy `.env.example` to `.env` and configure:
- Database settings
- Cloudinary keys
- Email configuration
- Payment integrations

### 4. Run Migrations
```bash
python DopeEvents/manage.py migrate
```

### 5. Create Superuser
```bash
python DopeEvents/manage.py createsuperuser
```

### 6. Start Development Server
```bash
python DopeEvents/manage.py runserver
```

## Features

- **Event Management**: Create and manage events
- **User Authentication**: User registration and login
- **Payment Processing**: Stripe and M-Pesa integration
- **Media Management**: Cloudinary integration
- **Analytics**: Event tracking and reporting
- **Merchandise**: Product sales management

## Configuration

### Environment Variables
Key environment variables needed:

```bash
# Database
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_password
DB_HOST=your_host
DB_PORT=5432

# Cloudinary
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password

# Stripe
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...

# M-Pesa
MPESA_CONSUMER_KEY=your_consumer_key
MPESA_CONSUMER_SECRET=your_consumer_secret
```

## Dependencies

Main dependencies include:
- Django 4.2+
- Django REST Framework
- PostgreSQL (psycopg2)
- Cloudinary
- Stripe
- Gunicorn
- Whitenoise

## Deployment

This project can be deployed to:
- **Render.com** (recommended)
- **Heroku**
- **DigitalOcean**
- **AWS**
- **Google Cloud Platform**

See deployment guides for specific platforms.

## Development

### Adding New Apps
```bash
python DopeEvents/manage.py startapp new_app_name
```

### Running Tests
```bash
python DopeEvents/manage.py test
```

### Collecting Static Files
```bash
python DopeEvents/manage.py collectstatic
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions, please open an issue in the repository.
