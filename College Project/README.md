# Student Enquiry & College Portal

A secure, academic-purpose Django application for student registration, mentor assignment, and college portal management. Built with modern web technologies and comprehensive security features.

## 🚀 Features

### Public Features
- **Landing Page**: Futuristic hero section with glassmorphism design and smooth transitions
- **Student Registration**: Comprehensive form with academic records, PINCODE auto-fill, and validation
- **Email Verification**: Secure token-based verification with Terms & Conditions

### Portal Features (Verified Users)
- **Home Dashboard**: Personalized welcome with navigation
- **Academics**: Dynamic program/course listings managed via admin
- **Contact & Mentor Request**: Contact information and mentor request system

### Director/Admin Features
- **Analytics Dashboard**: Visitor counts, registration statistics, pending verifications
- **Mentor Management**: Create, edit, and assign mentors to students
- **User Management**: View profiles, mark verifications, export data to CSV
- **Content Management**: Edit portal content, programs, and contact information

### Technical Features
- **Security**: Password hashing, email verification, rate limiting, staff-only routes
- **Notifications**: Email templates + WhatsApp integration (Twilio API)
- **Analytics**: Visitor tracking, registration logs, mentor assignment history
- **Responsive Design**: Mobile-first CSS with glassmorphism and neon accents

## 🛠️ Tech Stack

- **Backend**: Python 3.11+, Django 5.0.7, Django REST Framework
- **Database**: PostgreSQL with psycopg2
- **Frontend**: HTML5, CSS3, Vanilla JavaScript (no heavy frameworks)
- **Email**: Django Email backend (configurable for SendGrid, SES, etc.)
- **WhatsApp**: Twilio WhatsApp API integration
- **Deployment**: Gunicorn + Nginx (no Docker required)

## 📋 Prerequisites

- Python 3.11 or higher
- PostgreSQL 12 or higher
- Git
- Virtual environment (recommended)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd college-portal
python -m venv .venv

# Windows
.\.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
SITE_BASE_URL=http://localhost:8000

# Database
POSTGRES_DB=college_portal
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Email (example for SendGrid)
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
DEFAULT_FROM_EMAIL=College <no-reply@yourcollege.edu>

# Twilio WhatsApp (optional)
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

### 3. Database Setup

```bash
# Create PostgreSQL database
psql -U postgres -c "CREATE DATABASE college_portal;"

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 4. Run Development Server

```bash
python manage.py runserver
```

Visit:
- **Landing**: http://127.0.0.1:8000/
- **Admin**: http://127.0.0.1:8000/admin/
- **Registration**: http://127.0.0.1:8000/register/

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test core

# Run with coverage (install coverage first)
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Generates HTML report
```

## 📊 Admin Setup

### 1. Access Admin Interface
- Visit `/admin/` and login with your superuser credentials
- Customize admin site header and branding

### 2. Create Initial Content
- **Mentors**: Add mentor profiles with portfolio URLs and WhatsApp links
- **Page Content**: Create program listings (key: `program:Computer Science`, value: description)
- **Contact Info**: Set contact email/phone (key: `contact:email`, value: `info@college.edu`)

### 3. User Management
- View all registrations and verification status
- Export user data to CSV
- Mark users as verified manually if needed

## 🔒 Security Features

- **Password Security**: Django's PBKDF2 hashing
- **Email Verification**: Signed, expiring tokens
- **Rate Limiting**: Registration endpoint protection (5 requests/minute per IP)
- **Staff Access**: Director dashboard requires staff permissions
- **Input Validation**: Server-side validation for all forms
- **CSRF Protection**: Built-in Django CSRF tokens

## 📧 Email & WhatsApp Integration

### Email Configuration
The app supports multiple email backends:

```python
# SendGrid
EMAIL_HOST=smtp.sendgrid.net
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-api-key

# Amazon SES
EMAIL_HOST=email-smtp.us-east-1.amazonaws.com
EMAIL_HOST_USER=your-access-key
EMAIL_HOST_PASSWORD=your-secret-key

# Gmail (for testing)
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### WhatsApp Integration
Configure Twilio credentials in `.env`:

```env
TWILIO_ACCOUNT_SID=AC1234567890abcdef
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

## 🚀 Production Deployment

### 1. Server Setup (Ubuntu/Debian)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python, PostgreSQL, Nginx
sudo apt install python3 python3-pip python3-venv postgresql postgresql-contrib nginx

# Install Gunicorn
pip3 install gunicorn
```

### 2. Application Deployment

```bash
# Clone your repository
git clone <your-repo-url> /var/www/college-portal
cd /var/www/college-portal

# Setup virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with production values

# Run migrations
python manage.py migrate
python manage.py collectstatic
python manage.py createsuperuser
```

### 3. Gunicorn Configuration

Create `/etc/systemd/system/college-portal.service`:

```ini
[Unit]
Description=College Portal Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/college-portal
Environment="PATH=/var/www/college-portal/.venv/bin"
ExecStart=/var/www/college-portal/.venv/bin/gunicorn --workers 3 --bind unix:/var/www/college-portal/college_portal.sock college_portal.wsgi:application

[Install]
WantedBy=multi-user.target
```

### 4. Nginx Configuration

Create `/etc/nginx/sites-available/college-portal`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /var/www/college-portal;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/college-portal/college_portal.sock;
    }
}
```

Enable and start services:

```bash
# Enable Nginx site
sudo ln -s /etc/nginx/sites-available/college-portal /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx

# Start Gunicorn service
sudo systemctl start college-portal
sudo systemctl enable college-portal
```

### 5. SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 📁 Project Structure

```
college-portal/
├── college_portal/          # Project settings
│   ├── __init__.py
│   ├── settings.py          # Django configuration
│   ├── urls.py             # Main URL routing
│   └── wsgi.py             # WSGI application
├── core/                    # Main application
│   ├── __init__.py
│   ├── admin.py            # Admin interface
│   ├── apps.py             # App configuration
│   ├── models.py           # Database models
│   ├── views.py            # View logic
│   ├── urls.py             # App URL routing
│   ├── utils.py            # Utility functions
│   ├── middleware.py       # Custom middleware
│   └── tests.py            # Test suite
├── templates/               # HTML templates
│   ├── public/             # Public pages
│   ├── portal/             # Portal pages
│   └── emails/             # Email templates
├── static/                  # Static assets
│   ├── css/                # Stylesheets
│   └── js/                 # JavaScript
├── manage.py               # Django management
├── requirements.txt         # Python dependencies
├── .env.example            # Environment template
└── README.md               # This file
```

## 🔧 Customization

### Adding New Programs
1. Go to Admin → Page Content
2. Add new entry with key: `program:Program Name`
3. Set value to program description

### Customizing Email Templates
Edit templates in `templates/emails/`:
- `verify_email.txt`: Registration verification email
- `mentor_assignment.txt`: Mentor assignment notification

### Styling Changes
Modify `static/css/styles.css` for:
- Color schemes (CSS variables in `:root`)
- Layout adjustments
- Animation timing

## 🐛 Troubleshooting

### Common Issues

**Database Connection Error**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Verify connection
psql -U postgres -h localhost -d college_portal
```

**Email Not Sending**
- Verify SMTP credentials in `.env`
- Check firewall settings
- Test with Django shell:
```python
python manage.py shell
from django.core.mail import send_mail
send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])
```

**Static Files Not Loading**
```bash
python manage.py collectstatic
# Check STATIC_ROOT in settings.py
```

**Permission Denied Errors**
```bash
# Fix file permissions
sudo chown -R www-data:www-data /var/www/college-portal
sudo chmod -R 755 /var/www/college-portal
```

## 📈 Performance Optimization

### Database
- Add database indexes for frequently queried fields
- Use `select_related()` and `prefetch_related()` for related queries
- Consider database connection pooling

### Caching
- Replace local memory cache with Redis for production
- Cache frequently accessed data (programs, contact info)
- Use Django's cache framework

### Static Files
- Enable Gzip compression in Nginx
- Use CDN for static assets
- Optimize images and minify CSS/JS

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the troubleshooting section above
- Review Django documentation for framework-specific questions

## 🔄 Updates & Maintenance

### Regular Tasks
- Monitor error logs: `sudo journalctl -u college-portal`
- Backup database: `pg_dump college_portal > backup.sql`
- Update dependencies: `pip install -r requirements.txt --upgrade`
- Check SSL certificate renewal: `sudo certbot renew --dry-run`

### Security Updates
- Keep Django and dependencies updated
- Monitor security advisories
- Regular security audits
- Update environment variables regularly

---

**Built with ❤️ for educational institutions**







