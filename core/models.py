from django.db import models
from django.contrib.auth.models import User


class Mentor(models.Model):
	"""Mentor record holding contact and portfolio information.

	Fields:
	- name: Full name of the mentor
	- email: Contact email
	- portfolio_url: Public portfolio URL
	- whatsapp_group_link: Invite link for WhatsApp group
	- bio: Short mentor bio
	- created_at: Timestamp
	"""
	name = models.CharField(max_length=255)
	email = models.EmailField()
	portfolio_url = models.URLField(blank=True)
	whatsapp_group_link = models.URLField(blank=True)
	bio = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self) -> str:
		return self.name


class UserProfile(models.Model):
	"""Additional user information attached to Django's User model.

	Tracks personal, academic, verification, and mentor assignment metadata.
	"""
	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
	full_name = models.CharField(max_length=255, blank=True)  # Add full name field
	dob = models.DateField(null=True, blank=True)
	father_name = models.CharField(max_length=255, blank=True)
	mother_name = models.CharField(max_length=255, blank=True)
	phone = models.CharField(max_length=20)
	city = models.CharField(max_length=100, blank=True)
	pincode = models.CharField(max_length=10, blank=True)
	cet_taken = models.BooleanField(default=False)
	verified = models.BooleanField(default=False)
	assigned_mentor = models.ForeignKey('Mentor', null=True, blank=True, on_delete=models.SET_NULL)
	registration_source = models.CharField(max_length=100, default="web")
	visited_count = models.PositiveIntegerField(default=0)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self) -> str:
		return f"Profile({self.user.username})"


class AcademicRecord(models.Model):
	"""Academic record entries for a user (UG/PG/etc)."""
	LEVEL_CHOICES = (
		("UG", "Undergraduate"),
		("PG", "Postgraduate"),
	)
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="academics")
	level = models.CharField(max_length=10, choices=LEVEL_CHOICES)
	degree = models.CharField(max_length=255)
	institution = models.CharField(max_length=255)
	year = models.PositiveIntegerField()
	percentage = models.DecimalField(max_digits=5, decimal_places=2)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self) -> str:
		return f"{self.user.username} - {self.level} {self.degree}"


class MentorAssignment(models.Model):
	"""Mentor assignment history for auditing and analytics."""
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	mentor = models.ForeignKey('Mentor', on_delete=models.CASCADE)
	assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="assigned_mentors")
	assigned_at = models.DateTimeField(auto_now_add=True)

	def __str__(self) -> str:
		return f"{self.user.username} -> {self.mentor.name}"


class Visitor(models.Model):
	"""Minimal visitor tracking respecting privacy (ip, path, UA)."""
	ip_address = models.GenericIPAddressField()
	path = models.CharField(max_length=500)
	page_visited = models.CharField(max_length=500, blank=True)  # Store the actual page name/URL
	user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
	user_agent = models.CharField(max_length=255, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self) -> str:
		return f"{self.ip_address} {self.path}"


class EmailVerificationToken(models.Model):
	"""Stores signed token references for email verification with expiry."""
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	token = models.CharField(max_length=255, unique=True)
	created_at = models.DateTimeField(auto_now_add=True)
	expires_at = models.DateTimeField()

	def __str__(self) -> str:
		return f"Token for {self.user.email}"


class PageContent(models.Model):
	"""Key/value store for editable portal content (academics, contact info)."""
	key = models.CharField(max_length=100, unique=True)
	value = models.TextField()
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self) -> str:
		return self.key


class RegistrationLog(models.Model):
	"""Tracks registration events for analytics and troubleshooting."""
	user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
	ip = models.GenericIPAddressField(null=True, blank=True)
	status = models.CharField(max_length=100)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self) -> str:
		return f"{self.status} at {self.created_at}"



class MentorRequest(models.Model):
	"""Student-initiated mentor request to be reviewed in admin."""
	STATUS_CHOICES = (
		("pending", "Pending"),
		("approved", "Approved"),
		("rejected", "Rejected"),
	)
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="mentor_requests")
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
	message = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self) -> str:
		return f"MentorRequest({self.user.username}, {self.status})"


class Program(models.Model):
	"""Model to store details for academic programs."""
	name = models.CharField(max_length=255)
	description = models.TextField()
	video = models.FileField(upload_to='program_videos/', blank=True)
	image = models.ImageField(upload_to='program_images/', blank=True)
	brochure = models.FileField(upload_to='program_brochures/', blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self) -> str:
		return self.name

