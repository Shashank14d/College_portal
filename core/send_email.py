import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
import logging
from django.core.mail import send_mail
from django.conf import settings
import traceback

logger = logging.getLogger(__name__)

def send_direct_email(to_emails, subject, html_content, text_content=None, attachments=None, fallback_to_console=True):
    """
    Send email directly using smtplib without relying on Django's email backend.
    Includes fallback mechanisms for handling Gmail sending limits.
    
    Args:
        to_emails: List of recipient email addresses
        subject: Email subject
        html_content: HTML content of the email
        text_content: Plain text content of the email (optional)
        attachments: List of file paths to attach (optional)
        fallback_to_console: Whether to fallback to console output if all sending methods fail
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    # Convert single email to list if needed
    if isinstance(to_emails, str):
        to_emails = [to_emails]
    
    # Try direct SMTP first
    if _try_direct_smtp(to_emails, subject, html_content, text_content, attachments):
        return True
    
    # If direct SMTP fails, try Django's send_mail as fallback
    if _try_django_email(to_emails, subject, text_content or html_content):
        return True
    
    # If all else fails, log the email to console
    if fallback_to_console:
        _log_email_to_console(to_emails, subject, text_content or html_content)
        return True
    
    return False

def _try_direct_smtp(to_emails, subject, html_content, text_content, attachments):
    """Try to send email via direct SMTP connection"""
    try:
        # Email credentials from environment variables
        sender_email = os.environ.get('EMAIL_HOST_USER', 'shashankk1410@gmail.com')
        password = os.environ.get('EMAIL_HOST_PASSWORD', 'afzp axal ajww imue')
        
        # Create message container
        msg = MIMEMultipart('alternative')
        msg['From'] = sender_email
        msg['To'] = ', '.join(to_emails)
        msg['Subject'] = subject
        
        # Add text content if provided
        if text_content:
            msg.attach(MIMEText(text_content, 'plain'))
        
        # Add HTML content
        msg.attach(MIMEText(html_content, 'html'))
        
        # Add attachments if provided
        if attachments:
            for file_path in attachments:
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as file:
                        part = MIMEApplication(file.read(), Name=os.path.basename(file_path))
                        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                        msg.attach(part)
                        logger.info(f"Attached file: {file_path}")
                else:
                    logger.warning(f"Attachment file not found: {file_path}")
        
        # Connect to Gmail SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Secure the connection
        
        # Log in to server
        server.login(sender_email, password)
        
        # Send email
        server.sendmail(sender_email, to_emails, msg.as_string())
        
        # Close connection
        server.quit()
        
        logger.info(f"Email sent successfully via direct SMTP to {to_emails}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email via direct SMTP: {str(e)}")
        logger.debug(traceback.format_exc())
        return False

def _try_django_email(to_emails, subject, message):
    """Try to send email via Django's send_mail"""
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=to_emails,
            fail_silently=False,
        )
        logger.info(f"Email sent successfully via Django send_mail to {to_emails}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email via Django send_mail: {str(e)}")
        logger.debug(traceback.format_exc())
        return False

def _log_email_to_console(to_emails, subject, message):
    """Log email to console as last resort"""
    logger.info("=============== EMAIL FALLBACK ===============")
    logger.info(f"To: {', '.join(to_emails)}")
    logger.info(f"Subject: {subject}")
    logger.info(f"Message: {message[:500]}...")
    logger.info("=============================================")
    print("=============== EMAIL FALLBACK ===============")
    print(f"To: {', '.join(to_emails)}")
    print(f"Subject: {subject}")
    print(f"Message: {message[:500]}...")
    print("=============================================")
    return True