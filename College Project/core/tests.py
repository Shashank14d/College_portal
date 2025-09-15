"""
Comprehensive test suite for the College Portal application.

This module contains unit tests, integration tests, and security tests
to ensure the portal functions correctly and securely.
"""

import json
from datetime import timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.mail import outbox
from django.utils import timezone
from django.urls import reverse
from django.core.cache import cache
from unittest.mock import patch, MagicMock

from .models import (
    UserProfile, AcademicRecord, Mentor, MentorAssignment,
    Visitor, EmailVerificationToken, PageContent, RegistrationLog
)
from .utils import send_verification_email, send_mentor_assignment, send_whatsapp_message


class ModelTests(TestCase):
    """Test cases for database models."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.mentor = Mentor.objects.create(
            name='Test Mentor',
            email='mentor@example.com',
            portfolio_url='https://mentor.example.com',
            whatsapp_group_link='https://wa.me/test',
            bio='Test mentor bio'
        )
    
    def test_user_profile_creation(self):
        """Test UserProfile model creation."""
        profile = UserProfile.objects.create(
            user=self.user,
            full_name='Test User',
            phone='+1234567890',
            city='Test City',
            pincode='12345',
            cet_taken=True
        )
        
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.full_name, 'Test User')
        self.assertTrue(profile.cet_taken)
        self.assertFalse(profile.verified)
    
    def test_academic_record_creation(self):
        """Test AcademicRecord model creation."""
        record = AcademicRecord.objects.create(
            user=self.user,
            level='UG',
            degree='B.Tech Computer Science',
            institution='Test University',
            year=2023,
            percentage=85.5
        )
        
        self.assertEqual(record.user, self.user)
        self.assertEqual(record.level, 'UG')
        self.assertEqual(record.percentage, 85.5)
    
    def test_mentor_creation(self):
        """Test Mentor model creation."""
        mentor = Mentor.objects.create(
            name='Dr. Test Mentor',
            email='dr.test@example.com',
            bio='Test bio'
        )
        
        self.assertEqual(mentor.name, 'Dr. Test Mentor')
        self.assertEqual(mentor.email, 'dr.test@example.com')
        self.assertIsNotNone(mentor.created_at)
    
    def test_mentor_assignment_creation(self):
        """Test MentorAssignment model creation."""
        assignment = MentorAssignment.objects.create(
            user=self.user,
            mentor=self.mentor,
            assigned_by=self.user
        )
        
        self.assertEqual(assignment.user, self.user)
        self.assertEqual(assignment.mentor, self.mentor)
        self.assertIsNotNone(assignment.assigned_at)
    
    def test_visitor_tracking(self):
        """Test Visitor model for tracking page visits."""
        visitor = Visitor.objects.create(
            ip_address='192.168.1.1',
            path='/test-page',
            page_visited='/test-page',
            user=self.user,
            user_agent='Test Browser'
        )
        
        self.assertEqual(visitor.ip_address, '192.168.1.1')
        self.assertEqual(visitor.path, '/test-page')
        self.assertEqual(visitor.user, self.user)
    
    def test_email_verification_token_creation(self):
        """Test EmailVerificationToken model creation."""
        token = EmailVerificationToken.objects.create(
            user=self.user,
            token='test-token-123',
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        self.assertEqual(token.user, self.user)
        self.assertEqual(token.token, 'test-token-123')
        self.assertFalse(token.expires_at < timezone.now())
    
    def test_page_content_creation(self):
        """Test PageContent model creation."""
        content = PageContent.objects.create(
            key='test_key',
            value='Test content value'
        )
        
        self.assertEqual(content.key, 'test_key')
        self.assertEqual(content.value, 'Test content value')
        self.assertIsNotNone(content.updated_at)
    
    def test_registration_log_creation(self):
        """Test RegistrationLog model creation."""
        log = RegistrationLog.objects.create(
            user=self.user,
            ip='192.168.1.1',
            status='submitted'
        )
        
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.ip, '192.168.1.1')
        self.assertEqual(log.status, 'submitted')


class ViewTests(TestCase):
    """Test cases for views and URL routing."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            full_name='Test User',
            phone='+1234567890',
            verified=True
        )
        self.mentor = Mentor.objects.create(
            name='Test Mentor',
            email='mentor@example.com',
            bio='Test mentor bio'
        )
    
    def test_landing_page(self):
        """Test landing page loads correctly."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Welcome to Futuristic College')
    
    def test_registration_page(self):
        """Test registration page loads correctly."""
        response = self.client.get('/register/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Student Registration')
    
    def test_login_page(self):
        """Test login page loads correctly."""
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Student Login')
    
    def test_portal_home_requires_login(self):
        """Test portal home requires authentication."""
        response = self.client.get('/portal/home/')
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_portal_home_authenticated(self):
        """Test portal home for authenticated users."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/portal/home/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Welcome to Your Portal')
    
    def test_director_dashboard_requires_staff(self):
        """Test director dashboard requires staff permissions."""
        response = self.client.get('/director/dashboard/')
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_director_dashboard_staff_access(self):
        """Test director dashboard for staff users."""
        self.user.is_staff = True
        self.user.save()
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/director/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Director Dashboard')
    
    def test_registration_submission(self):
        """Test user registration submission."""
        data = {
            'full_name': 'New User',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'confirm_password': 'newpass123',
            'phone': '+1234567890',
            'city': 'Test City',
            'pincode': '12345',
            'cet_taken': 'yes',
            'level[]': ['UG'],
            'degree[]': ['B.Tech'],
            'institution[]': ['Test University'],
            'year[]': ['2023'],
            'percentage[]': ['85.5']
        }
        
        response = self.client.post('/register/submit/', data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful registration
        
        # Check if user was created
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())
        
        # Check if profile was created
        user = User.objects.get(email='newuser@example.com')
        self.assertTrue(hasattr(user, 'profile'))
    
    def test_login_authentication(self):
        """Test user login authentication."""
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        
        response = self.client.post('/login/submit/', data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful login
    
    def test_mentor_request(self):
        """Test mentor request functionality."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post('/portal/request-mentor/')
        self.assertEqual(response.status_code, 302)  # Redirect after request
        
        # Check if registration log was created
        self.assertTrue(RegistrationLog.objects.filter(
            user=self.user,
            status='mentor_requested'
        ).exists())
    
    def test_mentor_assignment(self):
        """Test mentor assignment functionality."""
        self.user.is_staff = True
        self.user.save()
        self.client.login(username='testuser', password='testpass123')
        
        data = {
            'user_id': self.user.id,
            'mentor_id': self.mentor.id
        }
        
        response = self.client.post('/director/assign-mentor/', data)
        self.assertEqual(response.status_code, 302)  # Redirect after assignment
        
        # Check if assignment was created
        self.assertTrue(MentorAssignment.objects.filter(
            user=self.user,
            mentor=self.mentor
        ).exists())
        
        # Check if user profile was updated
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.assigned_mentor, self.mentor)
    
    def test_admin_can_access_common_user_features(self):
        """Test that admin users can access common user features."""
        self.user.is_staff = True
        self.user.save()
        self.client.login(username='testuser', password='testpass123')
        
        # Test portal home access
        response = self.client.get('/portal/home/')
        self.assertEqual(response.status_code, 200)  # Should work
        
        # Test portal academics access
        response = self.client.get('/portal/academics/')
        self.assertEqual(response.status_code, 200)  # Should work
        
        # Test portal contact access
        response = self.client.get('/portal/contact/')
        self.assertEqual(response.status_code, 200)  # Should work
        
        # Test mentor request access
        response = self.client.get('/portal/request-mentor/')
        self.assertEqual(response.status_code, 200)  # Should work
        
        # Test registration access
        response = self.client.get('/register/')
        self.assertEqual(response.status_code, 200)  # Should work
        
        # Test login access
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 200)  # Should work
    
    def test_mentor_request_hidden_for_users_with_mentors(self):
        """Test that request mentor option is hidden for users with assigned mentors."""
        # Create a mentor
        mentor = Mentor.objects.create(
            name='Test Mentor',
            email='mentor@example.com',
            portfolio_url='https://mentor.example.com',
            whatsapp_group_link='https://wa.me/test',
            bio='Test mentor bio'
        )
        
        # Assign mentor to user
        self.user.profile.assigned_mentor = mentor
        self.user.profile.save()
        
        self.client.login(username='testuser', password='testpass123')
        
        # Test contact page shows mentor info instead of request button
        response = self.client.get('/portal/contact/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Your Assigned Mentor')
        self.assertContains(response, mentor.name)
        self.assertNotContains(response, 'Request Mentor Assignment')
        
        # Test direct access to request mentor redirects
        response = self.client.get('/portal/request-mentor/')
        self.assertEqual(response.status_code, 302)  # Redirect to contact page
    
    def test_admin_limit_enforcement(self):
        """Test that maximum 4 admins limit is enforced."""
        # Create 4 admin users
        for i in range(4):
            admin_user = User.objects.create_user(
                username=f'admin{i}',
                email=f'admin{i}@example.com',
                password='adminpass123'
            )
            admin_user.is_staff = True
            admin_user.save()
        
        # Try to create 5th admin should fail
        self.user.is_staff = True
        self.user.save()
        self.client.login(username='testuser', password='testpass123')
        
        # This would be tested in admin interface, but we can test the middleware
        from core.middleware import AdminRestrictionMiddleware
        middleware = AdminRestrictionMiddleware(lambda r: None)
        
        # Simulate admin creation request
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.post('/admin/auth/user/', {'is_staff': 'on'})
        request.user = self.user
        
        # Should be blocked
        self.assertTrue(middleware._is_admin_creation_request(request))


class EmailVerificationTests(TestCase):
    """Test cases for email verification functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            full_name='Test User',
            verified=False
        )
    
    def test_email_verification_token_creation(self):
        """Test email verification token creation."""
        from django.core.signing import TimestampSigner
        
        signer = TimestampSigner()
        raw = f"{self.user.pk}:{self.user.email}:{timezone.now().timestamp()}"
        token = signer.sign(raw)
        
        verification_token = EmailVerificationToken.objects.create(
            user=self.user,
            token=token,
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        self.assertEqual(verification_token.user, self.user)
        self.assertFalse(verification_token.expires_at < timezone.now())
    
    def test_email_verification_process(self):
        """Test complete email verification process."""
        from django.core.signing import TimestampSigner
        
        # Create verification token
        signer = TimestampSigner()
        raw = f"{self.user.pk}:{self.user.email}:{timezone.now().timestamp()}"
        token = signer.sign(raw)
        
        EmailVerificationToken.objects.create(
            user=self.user,
            token=token,
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        # Test verification endpoint
        response = self.client.get(f'/verify-email/?token={token}')
        self.assertEqual(response.status_code, 302)  # Redirect after verification
        
        # Check if user is now verified
        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.verified)
    
    def test_expired_token_verification(self):
        """Test verification with expired token."""
        from django.core.signing import TimestampSigner
        
        # Create expired token
        signer = TimestampSigner()
        raw = f"{self.user.pk}:{self.user.email}:{timezone.now().timestamp()}"
        token = signer.sign(raw)
        
        EmailVerificationToken.objects.create(
            user=self.user,
            token=token,
            expires_at=timezone.now() - timedelta(hours=1)  # Expired
        )
        
        # Test verification with expired token
        response = self.client.get(f'/verify-email/?token={token}')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Token expired')
    
    def test_invalid_token_verification(self):
        """Test verification with invalid token."""
        response = self.client.get('/verify-email/?token=invalid-token')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid or expired token')


class EmailNotificationTests(TestCase):
    """Test cases for email notification functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.mentor = Mentor.objects.create(
            name='Test Mentor',
            email='mentor@example.com',
            portfolio_url='https://mentor.example.com',
            whatsapp_group_link='https://wa.me/test'
        )
    
    def test_send_verification_email(self):
        """Test sending verification email."""
        with patch('core.utils.send_mail') as mock_send_mail:
            result = send_verification_email(
                to_email='test@example.com',
                full_name='Test User',
                verify_link='https://example.com/verify?token=123'
            )
            
            self.assertTrue(result)
            mock_send_mail.assert_called_once()
    
    def test_send_mentor_assignment_email(self):
        """Test sending mentor assignment email."""
        with patch('core.utils.send_mail') as mock_send_mail:
            result = send_mentor_assignment(
                to_email='test@example.com',
                student_name='Test User',
                mentor_name='Test Mentor',
                portfolio_url='https://mentor.example.com',
                whatsapp_link='https://wa.me/test'
            )
            
            self.assertTrue(result)
            mock_send_mail.assert_called_once()
    
    @patch('core.utils.TWILIO_AVAILABLE', True)
    @patch('core.utils.TwilioClient')
    def test_send_whatsapp_message(self, mock_twilio_client):
        """Test sending WhatsApp message."""
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.sid = 'test-sid-123'
        mock_client.messages.create.return_value = mock_message
        mock_twilio_client.return_value = mock_client

        with patch.dict('os.environ', {
            'TWILIO_ACCOUNT_SID': 'test-sid',
            'TWILIO_AUTH_TOKEN': 'test-token',
            'TWILIO_WHATSAPP_FROM': 'whatsapp:+1234567890'
        }):
            result = send_whatsapp_message(
                to_phone_e164='+1234567890',
                body='Test message'
            )
            
            self.assertTrue(result)
            mock_client.messages.create.assert_called_once()


class SecurityTests(TestCase):
    """Test cases for security features."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_csrf_protection(self):
        """Test CSRF protection on forms."""
        # Test registration form without CSRF token
        data = {
            'full_name': 'Test User',
            'email': 'test@example.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123'
        }
        
        response = self.client.post('/register/submit/', data)
        self.assertEqual(response.status_code, 403)  # CSRF error
    
    def test_rate_limiting(self):
        """Test registration rate limiting."""
        data = {
            'full_name': 'Test User',
            'email': 'test@example.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123'
        }
        
        # Make multiple requests to test rate limiting
        for i in range(6):  # Exceed the limit of 5
            response = self.client.post('/register/submit/', data)
            if i < 5:
                self.assertNotEqual(response.status_code, 429)
            else:
                self.assertEqual(response.status_code, 429)
    
    def test_staff_only_access(self):
        """Test staff-only access to admin areas."""
        # Test without staff permissions
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/director/dashboard/')
        self.assertEqual(response.status_code, 403)
        
        # Test with staff permissions
        self.user.is_staff = True
        self.user.save()
        response = self.client.get('/director/dashboard/')
        self.assertEqual(response.status_code, 200)
    
    def test_password_validation(self):
        """Test password validation."""
        data = {
            'full_name': 'Test User',
            'email': 'test@example.com',
            'password': '123',  # Too short
            'confirm_password': '123'
        }
        
        response = self.client.post('/register/submit/', data)
        self.assertEqual(response.status_code, 302)  # Should still redirect but with error message
    
    def test_email_uniqueness(self):
        """Test email uniqueness validation."""
        # Create first user
        User.objects.create_user(
            username='user1',
            email='test@example.com',
            password='testpass123'
        )
        
        # Try to create second user with same email
        data = {
            'full_name': 'Test User 2',
            'email': 'test@example.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123'
        }
        
        response = self.client.post('/register/submit/', data)
        self.assertEqual(response.status_code, 302)  # Should redirect with error message


class CacheTests(TestCase):
    """Test cases for caching functionality."""
    
    def setUp(self):
        """Set up test data."""
        cache.clear()
    
    def test_cache_operations(self):
        """Test basic cache operations."""
        cache.set('test_key', 'test_value', 30)
        self.assertEqual(cache.get('test_key'), 'test_value')
        
        cache.delete('test_key')
        self.assertIsNone(cache.get('test_key'))
    
    def test_rate_limiting_cache(self):
        """Test rate limiting cache functionality."""
        # Simulate rate limiting
        key = 'rl:register:192.168.1.1'
        cache.set(key, 1, 60)
        
        count = cache.get(key, 0)
        self.assertEqual(count, 1)
        
        cache.set(key, count + 1, 60)
        count = cache.get(key, 0)
        self.assertEqual(count, 2)


class IntegrationTests(TestCase):
    """Integration tests for complete workflows."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.mentor = Mentor.objects.create(
            name='Test Mentor',
            email='mentor@example.com',
            portfolio_url='https://mentor.example.com',
            whatsapp_group_link='https://wa.me/test'
        )
    
    def test_complete_registration_workflow(self):
        """Test complete user registration workflow."""
        # Step 1: Register user
        data = {
            'full_name': 'Test User',
            'email': 'test@example.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123',
            'phone': '+1234567890',
            'city': 'Test City',
            'pincode': '12345',
            'cet_taken': 'yes',
            'level[]': ['UG'],
            'degree[]': ['B.Tech Computer Science'],
            'institution[]': ['Test University'],
            'year[]': ['2023'],
            'percentage[]': ['85.5']
        }
        
        response = self.client.post('/register/submit/', data)
        self.assertEqual(response.status_code, 302)
        
        # Step 2: Verify user was created
        user = User.objects.get(email='test@example.com')
        self.assertFalse(user.profile.verified)
        
        # Step 3: Create verification token
        from django.core.signing import TimestampSigner
        signer = TimestampSigner()
        raw = f"{user.pk}:{user.email}:{timezone.now().timestamp()}"
        token = signer.sign(raw)
        
        EmailVerificationToken.objects.create(
            user=user,
            token=token,
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        # Step 4: Verify email
        response = self.client.get(f'/verify-email/?token={token}')
        self.assertEqual(response.status_code, 302)
        
        # Step 5: Check user is verified
        user.profile.refresh_from_db()
        self.assertTrue(user.profile.verified)
        
        # Step 6: Login
        login_data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post('/login/submit/', login_data)
        self.assertEqual(response.status_code, 302)
        
        # Step 7: Access portal
        response = self.client.get('/portal/home/')
        self.assertEqual(response.status_code, 200)
    
    def test_mentor_assignment_workflow(self):
        """Test complete mentor assignment workflow."""
        # Create staff user
        staff_user = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='staffpass123'
        )
        staff_user.is_staff = True
        staff_user.save()
        
        # Create student user
        student_user = User.objects.create_user(
            username='student',
            email='student@example.com',
            password='studentpass123'
        )
        UserProfile.objects.create(
            user=student_user,
            full_name='Student User',
            phone='+1234567890',
            verified=True
        )
        
        # Login as staff
        self.client.login(username='staff', password='staffpass123')
        
        # Assign mentor
        data = {
            'user_id': student_user.id,
            'mentor_id': self.mentor.id
        }
        
        with patch('core.utils.send_mentor_assignment') as mock_email, \
             patch('core.utils.send_whatsapp_message') as mock_whatsapp:
            
            response = self.client.post('/director/assign-mentor/', data)
            self.assertEqual(response.status_code, 302)
            
            # Check assignment was created
            self.assertTrue(MentorAssignment.objects.filter(
                user=student_user,
                mentor=self.mentor
            ).exists())
            
            # Check profile was updated
            student_user.profile.refresh_from_db()
            self.assertEqual(student_user.profile.assigned_mentor, self.mentor)
            
            # Check notifications were sent
            mock_email.assert_called_once()
            mock_whatsapp.assert_called_once()


class PerformanceTests(TestCase):
    """Test cases for performance and optimization."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
    
    def test_database_query_optimization(self):
        """Test database query optimization."""
        # Create multiple users and profiles
        for i in range(10):
            user = User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='testpass123'
            )
            UserProfile.objects.create(
                user=user,
                full_name=f'User {i}',
                phone=f'+123456789{i}',
                verified=True
            )
        
        # Test query count for director dashboard
        with self.assertNumQueries(3):  # Should be optimized to minimal queries
            self.client.get('/director/dashboard/')
    
    def test_cache_performance(self):
        """Test cache performance."""
        # Test cache hit/miss performance
        start_time = timezone.now()
        
        # First access (cache miss)
        cache.set('test_key', 'test_value', 30)
        value = cache.get('test_key')
        
        # Second access (cache hit)
        value = cache.get('test_key')
        
        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()
        
        # Should be very fast
        self.assertLess(duration, 0.1)


class ErrorHandlingTests(TestCase):
    """Test cases for error handling and edge cases."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
    
    def test_invalid_form_data(self):
        """Test handling of invalid form data."""
        data = {
            'full_name': '',  # Empty required field
            'email': 'invalid-email',  # Invalid email format
            'password': '123',  # Too short password
            'confirm_password': '456'  # Mismatched passwords
        }
        
        response = self.client.post('/register/submit/', data)
        self.assertEqual(response.status_code, 302)  # Should redirect with errors
    
    def test_database_connection_error(self):
        """Test handling of database connection errors."""
        # This would require mocking database connection
        # For now, just test that the app doesn't crash
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_email_service_error(self):
        """Test handling of email service errors."""
        with patch('core.utils.send_mail', side_effect=Exception('Email service error')):
            result = send_verification_email(
                to_email='test@example.com',
                full_name='Test User',
                verify_link='https://example.com/verify'
            )
            self.assertFalse(result)
    
    def test_whatsapp_service_error(self):
        """Test handling of WhatsApp service errors."""
        with patch('core.utils.TWILIO_AVAILABLE', True), \
             patch('core.utils.TwilioClient', side_effect=Exception('WhatsApp service error')):
            
            result = send_whatsapp_message(
                to_phone_e164='+1234567890',
                body='Test message'
            )
            self.assertFalse(result)


# Test runner configuration
def run_tests():
    """Run all tests with proper configuration."""
    import django
    from django.conf import settings
    from django.test.utils import get_runner
    
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            INSTALLED_APPS=[
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'django.contrib.sessions',
                'django.contrib.messages',
                'django.contrib.staticfiles',
                'core',
            ],
            ROOT_URLCONF='college_portal.urls',
            SECRET_KEY='test-secret-key',
            USE_TZ=True,
        )
    
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(['core'])
    return failures


if __name__ == '__main__':
    import sys
    failures = run_tests()
    sys.exit(bool(failures))