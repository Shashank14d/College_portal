"""Custom middleware for simple registration rate limiting and admin restrictions.

This is a minimal implementation using Django's cache. For production,
use django-ratelimit or a Redis-backed rate limiter.
"""
from datetime import timedelta
from django.core.cache import cache
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.models import User
from django.contrib import messages


class RegistrationRateLimitMiddleware:
	"""Rate-limit POST /register/submit/ per IP to prevent abuse."""
	def __init__(self, get_response):
		self.get_response = get_response

	def __call__(self, request):
		if request.method == "POST" and request.path.startswith("/register/submit/"):
			ip = request.META.get("REMOTE_ADDR", "0.0.0.0")
			ua = request.META.get("HTTP_USER_AGENT", "")
			key = f"rl:register:{ip}:{hash(ua) % 1000}"
			count = cache.get(key, 0)
			if count >= 5:
				return HttpResponse("Too many registration attempts. Please try again later.", status=429)
			cache.set(key, count + 1, timeout=60)  # 5 per minute
		return self.get_response(request)


class AdminRestrictionMiddleware:
	"""Middleware to enforce admin restrictions and limits."""
	
	def __init__(self, get_response):
		self.get_response = get_response

	def __call__(self, request):
		# Only apply to admin URLs
		if request.path.startswith('/admin/'):
			# Check if user is authenticated and is staff
			if request.user.is_authenticated and request.user.is_staff:
				# Enforce maximum 4 admins limit
				if self._is_admin_creation_request(request):
					admin_count = User.objects.filter(is_staff=True).count()
					if admin_count >= 4:
						messages.error(request, 'Maximum of 4 admin users allowed.')
						return HttpResponseForbidden('Maximum of 4 admin users allowed.')
		
		# Admin users can access all features - no restrictions here
			
		return self.get_response(request)
	
	def _is_admin_creation_request(self, request):
		"""Check if this is a request to create a new admin user."""
		if request.method == 'POST':
			# Check if creating a new user with staff privileges
			if 'is_staff' in request.POST and request.POST.get('is_staff') == 'on':
				return True
		return False
	
	def _is_common_user_feature(self, request):
		"""Check if admin is trying to access common user features."""
		common_user_paths = [
			'/portal/home/',
			'/portal/academics/',
			'/portal/contact/',
			'/portal/request-mentor/',
			'/register/',
			'/login/',
		]
		
		return any(request.path.startswith(path) for path in common_user_paths)











