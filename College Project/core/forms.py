from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, AcademicRecord, Mentor, MentorAssignment


class UserRegistrationForm(UserCreationForm):
    """Form for student registration with extended fields."""
    
    # Personal Information
    full_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your full name'
        })
    )
    
    dob = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    father_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Father\'s name (optional)'
        })
    )
    
    mother_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mother\'s name (optional)'
        })
    )
    
    phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone number'
        })
    )
    
    pincode = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'PIN Code'
        })
    )
    
    city = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'City'
        })
    )
    
    cet_taken = forms.ChoiceField(
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect(attrs={'class': 'radio-input'})
    )
    
    # Academic Records (handled via JavaScript)
    academic_records = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )
    
    class Meta:
        model = User
        fields = ('email', 'password1', 'password2')
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email address'
            })
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already registered.')
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        # Basic phone validation
        if not phone.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise forms.ValidationError('Please enter a valid phone number.')
        return phone
    
    def clean_pincode(self):
        pincode = self.cleaned_data.get('pincode')
        if not pincode.isdigit() or len(pincode) != 6:
            raise forms.ValidationError('Please enter a valid 6-digit PIN code.')
        return pincode
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']  # Use email as username
        user.first_name = self.cleaned_data['full_name'].split()[0] if self.cleaned_data['full_name'] else ''
        user.last_name = ' '.join(self.cleaned_data['full_name'].split()[1:]) if len(self.cleaned_data['full_name'].split()) > 1 else ''
        
        if commit:
            user.save()
            
            # Create user profile
            profile = UserProfile.objects.create(
                user=user,
                full_name=self.cleaned_data['full_name'],
                dob=self.cleaned_data['dob'],
                father_name=self.cleaned_data['father_name'],
                mother_name=self.cleaned_data['mother_name'],
                phone=self.cleaned_data['phone'],
                pincode=self.cleaned_data['pincode'],
                city=self.cleaned_data['city'],
                cet_taken=self.cleaned_data['cet_taken'] == 'yes'
            )
            
        return user


class AcademicRecordForm(forms.ModelForm):
    """Form for individual academic records."""
    
    class Meta:
        model = AcademicRecord
        fields = ['level', 'degree', 'institution', 'year', 'percentage']
        widgets = {
            'level': forms.Select(attrs={'class': 'form-control'}),
            'degree': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., B.Tech Computer Science'
            }),
            'institution': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Institution name'
            }),
            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1900',
                'max': '2100'
            }),
            'percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100'
            })
        }
    
    def clean_year(self):
        year = self.cleaned_data.get('year')
        if year < 1900 or year > 2100:
            raise forms.ValidationError('Please enter a valid year between 1900 and 2100.')
        return year
    
    def clean_percentage(self):
        percentage = self.cleaned_data.get('percentage')
        if percentage < 0 or percentage > 100:
            raise forms.ValidationError('Percentage must be between 0 and 100.')
        return percentage


class MentorAssignmentForm(forms.ModelForm):
    """Form for assigning mentors to students."""
    
    user_id = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        empty_label="Select a student",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    mentor_id = forms.ModelChoiceField(
        queryset=Mentor.objects.all(),
        empty_label="Select a mentor",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = MentorAssignment
        fields = ['user_id', 'mentor_id']
        widgets = {}
    
    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get('user_id')
        mentor = cleaned_data.get('mentor_id')
        
        if user and mentor:
            # Check if user already has a mentor
            if MentorAssignment.objects.filter(user=user).exists():
                raise forms.ValidationError('This student already has an assigned mentor.')
            
            # Check if mentor is available (not overloaded)
            active_assignments = MentorAssignment.objects.filter(mentor=mentor).count()
            if active_assignments >= 10:  # Maximum 10 students per mentor
                raise forms.ValidationError('This mentor has reached the maximum number of students.')
        
        return cleaned_data


class MentorForm(forms.ModelForm):
    """Form for creating/editing mentor profiles."""
    
    class Meta:
        model = Mentor
        fields = ['name', 'email', 'portfolio_url', 'whatsapp_group_link', 'bio']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Mentor\'s full name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email address'
            }),
            'portfolio_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'Portfolio website URL (optional)'
            }),
            'whatsapp_group_link': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'WhatsApp group invite link (optional)'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Mentor bio and background (optional)',
                'rows': 3
            })
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Mentor.objects.filter(email=email).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise forms.ValidationError('This email address is already registered for another mentor.')
        return email


class UserProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile information."""
    
    class Meta:
        model = UserProfile
        fields = ['full_name', 'phone', 'city', 'pincode']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full name'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone number'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City'
            }),
            'pincode': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'PIN Code'
            })
        }
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise forms.ValidationError('Please enter a valid phone number.')
        return phone
    
    def clean_pincode(self):
        pincode = self.cleaned_data.get('pincode')
        if not pincode.isdigit() or len(pincode) != 6:
            raise forms.ValidationError('Please enter a valid 6-digit PIN code.')
        return pincode


class ContactForm(forms.Form):
    """Form for contact page inquiries."""
    
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your name'
        })
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your email address'
        })
    )
    
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Subject of your inquiry'
        })
    )
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Please describe your inquiry or request...'
        })
    )
    
    inquiry_type = forms.ChoiceField(
        choices=[
            ('general', 'General Inquiry'),
            ('academic', 'Academic Support'),
            ('mentor', 'Mentor Request'),
            ('technical', 'Technical Support'),
            ('other', 'Other')
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    preferred_contact = forms.ChoiceField(
        choices=[
            ('email', 'Email'),
            ('phone', 'Phone'),
            ('whatsapp', 'WhatsApp')
        ],
        widget=forms.RadioSelect(attrs={'class': 'radio-input'})
    )


class SearchForm(forms.Form):
    """Form for searching students, mentors, or academic records."""
    
    search_query = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search for students, mentors, or programs...'
        })
    )
    
    search_type = forms.ChoiceField(
        choices=[
            ('all', 'All'),
            ('students', 'Students'),
            ('mentors', 'Mentors'),
            ('programs', 'Academic Programs')
        ],
        initial='all',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    status_filter = forms.ChoiceField(
        choices=[
            ('all', 'All Statuses'),
            ('verified', 'Verified'),
            ('pending', 'Pending'),
            ('assigned', 'Mentor Assigned'),
            ('unassigned', 'No Mentor')
        ],
        initial='all',
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


# Formset for multiple academic records
AcademicRecordFormSet = forms.inlineformset_factory(
    UserProfile,
    AcademicRecord,
    form=AcademicRecordForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)


