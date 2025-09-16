"""Core app URL routes for public, auth, and portal pages."""
from django.urls import path
from django.contrib.auth import views as auth_views


from django.contrib.auth import views as auth_views
from . import views


urlpatterns = [
	path(
		"reset/<uidb64>/<token>/",
		auth_views.PasswordResetConfirmView.as_view(template_name="public/password_reset_confirm.html"),
		name="password_reset_confirm",
	),
	path("forgot-password/", views.forgot_password, name="forgot_password"),
	path("", views.landing_page, name="landing"),
	path("register/", views.register_get, name="register_get"),
	path("register/submit/", views.register_post, name="register_post"),
	path("verify-email/", views.verify_email, name="verify_email"),
	path("login/", views.login_get, name="login_get"),
	path("login/submit/", views.login_post, name="login_post"),
	path("portal/home/", views.portal_home, name="portal_home"),
	path("portal/academics/", views.portal_academics, name="portal_academics"),
	path("portal/academics/<int:program_id>/", views.program_detail, name="program_detail"),
	path("portal/contact/", views.portal_contact, name="portal_contact"),
	path("portal/request-mentor/", views.request_mentor, name="request_mentor"),
	# Staff-only routes available under both /director/ and /admin/director/
	path("director/dashboard/", views.director_dashboard, name="director_dashboard"),
	path("director/assign-mentor/", views.assign_mentor, name="assign_mentor"),
	path("admin/director/dashboard/", views.director_dashboard, name="admin_director_dashboard"),
	path("admin/director/assign-mentor/", views.assign_mentor, name="admin_assign_mentor"),
	# Staff choice page after login
	path("choose-dashboard/", views.choose_dashboard, name="choose_dashboard"),
	# Logout
	path("logout/", views.logout_view, name="logout"),
	# JSON API endpoints for dropdowns
	path("api/states/", views.api_states, name="api_states"),
	path("api/cities/", views.api_cities, name="api_cities"),
	path("api/degrees/", views.api_academic_degrees, name="api_academic_degrees"),
	path("api/years/", views.api_academic_years, name="api_academic_years"),
	path("api/institutions/", views.api_institutions, name="api_institutions"),
]



