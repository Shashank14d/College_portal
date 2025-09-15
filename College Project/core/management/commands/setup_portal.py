from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.management import call_command
from core.models import PageContent, Mentor, UserProfile
from django.utils import timezone


class Command(BaseCommand):
    help = 'Set up the College Portal with initial data and sample content'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force setup even if data already exists',
        )
        parser.add_argument(
            '--sample-data',
            action='store_true',
            help='Create sample data for testing',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Setting up College Portal...')
        )

        # Create initial page content
        self.setup_page_content(options['force'])
        
        # Create sample mentors if requested
        if options['sample_data']:
            self.create_sample_mentors()
        
        # Create superuser if none exists
        self.create_superuser()
        
        # Run migrations
        self.stdout.write('Running migrations...')
        call_command('migrate', verbosity=0)
        
        # Collect static files
        self.stdout.write('Collecting static files...')
        call_command('collectstatic', '--noinput', verbosity=0)
        
        self.stdout.write(
            self.style.SUCCESS('✅ College Portal setup completed successfully!')
        )

    def setup_page_content(self, force=False):
        """Set up initial page content."""
        self.stdout.write('Setting up page content...')
        
        content_data = {
            'welcome_title': 'Welcome to Our College Portal',
            'welcome_message': 'Discover excellence in education and connect with mentors for your academic journey.',
            'contact_email': 'info@college.edu',
            'contact_phone': '+1 (555) 123-4567',
            'program_ug_cs': 'B.Tech Computer Science - 4 years program with modern curriculum',
            'program_ug_it': 'B.Tech Information Technology - 4 years program with industry focus',
            'program_pg_cs': 'M.Tech Computer Science - 2 years advanced program',
            'program_pg_it': 'M.Tech Information Technology - 2 years specialized program',
            'about_college': 'A premier institution dedicated to academic excellence and innovation.',
            'admission_info': 'Admissions open for the academic year 2025-26. Apply now!',
            'academic_calendar': 'Academic calendar and important dates for the current year.',
            'library_info': 'Access to extensive digital and physical learning resources.',
            'career_services': 'Comprehensive career counseling and placement assistance.',
            'student_life': 'Rich campus life with various clubs, events, and activities.',
            'research_areas': 'Cutting-edge research in Computer Science, AI, and Data Science.',
            'international_programs': 'Global exchange programs and international collaborations.',
            'alumni_network': 'Strong alumni network providing mentorship and career guidance.',
            'facilities_info': 'State-of-the-art laboratories, libraries, and sports facilities.',
            'scholarship_info': 'Merit-based and need-based scholarship programs available.',
            'hostel_info': 'Comfortable accommodation with modern amenities for students.',
            'transport_info': 'Convenient transportation services for students and staff.',
            'health_services': 'On-campus health center providing medical care and counseling.',
            'security_info': '24/7 security services ensuring campus safety.',
        }
        
        for key, value in content_data.items():
            if force or not PageContent.objects.filter(key=key).exists():
                PageContent.objects.update_or_create(
                    key=key,
                    defaults={
                        'value': value,
                        'updated_at': timezone.now()
                    }
                )
                self.stdout.write(f'  ✓ Created/Updated: {key}')
            else:
                self.stdout.write(f'  - Skipped (exists): {key}')

    def create_sample_mentors(self):
        """Create sample mentor profiles for testing."""
        self.stdout.write('Creating sample mentors...')
        
        mentors_data = [
            {
                'name': 'Dr. Sarah Johnson',
                'email': 'sarah.johnson@college.edu',
                'portfolio_url': 'https://sarahjohnson.dev',
                'whatsapp_group_link': 'https://chat.whatsapp.com/sample1',
                'bio': 'Expert in Computer Science and Artificial Intelligence with 10+ years of industry experience.'
            },
            {
                'name': 'Prof. Michael Chen',
                'email': 'michael.chen@college.edu',
                'portfolio_url': 'https://michaelchen.tech',
                'whatsapp_group_link': 'https://chat.whatsapp.com/sample2',
                'bio': 'Data Science and Machine Learning specialist with extensive research background.'
            },
            {
                'name': 'Ms. Emily Davis',
                'email': 'emily.davis@college.edu',
                'portfolio_url': 'https://emilydavis.dev',
                'whatsapp_group_link': 'https://chat.whatsapp.com/sample3',
                'bio': 'Software Engineering and Web Development expert with focus on modern technologies.'
            },
            {
                'name': 'Mr. Robert Wilson',
                'email': 'robert.wilson@college.edu',
                'portfolio_url': 'https://robertwilson.tech',
                'whatsapp_group_link': 'https://chat.whatsapp.com/sample4',
                'bio': 'Cybersecurity and Network Security professional with industry certifications.'
            },
            {
                'name': 'Dr. Lisa Rodriguez',
                'email': 'lisa.rodriguez@college.edu',
                'portfolio_url': 'https://lisarodriguez.dev',
                'whatsapp_group_link': 'https://chat.whatsapp.com/sample5',
                'bio': 'Database Systems and Cloud Computing expert with academic and industry experience.'
            }
        ]
        
        for mentor_data in mentors_data:
            if not Mentor.objects.filter(email=mentor_data['email']).exists():
                Mentor.objects.create(**mentor_data)
                self.stdout.write(f'  ✓ Created mentor: {mentor_data["name"]}')
            else:
                self.stdout.write(f'  - Skipped (exists): {mentor_data["name"]}')

    def create_superuser(self):
        """Create a superuser if none exists."""
        if not User.objects.filter(is_superuser=True).exists():
            self.stdout.write('Creating superuser...')
            try:
                user = User.objects.create_superuser(
                    username='admin',
                    email='admin@college.edu',
                    password='admin123'
                )
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Superuser created: {user.username}')
                )
                self.stdout.write(
                    self.style.WARNING('  ⚠️  Default password: admin123 - Change this immediately!')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Failed to create superuser: {e}')
                )
        else:
            self.stdout.write('  - Superuser already exists')

    def create_sample_users(self):
        """Create sample user profiles for testing."""
        self.stdout.write('Creating sample users...')
        
        users_data = [
            {
                'username': 'student1',
                'email': 'student1@example.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'password': 'student123'
            },
            {
                'username': 'student2',
                'email': 'student2@example.com',
                'first_name': 'Jane',
                'last_name': 'Smith',
                'password': 'student123'
            }
        ]
        
        for user_data in users_data:
            if not User.objects.filter(username=user_data['username']).exists():
                user = User.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    password=user_data['password']
                )
                
                # Create user profile
                UserProfile.objects.create(
                    user=user,
                    full_name=f"{user_data['first_name']} {user_data['last_name']}",
                    phone='+1 (555) 123-4000',
                    city='Sample City',
                    pincode='123456',
                    verified=True
                )
                
                self.stdout.write(f'  ✓ Created user: {user_data["username"]}')
            else:
                self.stdout.write(f'  - Skipped (exists): {user_data["username"]}')

    def setup_permissions(self):
        """Set up basic permissions and groups."""
        self.stdout.write('Setting up permissions...')
        
        from django.contrib.auth.models import Group, Permission
        from django.contrib.contenttypes.models import ContentType
        from core.models import UserProfile, Mentor, MentorAssignment
        
        # Create groups
        student_group, created = Group.objects.get_or_create(name='Students')
        mentor_group, created = Group.objects.get_or_create(name='Mentors')
        staff_group, created = Group.objects.get_or_create(name='Staff')
        
        if created:
            self.stdout.write('  ✓ Created groups: Students, Mentors, Staff')
        else:
            self.stdout.write('  - Groups already exist')
        
        # Add permissions to groups
        content_types = {
            'userprofile': ContentType.objects.get_for_model(UserProfile),
            'mentor': ContentType.objects.get_for_model(Mentor),
            'mentorassignment': ContentType.objects.get_for_model(MentorAssignment),
        }
        
        # Students can view their own profile and assigned mentor
        view_profile = Permission.objects.get(
            content_type=content_types['userprofile'],
            codename='view_userprofile'
        )
        student_group.permissions.add(view_profile)
        
        # Mentors can view their assignments
        view_assignment = Permission.objects.get(
            content_type=content_types['mentorassignment'],
            codename='view_mentorassignment'
        )
        mentor_group.permissions.add(view_assignment)
        
        self.stdout.write('  ✓ Set up basic permissions')

    def validate_setup(self):
        """Validate that the setup was successful."""
        self.stdout.write('Validating setup...')
        
        # Check page content
        content_count = PageContent.objects.count()
        if content_count > 0:
            self.stdout.write(f'  ✓ Page content: {content_count} items')
        else:
            self.stdout.write(self.style.ERROR('  ✗ No page content found'))
        
        # Check mentors
        mentor_count = Mentor.objects.count()
        if mentor_count > 0:
            self.stdout.write(f'  ✓ Mentors: {mentor_count} profiles')
        else:
            self.stdout.write(self.style.ERROR('  ✗ No mentors found'))
        
        # Check superuser
        superuser_count = User.objects.filter(is_superuser=True).count()
        if superuser_count > 0:
            self.stdout.write(f'  ✓ Superuser: {superuser_count} accounts')
        else:
            self.stdout.write(self.style.ERROR('  ✗ No superuser found'))
        
        # Check groups
        group_count = Group.objects.count()
        if group_count >= 3:
            self.stdout.write(f'  ✓ Groups: {group_count} groups')
        else:
            self.stdout.write(self.style.ERROR('  ✗ Insufficient groups'))
        
        self.stdout.write(
            self.style.SUCCESS('✅ Setup validation completed!')
        )


