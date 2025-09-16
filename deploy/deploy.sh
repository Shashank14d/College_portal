#!/bin/bash

# College Portal Deployment Script
# This script automates the deployment process for the College Portal

set -e  # Exit on any error

echo "🚀 Starting College Portal Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/var/www/college-portal"
VENV_DIR="$PROJECT_DIR/.venv"
BACKUP_DIR="/var/backups/college-portal"
LOG_FILE="/var/log/college-portal/deploy.log"

# Create log directory if it doesn't exist
sudo mkdir -p /var/log/college-portal

# Function to log messages
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

# Function to log success
log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✅ $1${NC}" | tee -a "$LOG_FILE"
}

# Function to log warning
log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}" | tee -a "$LOG_FILE"
}

# Function to log error
log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ❌ $1${NC}" | tee -a "$LOG_FILE"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    log_error "Please do not run this script as root"
    exit 1
fi

# Check if project directory exists
if [ ! -d "$PROJECT_DIR" ]; then
    log_error "Project directory $PROJECT_DIR does not exist"
    exit 1
fi

cd "$PROJECT_DIR"

# Create backup
log "Creating backup..."
sudo mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/backup-$(date +'%Y%m%d-%H%M%S').tar.gz"
sudo tar -czf "$BACKUP_FILE" --exclude='.venv' --exclude='__pycache__' --exclude='*.pyc' .
log_success "Backup created: $BACKUP_FILE"

# Pull latest changes from Git
log "Pulling latest changes from Git..."
git pull origin main
log_success "Git pull completed"

# Activate virtual environment
log "Activating virtual environment..."
source "$VENV_DIR/bin/activate"
log_success "Virtual environment activated"

# Install/update dependencies
log "Installing/updating dependencies..."
pip install -r requirements.txt --upgrade
log_success "Dependencies updated"

# Run database migrations
log "Running database migrations..."
python manage.py migrate
log_success "Database migrations completed"

# Collect static files
log "Collecting static files..."
python manage.py collectstatic --noinput
log_success "Static files collected"

# Clear cache
log "Clearing cache..."
python manage.py clear_cache
log_success "Cache cleared"

# Run setup command (if needed)
log "Running portal setup..."
python manage.py setup_portal --force
log_success "Portal setup completed"

# Test the application
log "Running tests..."
python manage.py test --verbosity=0
log_success "Tests passed"

# Restart services
log "Restarting services..."

# Restart Gunicorn
sudo systemctl restart college-portal
if [ $? -eq 0 ]; then
    log_success "Gunicorn restarted"
else
    log_error "Failed to restart Gunicorn"
    exit 1
fi

# Restart Nginx
sudo systemctl restart nginx
if [ $? -eq 0 ]; then
    log_success "Nginx restarted"
else
    log_error "Failed to restart Nginx"
    exit 1
fi

# Check service status
log "Checking service status..."
if systemctl is-active --quiet college-portal; then
    log_success "College Portal service is running"
else
    log_error "College Portal service is not running"
    exit 1
fi

if systemctl is-active --quiet nginx; then
    log_success "Nginx service is running"
else
    log_error "Nginx service is not running"
    exit 1
fi

# Health check
log "Performing health check..."
HEALTH_URL="http://localhost"
if curl -f -s "$HEALTH_URL" > /dev/null; then
    log_success "Health check passed"
else
    log_warning "Health check failed - please check the application manually"
fi

# Cleanup old backups (keep last 5)
log "Cleaning up old backups..."
sudo find "$BACKUP_DIR" -name "backup-*.tar.gz" -type f -mtime +7 -delete
log_success "Old backups cleaned up"

# Final status
log_success "Deployment completed successfully!"
log "Application URL: $HEALTH_URL"
log "Log file: $LOG_FILE"
log "Backup: $BACKUP_FILE"

echo ""
echo "🎉 College Portal has been deployed successfully!"
echo "📊 Check the application at: $HEALTH_URL"
echo "📝 View logs: tail -f $LOG_FILE"
echo "💾 Latest backup: $BACKUP_FILE"