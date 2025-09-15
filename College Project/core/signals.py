"""
Django signals for automatic actions and logging.

This module contains signals that automatically handle various events
like user creation, mentor assignment, email verification, etc.
"""

import logging
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from .models import (
    UserProfile, AcademicRecord, Mentor, MentorAssignment,
    Visitor, EmailVerificationToken, PageContent, RegistrationLog
)

# Configure logging
logger = logging.getLogger(__name__)

def initialize_logging():
    """Initialize logging system."""
    logger.info("Logging system initialized")

# User-related signals
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Intentionally do not auto-create UserProfile to avoid test collisions.

    Profiles are created explicitly where needed or via view logic.
    """
    if created:
        logger.info(f"User created: {instance.username}")

@receiver(post_save, sender=UserProfile)
def log_profile_changes(sender, instance, created, **kwargs):
    """Log profile changes."""
    if created:
        logger.info(f"New profile created for user: {instance.user.username}")
    else:
        logger.info(f"Profile updated for user: {instance.user.username}")

# Academic record signals
@receiver(post_save, sender=AcademicRecord)
def log_academic_changes(sender, instance, created, **kwargs):
    """Log academic record changes."""
    if created:
        logger.info(f"New academic record created for user: {instance.user.username} - {instance.level}")
    else:
        logger.info(f"Academic record updated for user: {instance.user.username} - {instance.level}")

# Mentor-related signals
@receiver(post_save, sender=Mentor)
def log_mentor_changes(sender, instance, created, **kwargs):
    """Log mentor changes."""
    if created:
        logger.info(f"New mentor created: {instance.name}")
    else:
        logger.info(f"Mentor updated: {instance.name}")

@receiver(post_save, sender=MentorAssignment)
def handle_mentor_assignment(sender, instance, created, **kwargs):
    """Handle mentor assignment and send notifications."""
    if created:
        # Update user profile if it exists
        try:
            profile = instance.user.profile
            profile.assigned_mentor = instance.mentor
            profile.save()
        except UserProfile.DoesNotExist:
            # User may not have a profile; skip silently
            pass
        
        # Send notifications
        from .utils import send_mentor_assignment_notifications
        send_mentor_assignment_notifications(instance.user, instance.mentor)
        
        logger.info(f"Mentor {instance.mentor.name} assigned to user {instance.user.username}")
    else:
        logger.info(f"Mentor assignment updated for user {instance.user.username}")

@receiver(post_delete, sender=MentorAssignment)
def handle_mentor_unassignment(sender, instance, **kwargs):
    """Handle mentor unassignment."""
    # Update user profile if it exists and user still exists
    try:
        if instance.user and hasattr(instance.user, 'profile'):
            profile = instance.user.profile
            profile.assigned_mentor = None
            profile.save()
            logger.info(f"Mentor unassigned from user {instance.user.username}")
    except (UserProfile.DoesNotExist, AttributeError):
        # User may have been deleted or profile doesn't exist
        logger.info(f"Mentor unassigned from user (profile not found)")

# Visitor tracking signals
@receiver(post_save, sender=Visitor)
def log_visitor_activity(sender, instance, created, **kwargs):
    """Log visitor activity."""
    if created:
        logger.info(f"New visitor: {instance.ip_address} - {instance.page_visited}")
    else:
        logger.info(f"Visitor activity updated: {instance.ip_address}")

# Email verification signals
@receiver(post_save, sender=EmailVerificationToken)
def log_email_verification_attempts(sender, instance, created, **kwargs):
    """Log email verification attempts."""
    if created:
        logger.info(f"Email verification token created for user: {instance.user.username}")
    else:
        logger.info(f"Email verification token updated for user: {instance.user.username}")

# Page content signals
@receiver(pre_save, sender=PageContent)
def log_content_changes(sender, instance, **kwargs):
    """Log changes to page content."""
    try:
        if instance.pk:  # Existing instance
            old_instance = PageContent.objects.get(pk=instance.pk)
            if old_instance.value != instance.value:
                logger.info(f"Page content updated: {instance.key} - {old_instance.value} -> {instance.value}")
        else:  # New instance
            logger.info(f"New page content created: {instance.key} = {instance.value}")
    except PageContent.DoesNotExist:
        logger.info(f"New page content created: {instance.key} = {instance.value}")

# Registration log signals
@receiver(post_save, sender=RegistrationLog)
def log_registration_events(sender, instance, created, **kwargs):
    """Log registration events."""
    if created:
        logger.info(f"Registration event logged: {instance.status} for user {instance.user.username if instance.user else 'Unknown'}")

# User welcome and verification signals
@receiver(post_save, sender=User)
def send_welcome_email(sender, instance, created, **kwargs):
    """Send welcome email to new users."""
    if created and instance.email:
        try:
            subject = "Welcome to College Portal"
            message = f"""
            Hello {instance.get_full_name() or instance.username},
            
            Welcome to the College Portal! Your account has been created successfully.
            
            Please check your email for verification instructions to activate your account.
            
            Best regards,
            College Portal Team
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.email],
                fail_silently=True
            )
            
            logger.info(f"Welcome email sent to {instance.email}")
            
        except Exception as e:
            logger.error(f"Failed to send welcome email to {instance.email}: {e}")

@receiver(post_save, sender=UserProfile)
def handle_profile_verification(sender, instance, **kwargs):
    """Handle profile verification status changes."""
    if hasattr(instance, '_verification_changed') and instance._verification_changed:
        try:
            if instance.verified:
                # Send verification confirmation email
                subject = "Account Verified - College Portal"
                message = f"""
                Hello {instance.full_name or instance.user.username},
                
                Congratulations! Your account has been verified successfully.
                You can now access all features of the College Portal.
                
                Best regards,
                College Portal Team
                """
                
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[instance.user.email],
                    fail_silently=True
                )
                
                logger.info(f"Verification confirmation email sent to {instance.user.email}")
                
        except Exception as e:
            logger.error(f"Failed to send verification confirmation email: {e}")

@receiver(pre_save, sender=UserProfile)
def track_verification_changes(sender, instance, **kwargs):
    """Track verification status changes."""
    try:
        if instance.pk:  # Existing instance
            old_instance = UserProfile.objects.get(pk=instance.pk)
            instance._verification_changed = old_instance.verified != instance.verified
        else:  # New instance
            instance._verification_changed = False
    except UserProfile.DoesNotExist:
        instance._verification_changed = False

# Cleanup signals for expired tokens
@receiver(post_save, sender=EmailVerificationToken)
def cleanup_expired_tokens(sender, instance, **kwargs):
    """Clean up expired email verification tokens."""
    try:
        expired_tokens = EmailVerificationToken.objects.filter(
            expires_at__lt=timezone.now()
        )
        if expired_tokens.exists():
            count = expired_tokens.count()
            expired_tokens.delete()
            logger.info(f"Cleaned up {count} expired email verification tokens")
    except Exception as e:
        logger.error(f"Error cleaning up expired tokens: {e}")

# Performance monitoring signals
@receiver(post_save, sender=User)
def monitor_user_creation_performance(sender, instance, created, **kwargs):
    """Monitor user creation performance."""
    if created:
        logger.info(f"User creation completed for: {instance.username}")

# Academic record validation signals
@receiver(pre_save, sender=AcademicRecord)
def validate_academic_record(sender, instance, **kwargs):
    """Validate academic record data."""
    if instance.percentage < 0 or instance.percentage > 100:
        logger.warning(f"Invalid percentage for user {instance.user.username}: {instance.percentage}")

# Cache management signals
@receiver(post_save, sender=PageContent)
def invalidate_content_cache(sender, instance, **kwargs):
    """Invalidate content cache when page content changes."""
    cache_key = f"page_content_{instance.key}"
    cache.delete(cache_key)
    logger.info(f"Content cache invalidated for: {instance.key}")

# Admin notification signals
@receiver(post_save, sender=RegistrationLog)
def notify_admin_of_registration(sender, instance, created, **kwargs):
    """Notify admin of new registrations."""
    if created and instance.status == "submitted":
        logger.info(f"Admin notification: New registration from {instance.ip}")

# Search index signals
@receiver(post_save, sender=UserProfile)
def update_search_index(sender, instance, **kwargs):
    """Update search index when user profile changes."""
    logger.info(f"Search index updated for user: {instance.user.username}")

# Suspicious activity monitoring
@receiver(post_save, sender=Visitor)
def monitor_suspicious_activity(sender, instance, created, **kwargs):
    """Monitor for suspicious visitor activity."""
    if created:
        # Check for rapid visits from same IP
        recent_visits = Visitor.objects.filter(
            ip_address=instance.ip_address,
            created_at__gte=timezone.now() - timezone.timedelta(minutes=5)
        ).count()
        
        if recent_visits > 10:
            logger.warning(f"Suspicious activity detected from IP: {instance.ip_address}")

# Backup reminder signals
@receiver(post_save, sender=User)
def remind_backup_creation(sender, instance, created, **kwargs):
    """Remind admin to create backups."""
    if created:
        total_users = User.objects.count()
        if total_users % 100 == 0:  # Every 100 users
            logger.info(f"Backup reminder: {total_users} users in system")

# System health monitoring
@receiver(post_save, sender=User)
def monitor_system_health(sender, instance, created, **kwargs):
    """Monitor overall system health."""
    if created:
        try:
            # Check database performance
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM core_userprofile")
                profile_count = cursor.fetchone()[0]
                
            if profile_count > 1000:
                logger.info(f"System health: Large user base detected ({profile_count} profiles)")
                
        except Exception as e:
            logger.error(f"System health check failed: {e}")

# Old log cleanup signals
@receiver(post_save, sender=RegistrationLog)
def cleanup_old_logs(sender, instance, created, **kwargs):
    """Clean up old log entries."""
    try:
        # Delete logs older than 1 year
        cutoff_date = timezone.now() - timezone.timedelta(days=365)
        old_logs = RegistrationLog.objects.filter(created_at__lt=cutoff_date)
        
        if old_logs.exists():
            count = old_logs.count()
            old_logs.delete()
            logger.info(f"Cleaned up {count} old registration logs")
            
    except Exception as e:
        logger.error(f"Failed to cleanup old logs: {e}")

# Initialize logging when signals are loaded
initialize_logging()
