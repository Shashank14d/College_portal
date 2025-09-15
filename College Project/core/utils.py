"""
Utility functions for email and WhatsApp notifications.

This module contains helper functions for sending verification emails,
mentor assignment notifications, and WhatsApp messages using Twilio API.
"""

import os
import logging
from typing import Optional
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone

# Configure logging
logger = logging.getLogger(__name__)

try:
    from twilio.rest import Client as TwilioClient
    from twilio.base.exceptions import TwilioException
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    logger.warning("Twilio not installed. WhatsApp notifications will be disabled.")


def send_verification_email(to_email: str, full_name: str, verify_link: str) -> bool:
    """
    Send email verification with Terms & Conditions and verification link.
    
    Args:
        to_email: Recipient email address
        full_name: Full name of the user
        verify_link: Signed verification link
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject = "Welcome to College Portal - Verify Your Email"
        
        # Render HTML and text versions
        html_content = render_to_string('emails/verify_email.html', {
            'full_name': full_name,
            'verify_link': verify_link,
            'site_url': settings.SITE_BASE_URL,
        })
        
        text_content = render_to_string('emails/verify_email.txt', {
            'full_name': full_name,
            'verify_link': verify_link,
            'site_url': settings.SITE_BASE_URL,
        })
        
        # Create email with both HTML and text versions
        # Use send_mail to be compatible with test mocks
        result = send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            html_message=html_content,
            fail_silently=False,
        )
        logger.info(f"Verification email sent to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send verification email to {to_email}: {e}")
        return False


def send_mentor_assignment(
    to_email: str, 
    student_name: str, 
    mentor_name: str, 
    portfolio_url: str, 
    whatsapp_link: str
) -> bool:
    """
    Send mentor assignment notification via email.
    
    Args:
        to_email: Student's email address
        student_name: Student's full name
        mentor_name: Assigned mentor's name
        portfolio_url: Mentor's portfolio URL
        whatsapp_link: WhatsApp group invite link
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject = "Mentor Assigned - College Portal"
        
        # Render HTML and text versions
        html_content = render_to_string('emails/mentor_assignment.html', {
            'student_name': student_name,
            'mentor_name': mentor_name,
            'portfolio_url': portfolio_url,
            'whatsapp_link': whatsapp_link,
            'site_url': settings.SITE_BASE_URL,
        })
        
        text_content = render_to_string('emails/mentor_assignment.txt', {
            'student_name': student_name,
            'mentor_name': mentor_name,
            'portfolio_url': portfolio_url,
            'whatsapp_link': whatsapp_link,
            'site_url': settings.SITE_BASE_URL,
        })
        
        # Create email with both HTML and text versions
        result = send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            html_message=html_content,
            fail_silently=False,
        )
        logger.info(f"Mentor assignment email sent to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send mentor assignment email to {to_email}: {e}")
        return False


def send_mentor_notification_to_mentor(mentor, user) -> bool:
    """
    Send notification to mentor about new student assignment.
    
    Args:
        mentor: Mentor instance
        user: User instance (student)
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject = "New Student Assigned to You - College Portal"
        student_name = user.get_full_name() or user.first_name or user.username
        
        text_content = render_to_string('emails/mentor_student_assignment.txt', {
            'mentor_name': mentor.name,
            'student_name': student_name,
            'student_email': user.email,
            'student_phone': user.profile.phone,
        })
        
        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[mentor.email],
            fail_silently=False,
        )
        
        logger.info(f"Notification sent to mentor {mentor.email} for student {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send notification to mentor {mentor.email}: {e}")
        return False


def send_whatsapp_message(to_phone_e164: str, body: str) -> bool:
    """
    Send WhatsApp message using Twilio API with fallback to email.
    
    Args:
        to_phone_e164: Phone number in E.164 format (e.g., +1234567890)
        body: Message content
        
    Returns:
        bool: True if message sent successfully, False otherwise
    """
    if not TWILIO_AVAILABLE:
        logger.warning("Twilio not available. WhatsApp message not sent.")
        return False
        
    try:
        # Get Twilio credentials from environment
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        whatsapp_from = os.getenv('TWILIO_WHATSAPP_FROM')
        
        if not all([account_sid, auth_token, whatsapp_from]):
            logger.warning("Twilio credentials not configured. WhatsApp message not sent.")
            return False
            
        # Initialize Twilio client
        client = TwilioClient(account_sid, auth_token)
        
        # Send WhatsApp message
        message = client.messages.create(
            body=body,
            from_=whatsapp_from,
            to=f'whatsapp:{to_phone_e164}'
        )
        
        logger.info(f"WhatsApp message sent to {to_phone_e164}. SID: {message.sid}")
        return True
        
    except TwilioException as e:
        logger.error(f"Twilio error sending WhatsApp to {to_phone_e164}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending WhatsApp to {to_phone_e164}: {e}")
        return False


def send_mentor_assignment_notifications(user, mentor) -> bool:
    """
    Send both email and WhatsApp notifications for mentor assignment.
    
    Args:
        user: User instance
        mentor: Mentor instance
        
    Returns:
        bool: True if at least one notification sent successfully
    """
    student_name = user.get_full_name() or user.first_name or user.email
    
    # Send email notification
    email_sent = send_mentor_assignment(
        to_email=user.email,
        student_name=student_name,
        mentor_name=mentor.name,
        portfolio_url=mentor.portfolio_url or f"{settings.SITE_BASE_URL}/mentor/{mentor.id}/",
        whatsapp_link=mentor.whatsapp_group_link or ""
    )
    
    # Send WhatsApp notification
    whatsapp_body = f"""Hello {student_name},

Your mentor {mentor.name} has been assigned to you!

Portfolio: {mentor.portfolio_url or 'Not available'}
WhatsApp Group: {mentor.whatsapp_group_link or 'Not available'}

Please contact your mentor for guidance and support.

Best regards,
College Portal Team"""
    
    whatsapp_sent = False
    if user.profile.phone:
        # Format phone number for WhatsApp (basic E.164 formatting)
        phone = user.profile.phone.strip()
        if not phone.startswith('+'):
            # Assume Indian number if no country code
            if phone.startswith('0'):
                phone = '+91' + phone[1:]
            elif len(phone) == 10:
                phone = '+91' + phone
            else:
                phone = '+' + phone
                
        whatsapp_sent = send_whatsapp_message(phone, whatsapp_body)
    
    return email_sent or whatsapp_sent


def send_welcome_email(user) -> bool:
    """
    Send welcome email to newly registered user.
    
    Args:
        user: User instance
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject = "Welcome to College Portal"
        full_name = user.get_full_name() or user.first_name or user.username
        
        message = f"""Hello {full_name},

Welcome to the College Portal! Your account has been created successfully.

Please check your email for verification instructions to activate your account.

Once verified, you'll be able to:
- Access academic programs and information
- Request mentor assignment
- View your academic records
- Contact college administration

Best regards,
College Portal Team"""
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False
        )
        
        logger.info(f"Welcome email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {e}")
        return False


def send_verification_confirmation(user) -> bool:
    """
    Send email confirmation when user's email is verified.
    
    Args:
        user: User instance
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject = "Account Verified - College Portal"
        full_name = user.get_full_name() or user.first_name or user.username
        
        message = f"""Hello {full_name},

Congratulations! Your account has been verified successfully.

You can now access all features of the College Portal:
- View academic programs
- Request mentor assignment
- Access your profile and academic records
- Contact college administration

Login at: {settings.SITE_BASE_URL}/login/

Best regards,
College Portal Team"""
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False
        )
        
        logger.info(f"Verification confirmation email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send verification confirmation to {user.email}: {e}")
        return False


def format_phone_for_whatsapp(phone: str) -> str:
    """
    Format phone number for WhatsApp E.164 format.
    
    Args:
        phone: Raw phone number string
        
    Returns:
        str: Formatted phone number in E.164 format
    """
    if not phone:
        return ""
        
    # Remove all non-digit characters except +
    cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')
    
    # If it starts with +, return as is
    if cleaned.startswith('+'):
        return cleaned
    
    # Handle Indian numbers
    if cleaned.startswith('0') and len(cleaned) == 11:
        return '+91' + cleaned[1:]
    elif len(cleaned) == 10:
        return '+91' + cleaned
    
    # If it's already 12 digits, assume it has country code
    if len(cleaned) == 12:
        return '+' + cleaned
    
    # Default: add + if not present
    return '+' + cleaned if not cleaned.startswith('+') else cleaned


def get_pincode_info(pincode: str) -> dict:
    """
    Fetch city and state information from PINCODE using external API.
    
    Args:
        pincode: 6-digit PINCODE
        
    Returns:
        dict: City and state information or empty dict if not found
    """
    import requests
    
    try:
        response = requests.get(f"https://api.postalpincode.in/pincode/{pincode}", timeout=5)
        data = response.json()
        
        if data and data[0].get('Status') == 'Success':
            post_office = data[0].get('PostOffice', [{}])[0]
            return {
                'city': post_office.get('District', ''),
                'state': post_office.get('State', ''),
                'country': post_office.get('Country', 'India')
            }
    except Exception as e:
        logger.error(f"Failed to fetch pincode info for {pincode}: {e}")
    
    return {}


def log_notification_sent(notification_type: str, recipient: str, status: str, details: str = "") -> None:
    """
    Log notification sending attempts for monitoring and debugging.
    
    Args:
        notification_type: Type of notification (email, whatsapp, etc.)
        recipient: Recipient identifier (email, phone, etc.)
        status: Success/failure status
        details: Additional details about the notification
    """
    logger.info(f"Notification {notification_type} to {recipient}: {status}. {details}")


def cleanup_expired_tokens() -> int:
    """
    Clean up expired email verification tokens.
    
    Returns:
        int: Number of tokens deleted
    """
    from .models import EmailVerificationToken
    
    try:
        expired_tokens = EmailVerificationToken.objects.filter(
            expires_at__lt=timezone.now()
        )
        count = expired_tokens.count()
        expired_tokens.delete()
        
        if count > 0:
            logger.info(f"Cleaned up {count} expired email verification tokens")
        
        return count
    except Exception as e:
        logger.error(f"Error cleaning up expired tokens: {e}")
        return 0









