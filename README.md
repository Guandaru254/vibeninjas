# Vibeninjas - A Ticket and Event Platform

A ticket and event platform that allows organizers to create and manage events, while attendees can purchase tickets securely.

## Features

### Core Features
- User authentication for event organizers
- Event creation and management
- Ticket purchasing system
- Secure payment processing with Stripe
- Mobile responsive design

### Pro Features (Vibeninjas Pro)
- Advanced analytics
- Priority support
- Custom branding
- Multiple subscription tiers:
  - Daily ($5/day)
  - Monthly ($49/month)
  - Yearly ($399/year)

## Technology Stack

- **Backend**: Django 4.2
- **Frontend**: Bootstrap 5.3
- **Database**: SQLite (Development) / PostgreSQL (Production)
- **Payment Processing**: Stripe,M-PESA
- **Icons**: Font Awesome 6.4
- **Additional Libraries**: Pillow (Image processing)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/tazamoafrica/vibeninjas.git
cd vibeninjas
```

2. Create and activate virtual environment:
```bash
python -m venv env
env\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create environment variables file (.env):
```plaintext
SECRET_KEY=your_django_secret_key
STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key
STRIPE_SECRET_KEY=your_stripe_secret_key
```

5. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

6. Create superuser:
```bash
python manage.py createsuperuser
```

7. Run the development server:
```bash
python manage.py runserver
```

## Project Structure

```
vibeninjas/
├── events/                 # Main application directory
│   ├── migrations/        # Database migrations
│   ├── templates/        # HTML templates
│   │   ├── base.html    # Base template
│   │   ├── events/      # Event-related templates
│   │   └── registration/ # Auth-related templates
│   ├── models.py        # Database models
│   ├── views.py         # View logic
│   ├── urls.py          # URL configurations
│   └── forms.py         # Form definitions
├── static/              # Static files (CSS, JS, images)
├── media/              # User-uploaded files
└── manage.py           # Django management script
```

## Models

### User
- Custom user model extending AbstractUser
- Includes pro status tracking
- Handles subscription management

### Event
- Title, description, image
- Date and location
- Ticket pricing and availability
- Organizer relationship

### Ticket
- Event relationship
- Buyer information
- Payment tracking
- Unique ticket code

### Subscription
- User relationship
- Plan type and status
- Payment tracking
- Expiration handling

## API Endpoints

### Events
- `GET /events/` - List all events
- `GET /event/<id>/` - Event details
- `POST /create-event/` - Create new event
- `PUT /edit-event/<id>/` - Update event
- `DELETE /event/<id>/` - Delete event

### Authentication
- `POST /login/` - Organizer login
- `POST /logout/` - Logout
- `GET /dashboard/` - Organizer dashboard

### Tickets
- `POST /checkout/<event_id>/` - Purchase tickets
- `GET /ticket/<ticket_id>/` - Ticket confirmation

### Subscriptions
- `POST /subscribe/<plan>/` - Subscribe to pro plan
- `GET /pro-features/` - Pro features
- `GET /subscription/settings/` - Manage subscription

### Gate Verification (NEW)
- `POST /api/v1/gate/verify-ticket/` - Verify ticket at gate entry
- `POST /api/v1/gate/validate-signature/` - Validate HMAC signature only

#### Gate Verification Endpoint Details

**POST /api/v1/gate/verify-ticket/**

Verify a ticket at the gate using HMAC-SHA256 signature validation. This endpoint:
- Validates HMAC signature to prevent tampering
- Checks timestamp to prevent replay attacks (5-minute window)
- Verifies ticket status and event timing
- Marks ticket as used when valid

**Request:**
```json
{
  "ticket_code": "ABC12345",
  "timestamp": "2026-05-27T14:30:00Z",
  "signature": "abc123def456..."
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Ticket verified and marked as used",
  "ticket": {
    "ticket_code": "ABC12345",
    "status": "valid",
    "buyer_name": "John Doe",
    "buyer_email": "john@example.com",
    "event_title": "Tech Conference 2026",
    "event_date": "2026-05-27T18:00:00Z",
    "event_location": "Convention Center",
    "ticket_category": "VIP",
    "quantity": 1,
    "verified_at": "2026-05-27T14:30:15Z"
  }
}
```

**Error Responses:**
- `400 Bad Request` - Invalid payload or missing fields
- `401 Unauthorized` - Invalid or expired signature
- `404 Not Found` - Ticket not found
- `409 Conflict` - Ticket already used or invalid status

**Generating HMAC Signature (Client-side example):**
```python
import hmac
import hashlib

ticket_code = "ABC12345"
timestamp = "2026-05-27T14:30:00Z"
secret_key = "your-secret-key"

payload = f"{ticket_code}:{timestamp}".encode('utf-8')
signature = hmac.new(
    secret_key.encode('utf-8'),
    payload,
    hashlib.sha256
).hexdigest()
```

**POST /api/v1/gate/validate-signature/**

Validate a signature WITHOUT marking the ticket as used. Use for pre-validation or testing.

## Configuration

### Required Environment Variables
- `SECRET_KEY`: Django secret key
- `STRIPE_PUBLISHABLE_KEY`: Stripe public key
- `STRIPE_SECRET_KEY`: Stripe secret key

### Optional Environment Variables
- `DEBUG`: Set to False in production
- `ALLOWED_HOSTS`: List of allowed hosts
- `DATABASE_URL`: Database connection string
- `GATE_VERIFICATION_SECRET_KEY`: Secret key for gate verification HMAC signatures (defaults to `SECRET_KEY`)
- `GATE_VERIFICATION_VALIDITY_SECONDS`: Signature validity window in seconds (default: 300)

## Development

1. Setup pre-commit hooks:
```bash
pre-commit install
```

2. Run tests:
```bash
python manage.py test
```

3. Check code style:
```bash
flake8 .
```

## Deployment

1. Set environment variables
2. Collect static files:
```bash
python manage.py collectstatic
```

3. Configure database
4. Setup web server (Nginx/Apache)
5. Configure SSL certificate

## Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, email info@vibeninjas.com or create an issue in the repository.
