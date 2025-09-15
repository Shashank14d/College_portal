import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Applications
INSTALLED_APPS = [
	"django.contrib.admin",
	"django.contrib.auth",
	"django.contrib.contenttypes",
	"django.contrib.sessions",
	"django.contrib.messages",
	"django.contrib.staticfiles",
	"core",
]

# Middleware
MIDDLEWARE = [
	"django.middleware.security.SecurityMiddleware",
	"django.contrib.sessions.middleware.SessionMiddleware",
	"django.middleware.common.CommonMiddleware",
	"django.middleware.csrf.CsrfViewMiddleware",
	"django.contrib.auth.middleware.AuthenticationMiddleware",
	"django.contrib.messages.middleware.MessageMiddleware",
	"django.middleware.clickjacking.XFrameOptionsMiddleware",
	"core.middleware.RegistrationRateLimitMiddleware",
	"core.middleware.AdminRestrictionMiddleware",
]

# URLs and WSGI
ROOT_URLCONF = "college_portal.urls"
WSGI_APPLICATION = "college_portal.wsgi.application"

# Templates
TEMPLATES = [
	{
		"BACKEND": "django.template.backends.django.DjangoTemplates",
		"DIRS": [BASE_DIR / "templates"],
		"APP_DIRS": True,
		"OPTIONS": {
			"context_processors": [
				"django.template.context_processors.debug",
				"django.template.context_processors.request",
				"django.contrib.auth.context_processors.auth",
				"django.contrib.messages.context_processors.messages",
			],
		},
	}
]

# Database Configuration
# Try PostgreSQL first, fallback to SQLite if connection fails
import getpass

def get_database_config():
    """Get database configuration, try PostgreSQL first"""
    # Check if we have PostgreSQL password
    password = os.getenv("DB_PASSWORD")
    
    if password:
        # Try PostgreSQL with provided password
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST", "localhost"),
                port=os.getenv("DB_PORT", "5432"),
                database=os.getenv("DB_NAME", "college_portal"),
                user=os.getenv("DB_USER", "postgres"),
                password=password
            )
            conn.close()
            print("✅ Using PostgreSQL database")
            return {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": os.getenv("DB_NAME", "college_portal"),
                "USER": os.getenv("DB_USER", "postgres"),
                "PASSWORD": password,
                "HOST": os.getenv("DB_HOST", "localhost"),
                "PORT": os.getenv("DB_PORT", "5432"),
            }
        except Exception as e:
            print(f"⚠️ PostgreSQL connection failed: {e}")
            print("🔄 Falling back to SQLite...")
    
    # Fallback to SQLite
    print("✅ Using SQLite database")
    return {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }

DATABASES = {
    "default": get_database_config()
}

# Password validation (keep defaults)
AUTH_PASSWORD_VALIDATORS = [
	{"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
	{"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
	{"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
	{"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

# Media files (for user-uploaded content)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Email / Site config
# Use environment variables for email credentials
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER or "webmaster@localhost"

# Admin/Manager emails for error reports
ADMINS = [("Admin", EMAIL_HOST_USER)] if EMAIL_HOST_USER else []
MANAGERS = ADMINS

SITE_BASE_URL = "http://127.0.0.1:8000"