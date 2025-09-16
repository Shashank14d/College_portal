import os
from datetime import timedelta
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.core.mail import send_mail
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.db import transaction
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
from django.urls import reverse


def forgot_password(request: HttpRequest) -> HttpResponse:
	"""Display and process forgot password form."""
	if request.method == "POST":
		email = request.POST.get("email", "").strip().lower()
		user = User.objects.filter(email=email).first()
		if not user:
			messages.error(request, "No user found with that email address.")
			return render(request, "public/forgot_password.html")
		# Generate password reset link
		token = default_token_generator.make_token(user)
		uid = urlsafe_base64_encode(force_bytes(user.pk))
		reset_url = request.build_absolute_uri(
			reverse("password_reset_confirm", kwargs={"uidb64": uid, "token": token})
		)
		# Send email
		subject = "Password Reset for Surana College Portal"
		message = render_to_string("emails/password_reset.txt", {"user": user, "reset_url": reset_url})
		send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
		messages.success(request, "A password reset link has been sent to your email.")
		return render(request, "public/forgot_password.html")
	return render(request, "public/forgot_password.html")
import os
from datetime import timedelta
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.core.mail import send_mail
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.db import transaction
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from .models import (
	AcademicRecord,
	EmailVerificationToken,
	Mentor,
	MentorAssignment,
	PageContent,
	MentorRequest,
	Program,
	RegistrationLog,
	UserProfile,
	Visitor,
)
from .utils import (
	send_verification_email, 
	send_mentor_assignment, 
	send_whatsapp_message,
	send_mentor_notification_to_mentor,
    send_registration_email
)


def _track_visit(request: HttpRequest, path: str) -> None:
	"""Record a simple visitor log for analytics.

	Inputs: HttpRequest, path string
	Side-effects: Creates a Visitor row.
	"""
	Visitor.objects.create(
		ip_address=request.META.get("REMOTE_ADDR", "0.0.0.0"),
		path=path,
		page_visited=path,  # Store the page path for analytics
		user=request.user if request.user.is_authenticated else None,
		user_agent=request.META.get("HTTP_USER_AGENT", ""),
	)


def landing_page(request: HttpRequest) -> HttpResponse:
	"""Public landing page with hero transitions and CTA."""
	_track_visit(request, "/")
	return render(request, "public/landing.html")


def register_get(request: HttpRequest) -> HttpResponse:
	"""Serve the registration form."""
	_track_visit(request, "/register/")
	return render(request, "public/register.html")


@transaction.atomic
@csrf_protect
def register_post(request: HttpRequest) -> HttpResponse:
	"""Process registration submission with server-side validation.

	Saves user, profile, academic records, and sends verification email.
	"""
	if request.method != "POST":
		return redirect("register_get")

	# Basic validation (more can be added as needed)
	full_name = request.POST.get("full_name", "").strip()
	email = request.POST.get("email", "").strip().lower()
	password = request.POST.get("password", "")
	confirm_password = request.POST.get("confirm_password", "")
	if not full_name or not email or not password:
		messages.error(request, "Please fill all required fields.")
		return redirect("register_get")
	if password != confirm_password:
		messages.error(request, "Passwords do not match.")
		return redirect("register_get")

	# Enforce same password rules as login (use Django validators from settings)
	try:
		validate_password(password)
	except ValidationError as exc:
		for msg in exc.messages:
			messages.error(request, msg)
		return redirect("register_get")
	if User.objects.filter(email=email).exists():
		messages.error(request, "Email already registered.")
		return redirect("register_get")

	first_name = full_name.split(" ")[0]
	username = email
	user = User.objects.create_user(username=username, email=email, password=password, first_name=first_name)

	# Create profile explicitly (signals don't auto-create to avoid test collisions)
	profile = UserProfile.objects.create(user=user)
	profile.full_name = full_name
	profile.dob = request.POST.get("dob") or None
	profile.father_name = request.POST.get("father_name", "")
	profile.mother_name = request.POST.get("mother_name", "")
	profile.phone = request.POST.get("phone", "")
	profile.city = request.POST.get("city", "")
	profile.pincode = request.POST.get("pincode", "")
	profile.cet_taken = request.POST.get("cet_taken") == "yes"
	# Allow immediate access without admin verification
	profile.verified = True
	profile.registration_source = "web"
	profile.save()

	# Academic records (expect arrays)
	levels = request.POST.getlist("level[]")
	degrees = request.POST.getlist("degree[]")
	institutions = request.POST.getlist("institution[]")
	years = request.POST.getlist("year[]")
	percentages = request.POST.getlist("percentage[]")
	for i in range(len(levels)):
		if levels[i] and degrees[i]:
			AcademicRecord.objects.create(
				user=user,
				level=levels[i],
				degree=degrees[i],
				institution=institutions[i],
				year=int(years[i] or 0),
				percentage=float(percentages[i] or 0),
			)

	# Optional: keep token for audit, but we won't require email verification
	signer = TimestampSigner()
	raw = f"{user.pk}:{email}:{timezone.now().timestamp()}"
	token = signer.sign(raw)
	EmailVerificationToken.objects.create(
		user=user,
		token=token,
		expires_at=timezone.now() + timedelta(hours=24),
	)

	# Send email with link to the main portal and attach brochure
	portal_link = f"{settings.SITE_BASE_URL}/portal/home/"
	brochure_path = os.path.join(settings.BASE_DIR, 'static', 'brochures', 'mca_brochure.pdf')
	send_registration_email(user=user, full_name=full_name, portal_link=portal_link, brochure_path=brochure_path)

	RegistrationLog.objects.create(user=user, ip=request.META.get("REMOTE_ADDR"), status="submitted")
	messages.success(request, "Registration successful. Check your email for the portal link and then log in.")
	return redirect("login_get")


def verify_email(request: HttpRequest) -> HttpResponse:
	"""Verify email using a signed, expiring token and activate user access."""
	_track_visit(request, "/verify-email/")
	token = request.GET.get("token", "")
	if not token:
		return HttpResponse("Invalid token.")
	try:
		# TimestampSigner doesn't automatically expire; we enforce via DB expires_at
		EmailVerificationToken.objects.get(token=token)
		# Validate signature
		TimestampSigner().unsign(token, max_age=None)
	except (BadSignature, EmailVerificationToken.DoesNotExist):
		return HttpResponse("Invalid or expired token.")

	# Mark profile verified
	try:
		record = EmailVerificationToken.objects.get(token=token)
		if record.expires_at < timezone.now():
			return HttpResponse("Token expired.")
		profile = UserProfile.objects.get(user=record.user)
		profile.verified = True
		profile.save()
		messages.success(request, "Email verified. You can now log in.")
		return redirect("login_get")
	except Exception:
		return HttpResponse("Verification failed.")


def login_get(request: HttpRequest) -> HttpResponse:
	"""Render login form."""
	_track_visit(request, "/login/")
	return render(request, "public/login.html")


def login_post(request: HttpRequest) -> HttpResponse:
	"""Authenticate user by email + password and ensure verified."""
	if request.method != "POST":
		return redirect("login_get")
	identifier = request.POST.get("email", "").strip()
	password = request.POST.get("password", "")
	# Support both flows: users whose username==email and superusers with separate usernames
	# Try email first, then username fallback for admins or general users
	user_obj = User.objects.filter(email__iexact=identifier).first()
	if user_obj:
		user = authenticate(request, username=user_obj.username, password=password)
	else:
		# Fallback: try authenticating directly with provided identifier as username
		user = authenticate(request, username=identifier, password=password)
	if not user:
		messages.error(request, "Invalid credentials.")
		return redirect("login_get")
	# Do not block login on verification; allow immediate access
	login(request, user)
	# If staff/admin, offer a choice between dashboards
	if user.is_staff or user.is_superuser:
		return redirect("choose_dashboard")
	return redirect("portal_home")


@login_required
def choose_dashboard(request: HttpRequest) -> HttpResponse:
	"""Staff landing page to choose between Director and Admin dashboards."""
	if not request.user.is_staff and not request.user.is_superuser:
		return redirect("portal_home")
	return render(request, "portal/admin_choice.html")


@login_required
def portal_home(request: HttpRequest) -> HttpResponse:
	"""Portal home page with hero transitions for verified users."""
	return render(request, "portal/home.html")


@login_required
def portal_academics(request: HttpRequest) -> HttpResponse:
	"""Show programs/courses managed via admin (PageContent)."""
	programs = Program.objects.all()
	return render(request, "portal/academics.html", {"programs": programs})


@login_required
def portal_contact(request: HttpRequest) -> HttpResponse:
	"""Display contact info from DB with mentor request button for logged-in users."""
	contact_email = PageContent.objects.filter(key="contact:email").first()
	contact_phone = PageContent.objects.filter(key="contact:phone").first()
	
	# Check if user already has a mentor assigned
	has_mentor = False
	if hasattr(request.user, 'profile') and request.user.profile.assigned_mentor:
		has_mentor = True
	
	return render(
		request,
		"portal/contact.html",
		{
			"contact_email": contact_email, 
			"contact_phone": contact_phone,
			"has_mentor": has_mentor,
			"assigned_mentor": request.user.profile.assigned_mentor if has_mentor else None
		},
	)


@login_required
def request_mentor(request: HttpRequest) -> HttpResponse:
	"""Create a mentor request and notify admins."""
	# Prevent duplicate pending requests
	if MentorRequest.objects.filter(user=request.user, status="pending").exists():
		messages.warning(request, "You already have a pending mentor request.")
		return redirect("portal_home")

	# Create the request
	MentorRequest.objects.create(user=request.user, status="pending")

	# Notify admins
	admin_emails = User.objects.filter(is_staff=True).values_list("email", flat=True)
	if admin_emails:
		subject = "New Mentor Request Received"
		message = render_to_string(
			"emails/mentor_request_admin.txt",
			{"user": request.user, "dashboard_url": request.build_absolute_uri("/director/dashboard/")}
		)
		send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, list(admin_emails))

	messages.success(request, "Your mentor request has been submitted. You will be notified once it's reviewed.")
	return redirect("portal_home")


@login_required
def program_detail(request: HttpRequest, program_id: int) -> HttpResponse:
	"""Show details for a specific program."""
	try:
		program = Program.objects.get(pk=program_id)
	except Program.DoesNotExist:
		messages.error(request, "The requested program does not exist.")
		return redirect("portal_academics")
	return render(request, "portal/program_detail.html", {"program": program})


def director_dashboard(request: HttpRequest) -> HttpResponse:
	"""Director dashboard: counts, pending verifications, and mentor requests."""
	if not request.user.is_authenticated:
		return redirect("login_get")
	if not request.user.is_staff:
		return HttpResponse(status=403)
	
	mentor_requests = MentorRequest.objects.filter(status="pending").select_related("user")

	counts = {
		"visitors": Visitor.objects.count(),
		"registrations": UserProfile.objects.select_related("user").filter(user__is_staff=False, user__is_superuser=False).count(),
		"pending_mentor_assignments": mentor_requests.count(),
		"mentors": Mentor.objects.count(),
	}
	
	# Show users without mentors in the assignment dropdown for clarity
	users_for_assignment = UserProfile.objects.filter(
		assigned_mentor__isnull=True, user__is_staff=False, user__is_superuser=False
	).select_related("user")

	# For the general list, show all recent users
	all_users = UserProfile.objects.select_related("user").filter(user__is_staff=False, user__is_superuser=False).order_by("-created_at")[:50]
	
	mentors = Mentor.objects.all()
	
	return render(
		request, 
		"portal/director_dashboard.html", 
		{
			"counts": counts, 
			"users_for_assignment": users_for_assignment,
			"all_users": all_users,
			"mentors": mentors,
			"mentor_requests": mentor_requests
		}
	)


@staff_member_required
def assign_mentor(request: HttpRequest) -> HttpResponse:
	"""Assign a mentor to a user, update request status, and send notifications."""
	if request.method != "POST":
		return HttpResponseForbidden("Invalid method")

	user_id = request.POST.get("user_id")
	mentor_id = request.POST.get("mentor_id")

	try:
		user = User.objects.get(pk=user_id)
		mentor = Mentor.objects.get(pk=mentor_id)
	except (User.DoesNotExist, Mentor.DoesNotExist):
		messages.error(request, "Invalid student or mentor selected.")
		return redirect("director_dashboard")

	# Prevent assigning mentors to staff/superusers
	if user.is_staff or user.is_superuser:
		messages.error(request, "Cannot assign mentors to admin/staff accounts.")
		return redirect("director_dashboard")

	profile = user.profile
	profile.assigned_mentor = mentor
	profile.save()
	
	MentorAssignment.objects.create(user=user, mentor=mentor, assigned_by=request.user)

	# If there was a pending request, mark it as approved
	pending_request = MentorRequest.objects.filter(user=user, status="pending").first()
	if pending_request:
		pending_request.status = "approved"
		pending_request.save()

	# Send notifications (email + WhatsApp with fallback)
	student_name = user.get_full_name() or user.first_name or user.email
	send_mentor_assignment(
		to_email=user.email,
		student_name=student_name,
		mentor_name=mentor.name,
		portfolio_url=mentor.portfolio_url,
		whatsapp_link=mentor.whatsapp_group_link,
	)
	# Send notification to the mentor
	send_mentor_notification_to_mentor(mentor, user)
	
	messages.success(request, f"Mentor '{mentor.name}' assigned to '{student_name}' and notifications triggered.")
	return redirect("director_dashboard")


def logout_view(request: HttpRequest) -> HttpResponse:
	"""Handle user logout with proper redirect."""
	logout(request)
	return redirect("landing")


# ---------- Lightweight JSON API endpoints for dropdown data ----------

def api_states(request: HttpRequest) -> JsonResponse:
	"""Return list of Indian states from a public dataset, cached."""
	from django.core.cache import cache
	import json
	from urllib import request as urlrequest

	cache_key = "states_IN"
	cached = cache.get(cache_key)
	if cached:
		return JsonResponse({"states": cached})

	# Public API: countriesnow.space (no API key). Use POST with JSON payload.
	try:
		api_url = "https://countriesnow.space/api/v0.1/countries/states"
		payload = json.dumps({"country": "India"}).encode("utf-8")
		req = urlrequest.Request(api_url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
		with urlrequest.urlopen(req, timeout=10) as resp:
			body = resp.read()
			data = json.loads(body.decode("utf-8"))
			states = [s.get("name") for s in (data.get("data", {}).get("states", []) or []) if s.get("name")]
			states.sort()
			cache.set(cache_key, states, 60 * 60 * 24)  # cache 24h
			return JsonResponse({"states": states})
	except Exception:
		# Fallback minimal list if API fails
		fallback = [
			"Andhra Pradesh", "Delhi", "Gujarat", "Karnataka", "Maharashtra", "Tamil Nadu", "Telangana", "Uttar Pradesh", "West Bengal",
		]
		return JsonResponse({"states": fallback})


def api_cities(request: HttpRequest) -> JsonResponse:
	"""Return list of cities for a given Indian state from a public dataset, cached."""
	from django.core.cache import cache
	import json
	from urllib import request as urlrequest

	state = request.GET.get("state", "").strip()
	if not state:
		return JsonResponse({"cities": []})

	cache_key = f"cities_IN_{state}"
	cached = cache.get(cache_key)
	if cached:
		return JsonResponse({"cities": cached})

	try:
		api_url = "https://countriesnow.space/api/v0.1/countries/state/cities"
		payload = json.dumps({"country": "India", "state": state}).encode("utf-8")
		req = urlrequest.Request(api_url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
		with urlrequest.urlopen(req, timeout=10) as resp:
			body = resp.read()
			data = json.loads(body.decode("utf-8"))
			cities = data.get("data") or []
			cities = [c for c in cities if isinstance(c, str)]
			cities.sort()
			cache.set(cache_key, cities, 60 * 60 * 24)  # cache 24h
			return JsonResponse({"cities": cities})
	except Exception:
		# Fallback sample map if API is unavailable
		sample_map = {
			"Andhra Pradesh": ["Visakhapatnam", "Vijayawada", "Guntur", "Nellore"],
			"Arunachal Pradesh": ["Itanagar", "Tawang"],
			"Assam": ["Guwahati", "Silchar", "Dibrugarh"],
			"Bihar": ["Patna", "Gaya", "Bhagalpur"],
			"Chhattisgarh": ["Raipur", "Bhilai"],
			"Delhi": ["New Delhi"],
			"Goa": ["Panaji", "Margao"],
			"Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Rajkot"],
			"Haryana": ["Gurugram", "Faridabad"],
			"Himachal Pradesh": ["Shimla", "Manali"],
			"Jharkhand": ["Ranchi", "Jamshedpur"],
			"Karnataka": ["Bengaluru", "Mysuru", "Mangaluru", "Hubballi"],
			"Kerala": ["Thiruvananthapuram", "Kochi", "Kozhikode"],
			"Madhya Pradesh": ["Bhopal", "Indore", "Gwalior"],
			"Maharashtra": ["Mumbai", "Pune", "Nagpur", "Nashik"],
			"Manipur": ["Imphal"],
			"Meghalaya": ["Shillong"],
			"Mizoram": ["Aizawl"],
			"Nagaland": ["Kohima", "Dimapur"],
			"Odisha": ["Bhubaneswar", "Cuttack"],
			"Punjab": ["Amritsar", "Ludhiana", "Jalandhar"],
			"Rajasthan": ["Jaipur", "Udaipur", "Jodhpur"],
			"Sikkim": ["Gangtok"],
			"Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Salem"],
			"Telangana": ["Hyderabad", "Warangal", "Nizamabad"],
			"Tripura": ["Agartala"],
			"Uttar Pradesh": ["Lucknow", "Kanpur", "Noida", "Varanasi"],
			"Uttarakhand": ["Dehradun", "Haridwar"],
			"West Bengal": ["Kolkata", "Siliguri", "Durgapur"],
		}
		return JsonResponse({"cities": sample_map.get(state, [])})


def api_academic_degrees(request: HttpRequest) -> JsonResponse:
	"""Return degrees based on level (UG/PG)."""
	level = (request.GET.get("level", "UG") or "UG").upper()
	ug = [
		"B.Tech Computer Science", "B.Tech Electronics", "B.Tech Mechanical",
		"B.Sc Computer Science", "BBA", "B.Com",
	]
	pg = [
		"M.Tech Computer Science", "M.Tech Data Science", "MBA", "MCA",
	]
	return JsonResponse({"degrees": ug if level == "UG" else pg})


def api_academic_years(request: HttpRequest) -> JsonResponse:
	"""Return a reasonable range of years for academic records."""
	from datetime import datetime

	current = datetime.utcnow().year
	start = 1980
	years = list(range(current, start - 1, -1))
	return JsonResponse({"years": years})


def api_institutions(request: HttpRequest) -> JsonResponse:
	"""Return institutions filtered by state/city/level/degree.

	Strategy:
	- Fetch India universities from Hipolabs (cached 24h)
	- Merge with curated list for popular cities
	- Filter by state/city heuristics (case-insensitive contains on name/state-province)
	- Light keyword filter for degree level
	"""
	import json
	from urllib import request as urlrequest
	from django.core.cache import cache

	state = (request.GET.get("state", "") or "").strip()
	city = (request.GET.get("city", "") or "").strip()
	level = (request.GET.get("level", "UG") or "UG").upper()
	degree = (request.GET.get("degree", "") or "").strip()

	# 1) Prefer authoritative local datasets if present (AISHE/AICTE/UGC)
	local_cache_key = "institutions_local_v1"
	local_rows = cache.get(local_cache_key)
	if local_rows is None:
		local_rows = []
		try:
			import csv, os
			base_dir = os.path.dirname(os.path.dirname(__file__))
			data_dir = os.path.join(base_dir, "core", "data")
			candidates = [
				os.path.join(data_dir, "aishe_institutions.csv"),
				os.path.join(data_dir, "aicte_institutions.csv"),
				os.path.join(data_dir, "ugc_institutions.csv"),
			]
			for path in candidates:
				if os.path.exists(path):
					with open(path, newline='', encoding='utf-8') as f:
						r = csv.DictReader(f)
						for row in r:
							name = (row.get("name") or row.get("institution") or row.get("Institute Name") or "").strip()
							st = (row.get("state") or row.get("State") or row.get("STATE") or "").strip()
							ct = (row.get("city") or row.get("District") or row.get("CITY") or "").strip()
							if name:
								local_rows.append({"name": name, "state": st, "city": ct})
			cache.set(local_cache_key, local_rows, 60 * 60)  # cache 1h; change if files updated
		except Exception:
			local_rows = []

	# Try to filter local rows first
	def norm(s: str) -> str:
		return (s or "").lower()

	n_state = norm(state)
	n_city = norm(city)
	n_degree = norm(degree).split(" ")[0] if degree else ""

	if local_rows:
		candidates = []
		for r in local_rows:
			name = r.get("name", "")
			st = norm(r.get("state", ""))
			ct = norm(r.get("city", ""))
			if ((not n_state) or (n_state in st) or (n_state in norm(name))) and ((not n_city) or (n_city in ct) or (n_city in norm(name))):
				candidates.append(name)
		# Optional degree keyword filter
		if n_degree:
			filtered = [n for n in candidates if n_degree in norm(n)]
			if filtered:
				candidates = filtered
		# Dedupe & return if non-empty
		seen = set()
		result = []
		for n in candidates:
			if n and n not in seen:
				seen.add(n)
				result.append(n)
		result = sorted(result)[:300]
		if result:
			return JsonResponse({"institutions": result})

	# 2) Fallback: Hipolabs (broad coverage)
	cache_key = "hipo_unis_IN_v1"
	unis = cache.get(cache_key)
	if unis is None:
		try:
			with urlrequest.urlopen("https://universities.hipolabs.com/search?country=India", timeout=10) as resp:
				unis = json.loads(resp.read().decode("utf-8"))
				cache.set(cache_key, unis, 60 * 60 * 24)
		except Exception:
			unis = []

	# Curated additions by (state, city)
	curated = {
		("Karnataka", "Bengaluru"): [
			"Indian Institute of Science",
			"RV College of Engineering",
			"BMS College of Engineering",
			"PES University",
			"Dayananda Sagar College of Engineering",
		],
		("Maharashtra", "Pune"): [
			"College of Engineering Pune",
			"MIT World Peace University",
			"Symbiosis Institute of Technology",
			"Vishwakarma Institute of Technology",
		],
		("Tamil Nadu", "Chennai"): [
			"Anna University",
			"IIT Madras",
			"SSN College of Engineering",
			"SRM Institute of Science and Technology",
		],
	}

	# Build initial list from Hipolabs
	candidates = []
	for u in unis:
		name = u.get("name") or ""
		prov = u.get("state-province") or ""
		if not name:
			continue
		name_n = norm(name)
		prov_n = norm(prov)
		ok_state = (not n_state) or (n_state in prov_n) or (n_state in name_n)
		ok_city = (not n_city) or (n_city in name_n)
		if ok_state and ok_city:
			candidates.append(name)

	# Merge curated list
	cur = curated.get((state, city)) or []
	if not cur and state:
		# state-only curated merge
		for (s, _c), lst in curated.items():
			if s == state:
				cur.extend(lst)

	candidates.extend(cur)

	# Optional filter by degree keyword
	if n_degree:
		filtered = [n for n in candidates if n_degree in norm(n)]
		if filtered:
			candidates = filtered

	# Dedupe and sort
	seen = set()
	result = []
	for n in candidates:
		if n not in seen:
			seen.add(n)
			result.append(n)
	result = sorted(result)[:200]

	# Always include an 'Other' on the client; we return just institutions
	return JsonResponse({"institutions": result})
