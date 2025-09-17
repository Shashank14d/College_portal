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
    if not to_email:
        logger.error("Cannot send verification email: recipient email is empty")
        return False
        
    try:
        subject = "Welcome to College Portal - Verify Your Email"
        
        # Render HTML and text versions
        html_content = render_to_string('emails/verify_email.html', {
            'full_name': full_name or "User",
            'verify_link': verify_link,
            'site_url': settings.SITE_BASE_URL,
            'current_year': timezone.now().year,
        })
        
        text_content = render_to_string('emails/verify_email.txt', {
            'full_name': full_name or "User",
            'verify_link': verify_link,
            'site_url': settings.SITE_BASE_URL,
            'current_year': timezone.now().year,
        })
        
        # Create email with both HTML and text versions
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email],
        )
        msg.attach_alternative(html_content, "text/html")
        
        # Send email
        result = msg.send(fail_silently=True)
        if result:
            logger.info(f"Verification email sent to {to_email}")
            return True
        else:
            logger.error(f"Failed to send verification email to {to_email}")
            return False
        
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
    if not to_email:
        logger.error("Cannot send mentor assignment email: recipient email is empty")
        return False
        
    try:
        subject = "Mentor Assigned - College Portal"
        
        # Prepare context with fallback values for optional parameters
        context = {
            'student_name': student_name or "Student",
            'mentor_name': mentor_name or "Your Mentor",
            'portfolio_url': portfolio_url or "#",
            'whatsapp_link': whatsapp_link or "#",
            'site_url': getattr(settings, 'SITE_BASE_URL', 'https://college-portal.example.com'),
        }
        
        # Render HTML and text versions
        html_content = render_to_string('emails/mentor_assignment.html', context)
        text_content = render_to_string('emails/mentor_assignment.txt', context)
        
        # Send email with both HTML and text versions
        result = send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            html_message=html_content,
            fail_silently=True,  # Don't raise exceptions that would break the flow
        )
        
        if result:
            logger.info(f"Mentor assignment email sent to {to_email}")
            return True
        else:
            logger.warning(f"Failed to send mentor assignment email to {to_email}")
            return False
        
    except Exception as e:
        logger.error(f"Failed to send mentor assignment email to {to_email}: {e}")
        return False


def send_mentor_notification_to_mentor(mentor, student_user, student_profile=None) -> bool:
    """
    Send notification to mentor about new student assignment.
    
    Args:
        mentor: Mentor instance
        student_user: User instance of the student
        student_profile: UserProfile instance of the student (optional)
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    if not mentor or not hasattr(mentor, 'email') or not mentor.email:
        logger.error("Cannot send mentor notification: mentor email is invalid")
        return False
        
    if not student_user or not hasattr(student_user, 'email'):
        logger.error("Cannot send mentor notification: student information is invalid")
        return False
        
    try:
        subject = "New Student Assignment - College Portal"
        
        # Get student information with fallbacks
        student_name = student_user.get_full_name() or student_user.first_name or student_user.username
        
        # Get student phone safely
        student_phone = "Not provided"
        if student_profile and hasattr(student_profile, 'phone'):
            student_phone = student_profile.phone
        elif hasattr(student_user, 'profile') and hasattr(student_user.profile, 'phone'):
            student_phone = student_user.profile.phone
            
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #67e8f9; color: #fff; padding: 10px; text-align: center; }}
                .content {{ padding: 20px; }}
                .student-info {{ background-color: #f5f5f5; padding: 15px; margin: 15px 0; border-left: 4px solid #67e8f9; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>New Student Assignment</h2>
                </div>
                <div class="content">
                    <p>Hello {mentor.name},</p>
                    <p>You have been assigned a new student in the College Portal:</p>
                    
                    <div class="student-info">
                        <p><strong>Student:</strong> {student_name}</p>
                        <p><strong>Email:</strong> {student_user.email}</p>
                        <p><strong>Phone:</strong> {student_phone}</p>
                    </div>
                    
                    <p>Please reach out to the student to introduce yourself and provide guidance.</p>
                    <p>Best regards,<br>College Portal Team</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""Hello {mentor.name},

You have been assigned a new student in the College Portal:

Student: {student_name}
Email: {student_user.email}
Phone: {student_phone}

Please reach out to the student to introduce yourself and provide guidance.

Best regards,
College Portal Team"""
        
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[mentor.email],
        )
        msg.attach_alternative(html_content, "text/html")
        
        result = msg.send(fail_silently=True)
        
        # Also send a copy to admin
        try:
            admin_email = settings.ADMIN_EMAIL if hasattr(settings, 'ADMIN_EMAIL') else settings.DEFAULT_FROM_EMAIL
            if admin_email and admin_email != mentor.email:
                admin_msg = EmailMessage(
                    subject=f"Mentor Assignment: {student_name} to {mentor.name}",
                    body=f"A student has been assigned to a mentor:\nStudent: {student_name}\nMentor: {mentor.name}\nMentor Email: {mentor.email}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[admin_email],
                )
                admin_msg.send(fail_silently=True)
                logger.info(f"Admin notification sent to {admin_email} about mentor assignment")
        except Exception as e:
            logger.error(f"Failed to send admin notification about mentor assignment: {e}")
        
        if result:
            logger.info(f"Mentor notification sent to {mentor.email} about student {student_user.email}")
            return True
        else:
            logger.error(f"Failed to send mentor notification to {mentor.email}")
            return False
        
    except Exception as e:
        logger.error(f"Failed to send mentor notification to {mentor.email if mentor else 'unknown'}: {e}")
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
    
    # Ensure portfolio and WhatsApp links are available
    portfolio_url = mentor.portfolio_url
    if not portfolio_url:
        portfolio_url = f"{settings.SITE_BASE_URL}/mentor/{mentor.id}/"
    
    whatsapp_link = mentor.whatsapp_group_link
    if not whatsapp_link:
        whatsapp_link = "https://chat.whatsapp.com/default-group"
    
    # Send email notification with detailed mentor information
    email_sent = send_mentor_assignment(
        to_email=user.email,
        student_name=student_name,
        mentor_name=mentor.name,
        portfolio_url=portfolio_url,
        whatsapp_link=whatsapp_link
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


def send_registration_email(user, full_name: str, portal_link: str, brochure_path: str = None) -> bool:
    """
    Send a single consolidated registration email that contains a welcome message,
    a prominent button to go to the portal (or verification/login), and optionally
    attaches a brochure PDF.

    Args:
        user: User instance
        full_name: Full name to address in the email
        portal_link: URL the button should point to (login or portal)
        brochure_path: Optional filesystem path to a PDF to attach

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    if not user or not hasattr(user, 'email') or not user.email:
        logger.error("Cannot send registration email: user or email is invalid")
        return False
        
    try:
        subject = "Welcome to College Portal - Get Started"
        html_content = render_to_string('emails/registration_email.html', {
            'full_name': full_name or "User",
            'portal_link': portal_link or f"{settings.SITE_BASE_URL}/login/",
            'site_url': settings.SITE_BASE_URL,
            'current_year': timezone.now().year,
        })
        text_content = render_to_string('emails/registration_email.txt', {
            'full_name': full_name or "User",
            'portal_link': portal_link or f"{settings.SITE_BASE_URL}/login/",
            'site_url': settings.SITE_BASE_URL,
            'current_year': timezone.now().year,
        })

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        msg.attach_alternative(html_content, "text/html")

        # Default brochure path if not provided
        if not brochure_path:
            brochure_path = os.path.join(settings.BASE_DIR, 'static', 'brochures', 'mca_brochure.pdf')
            
        # Attach brochure if exists
        if os.path.exists(brochure_path):
            try:
                with open(brochure_path, 'rb') as f:
                    msg.attach(os.path.basename(brochure_path), f.read(), 'application/pdf')
                    logger.info(f"Attached brochure to email for {user.email}")
            except Exception as e:
                logger.warning(f"Failed to attach brochure {brochure_path}: {e}")
        else:
            logger.warning(f"Brochure not found at {brochure_path}")

        # Send to user with real-time delivery
        result = msg.send(fail_silently=False)
        
        # Also send a copy to admin
        try:
            admin_email = settings.ADMIN_EMAIL if hasattr(settings, 'ADMIN_EMAIL') else settings.DEFAULT_FROM_EMAIL
            if admin_email and admin_email != user.email:
                admin_msg = EmailMultiAlternatives(
                    subject=f"New User Registration: {full_name}",
                    body=f"A new user has registered:\nName: {full_name}\nEmail: {user.email}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[admin_email],
                )
                admin_msg.send(fail_silently=True)
                logger.info(f"Admin notification sent to {admin_email} about new user {user.email}")
        except Exception as e:
            logger.error(f"Failed to send admin notification about {user.email}: {e}")
        
        if result:
            logger.info(f"Registration email sent to {user.email}")
            return True
        else:
            logger.error(f"Failed to send registration email to {user.email}")
            return False

    except Exception as e:
        logger.error(f"Failed to send registration email to {user.email}: {e}")
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









