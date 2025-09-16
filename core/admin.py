from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib import messages
from django.http import HttpResponseForbidden
from .models import Mentor, UserProfile, AcademicRecord, MentorAssignment, Visitor, EmailVerificationToken, PageContent, RegistrationLog, MentorRequest, Program


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
	"""Admin for managing academic programs."""
	list_display = ("name", "created_at")
	search_fields = ("name", "description")
	list_filter = ("created_at",)
	readonly_fields = ("created_at",)


@admin.register(Mentor)
class MentorAdmin(admin.ModelAdmin):
	"""Admin for managing mentors."""
	list_display = ("name", "email", "portfolio_url")
	search_fields = ("name", "email")
	list_filter = ("created_at",)
	readonly_fields = ("created_at",)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
	"""Admin for user profiles."""
	list_display = ("user", "phone", "city", "verified", "assigned_mentor", "created_at")
	list_filter = ("verified", "city", "cet_taken", "created_at")
	search_fields = ("user__username", "user__email", "phone", "city")
	readonly_fields = ("created_at", "visited_count")
	actions = ["mark_verified", "export_as_csv"]

	def get_queryset(self, request):
		"""Hide staff/superusers from profile list to avoid mixing admin accounts with students."""
		qs = super().get_queryset(request)
		return qs.filter(user__is_staff=False, user__is_superuser=False)

	def mark_verified(self, request, queryset):
		"""Mark selected profiles as verified."""
		updated = queryset.update(verified=True)
		self.message_user(request, f"{updated} profiles marked as verified.")
	mark_verified.short_description = "Mark selected profiles as verified"

	def export_as_csv(self, request, queryset):
		"""Export selected profiles as CSV."""
		import csv
		from django.http import HttpResponse
		response = HttpResponse(content_type="text/csv")
		response["Content-Disposition"] = "attachment; filename=user_profiles.csv"
		writer = csv.writer(response)
		writer.writerow(["Username", "Email", "Phone", "City", "Verified", "Mentor"])
		for profile in queryset:
			writer.writerow([
				profile.user.username,
				profile.user.email,
				profile.phone,
				profile.city,
				profile.verified,
				profile.assigned_mentor.name if profile.assigned_mentor else "None"
			])
		return response
	export_as_csv.short_description = "Export selected profiles as CSV"


@admin.register(AcademicRecord)
class AcademicRecordAdmin(admin.ModelAdmin):
	"""Admin for academic records."""
	list_display = ("user", "level", "degree", "year", "percentage", "institution")
	list_filter = ("level", "year", "created_at")
	search_fields = ("user__username", "degree", "institution")
	readonly_fields = ("created_at",)


@admin.register(MentorAssignment)
class MentorAssignmentAdmin(admin.ModelAdmin):
	"""Admin for mentor assignments."""
	list_display = ("user", "mentor", "assigned_by", "assigned_at")
	list_filter = ("assigned_at", "mentor")
	search_fields = ("user__username", "mentor__name")
	readonly_fields = ("assigned_at",)

	def formfield_for_foreignkey(self, db_field, request, **kwargs):
		from django.contrib.auth.models import User
		if db_field.name == "user":
			kwargs["queryset"] = User.objects.filter(is_staff=False, is_superuser=False)
		return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
	"""Admin for visitor logs."""
	list_display = ("ip_address", "path", "user", "created_at")
	list_filter = ("created_at", "path")
	search_fields = ("ip_address", "path", "user__username")
	readonly_fields = ("created_at",)
	actions = ["export_visitor_stats"]

	def export_visitor_stats(self, request, queryset):
		"""Export visitor statistics as CSV."""
		import csv
		from django.http import HttpResponse
		from django.db.models import Count
		response = HttpResponse(content_type="text/csv")
		response["Content-Disposition"] = "attachment; filename=visitor_stats.csv"
		writer = csv.writer(response)
		writer.writerow(["Path", "Visit Count", "Unique Users"])
		stats = queryset.values("path").annotate(
			count=Count("id"),
			unique_users=Count("user", distinct=True)
		).order_by("-count")
		for stat in stats:
			writer.writerow([stat["path"], stat["count"], stat["unique_users"]])
		return response
	export_visitor_stats.short_description = "Export visitor statistics as CSV"


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
	"""Admin for tokens."""
	list_display = ("user", "token", "created_at", "expires_at", "is_expired")
	search_fields = ("user__email", "token")
	readonly_fields = ("created_at", "expires_at")
	list_filter = ("created_at", "expires_at")

	def is_expired(self, obj):
		"""Check if token is expired."""
		from django.utils import timezone
		return obj.expires_at < timezone.now()
	is_expired.boolean = True
	is_expired.short_description = "Expired"


@admin.register(PageContent)
class PageContentAdmin(admin.ModelAdmin):
	"""Admin for CMS-like content."""
	list_display = ("key", "updated_at")
	search_fields = ("key", "value")
	readonly_fields = ("updated_at",)


@admin.register(RegistrationLog)
class RegistrationLogAdmin(admin.ModelAdmin):
	"""Admin for registration logs."""
	list_display = ("user", "ip", "status", "created_at")
	list_filter = ("status", "created_at")
	search_fields = ("user__email", "status", "ip")
	readonly_fields = ("created_at",)
	actions = ["export_registration_stats"]

	def export_registration_stats(self, request, queryset):
		"""Export registration statistics as CSV."""
		import csv
		from django.http import HttpResponse
		from django.db.models import Count
		response = HttpResponse(content_type="text/csv")
		response["Content-Disposition"] = "attachment; filename=registration_stats.csv"
		writer = csv.writer(response)
		writer.writerow(["Status", "Count", "Date"])
		stats = queryset.values("status", "created_at__date").annotate(
			count=Count("id")
		).order_by("-created_at__date", "-count")
		for stat in stats:
			writer.writerow([stat["status"], stat["count"], stat["created_at__date"]])
		return response
	export_registration_stats.short_description = "Export registration statistics as CSV"


# Custom User Admin with admin restrictions
class CustomUserAdmin(BaseUserAdmin):
	"""Custom User Admin with admin restrictions."""
	
	def has_add_permission(self, request):
		"""Limit admin creation to maximum 4 admins."""
		if request.POST and 'is_staff' in request.POST and request.POST.get('is_staff') == 'on':
			admin_count = User.objects.filter(is_staff=True).count()
			if admin_count >= 4:
				messages.error(request, 'Maximum of 4 admin users allowed.')
				return False
		return super().has_add_permission(request)
	
	def get_queryset(self, request):
		"""Filter queryset based on user permissions."""
		qs = super().get_queryset(request)
		# Only show admin users to other admin users
		if request.user.is_superuser:
			return qs
		return qs.filter(is_staff=True)
	
	def get_readonly_fields(self, request, obj=None):
		"""Make certain fields readonly for non-superusers."""
		readonly_fields = list(super().get_readonly_fields(request, obj))
		if not request.user.is_superuser:
			readonly_fields.extend(['is_superuser', 'user_permissions', 'groups'])
		return readonly_fields

# Unregister default User admin and register custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Customize admin site
admin.site.site_header = "College Portal Administration"
admin.site.site_title = "College Portal Admin"
admin.site.index_title = "Welcome to College Portal Administration"


@admin.register(MentorRequest)
class MentorRequestAdmin(admin.ModelAdmin):
	"""Admin for mentor requests submitted by students."""
	list_display = ("user", "status", "created_at", "updated_at")
	list_filter = ("status", "created_at")
	search_fields = ("user__username", "user__email")
	readonly_fields = ("created_at", "updated_at")
	autocomplete_fields = ("user",)
