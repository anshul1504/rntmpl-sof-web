from django import forms
import re

from apps.publicsite.models import (
    ContactSubmission,
    JobApplication,
    JobOpening,
    PartnerEnquiry,
    SponsorEnquiry,
    PlayerPaymentTransaction,
)


class ContactSubmissionForm(forms.ModelForm):
    ENQUIRY_CHOICES = (
        ('Player Registration', 'Player Registration'),
        ('Trials & Selection', 'Trials & Selection'),
        ('Tournament & Matches', 'Tournament & Matches'),
        ('Partnership & Sponsorship', 'Partnership & Sponsorship'),
        ('Technical Support', 'Technical Support'),
        ('General Enquiry', 'General Enquiry'),
    )
    enquiry_type = forms.ChoiceField(choices=ENQUIRY_CHOICES)

    class Meta:
        model = ContactSubmission
        fields = ('name', 'email', 'phone', 'subject', 'message')
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Your full name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'name@example.com'}),
            'phone': forms.TextInput(attrs={'placeholder': '+91 98765 43210'}),
            'subject': forms.TextInput(attrs={'placeholder': 'How can we help?'}),
            'message': forms.Textarea(attrs={'placeholder': 'Write your message here...', 'rows': 6}),
        }

    field_order = ('name', 'email', 'phone', 'enquiry_type', 'subject', 'message')

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.subject = f"[{self.cleaned_data['enquiry_type']}] {instance.subject}"
        if commit:
            instance.save()
        return instance

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if len(name) < 2:
            raise forms.ValidationError('Please enter your full name.')
        if not re.fullmatch(r"[A-Za-zÀ-ÿ.' -]+", name):
            raise forms.ValidationError('Name can only contain letters and common punctuation.')
        return name

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if phone and not re.fullmatch(r'\+?[0-9 ()-]{7,20}', phone):
            raise forms.ValidationError('Please enter a valid phone number.')
        return phone

    def clean_subject(self):
        subject = self.cleaned_data['subject'].strip()
        if len(subject) < 3:
            raise forms.ValidationError('Please enter a clear subject.')
        return subject

    def clean_message(self):
        message = self.cleaned_data['message'].strip()
        if len(message) < 20:
            raise forms.ValidationError('Please enter at least 20 characters.')
        if len(message) > 3000:
            raise forms.ValidationError('Message cannot exceed 3000 characters.')
        return message


class PartnerEnquiryForm(forms.ModelForm):
    class Meta:
        model = PartnerEnquiry
        fields = (
            'organisation_name', 'contact_person', 'email', 'phone',
            'partner_type', 'website', 'city', 'message',
        )
        widgets = {
            'organisation_name': forms.TextInput(attrs={'placeholder': 'Organisation or brand name'}),
            'contact_person': forms.TextInput(attrs={'placeholder': 'Contact person'}),
            'email': forms.EmailInput(attrs={'placeholder': 'name@company.com'}),
            'phone': forms.TextInput(attrs={'placeholder': '+91 98765 43210'}),
            'website': forms.URLInput(attrs={'placeholder': 'https://example.com'}),
            'city': forms.TextInput(attrs={'placeholder': 'City'}),
            'message': forms.Textarea(attrs={'placeholder': 'Tell us about your partnership proposal...', 'rows': 6}),
        }

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip()
        if not re.fullmatch(r'\+?[0-9 ()-]{7,20}', phone):
            raise forms.ValidationError('Please enter a valid phone number.')
        return phone

    def clean_message(self):
        message = self.cleaned_data['message'].strip()
        if len(message) < 30:
            raise forms.ValidationError('Please enter at least 30 characters.')
        return message


class SponsorEnquiryForm(forms.ModelForm):
    class Meta:
        model = SponsorEnquiry
        fields = ('company_name', 'contact_person', 'email', 'phone', 'website', 'industry', 'budget_range', 'objectives')
        widgets = {
            'company_name': forms.TextInput(attrs={'placeholder': 'Company or brand name'}),
            'contact_person': forms.TextInput(attrs={'placeholder': 'Contact person'}),
            'email': forms.EmailInput(attrs={'placeholder': 'name@company.com'}),
            'phone': forms.TextInput(attrs={'placeholder': '+91 98765 43210'}),
            'website': forms.URLInput(attrs={'placeholder': 'https://example.com'}),
            'industry': forms.TextInput(attrs={'placeholder': 'Industry'}),
            'objectives': forms.Textarea(attrs={'placeholder': 'Tell us about your campaign goals and sponsorship interests...', 'rows': 6}),
        }

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip()
        if not re.fullmatch(r'\+?[0-9 ()-]{7,20}', phone):
            raise forms.ValidationError('Please enter a valid phone number.')
        return phone

    def clean_objectives(self):
        objectives = self.cleaned_data['objectives'].strip()
        if len(objectives) < 30:
            raise forms.ValidationError('Please enter at least 30 characters.')
        return objectives


class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = (
            'job', 'full_name', 'email', 'phone', 'city', 'experience_years',
            'current_role', 'linkedin_url', 'resume', 'cover_note',
        )
        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'Your full name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'name@example.com'}),
            'phone': forms.TextInput(attrs={'placeholder': '+91 98765 43210'}),
            'city': forms.TextInput(attrs={'placeholder': 'City'}),
            'experience_years': forms.NumberInput(attrs={'min': 0, 'max': 50}),
            'current_role': forms.TextInput(attrs={'placeholder': 'Current role'}),
            'linkedin_url': forms.URLInput(attrs={'placeholder': 'LinkedIn profile'}),
            'resume': forms.FileInput(attrs={'accept': '.pdf,.doc,.docx'}),
            'cover_note': forms.Textarea(attrs={'placeholder': 'Why would you like to join RNTMPL?', 'rows': 6}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['job'].queryset = JobOpening.objects.filter(is_active=True)
        self.fields['job'].empty_label = 'General Application'

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip()
        if not re.fullmatch(r'\+?[0-9 ()-]{7,20}', phone):
            raise forms.ValidationError('Please enter a valid phone number.')
        return phone

    def clean_resume(self):
        resume = self.cleaned_data['resume']
        if resume.size > 5 * 1024 * 1024:
            raise forms.ValidationError('Resume file cannot exceed 5 MB.')
        extension = resume.name.rsplit('.', 1)[-1].lower()
        if extension not in {'pdf', 'doc', 'docx'}:
            raise forms.ValidationError('Upload a PDF, DOC or DOCX file.')
        return resume

    def clean_cover_note(self):
        note = self.cleaned_data['cover_note'].strip()
        if len(note) < 30:
            raise forms.ValidationError('Please enter at least 30 characters.')
        return note


class PlayerJourneyPersonalForm(forms.Form):
    full_name = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'placeholder': 'Your full name'}))
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    gender = forms.ChoiceField(choices=(('MALE', 'Male'), ('FEMALE', 'Female'), ('OTHER', 'Other')))
    phone = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'placeholder': '+91 mobile number'}))
    city = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Your city'}))
    state = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Your state'}))


class PlayerJourneyCricketForm(forms.Form):
    role = forms.ChoiceField(choices=(('BATTER','Batter'),('BOWLER','Bowler'),('ALL_ROUNDER','All Rounder'),('WICKET_KEEPER','Wicket Keeper'),('BATTER_WK','Batter & Wicket Keeper'),('BOWLING_AR','Bowling All Rounder'),('BATTING_AR','Batting All Rounder')))
    batting_style = forms.ChoiceField(choices=(('RIGHT_HAND','Right Handed'),('LEFT_HAND','Left Handed')))
    bowling_style = forms.ChoiceField(required=False, choices=(('','Not applicable'),('RA_FAST','Right Arm Fast'),('RA_FAST_MEDIUM','Right Arm Fast Medium'),('RA_MEDIUM','Right Arm Medium'),('RA_OFF_BREAK','Right Arm Off Break'),('RA_LEG_BREAK','Right Arm Leg Break'),('LA_FAST','Left Arm Fast'),('LA_FAST_MEDIUM','Left Arm Fast Medium'),('LA_MEDIUM','Left Arm Medium'),('LA_ORTHODOX','Left Arm Orthodox'),('LA_CHINAMAN','Left Arm Chinaman')))
    is_wicket_keeper = forms.BooleanField(required=False, label='I can keep wickets')
    jersey_number = forms.IntegerField(required=False, min_value=0, max_value=999)
    height_cm = forms.DecimalField(required=False, min_value=80, max_value=250)
    weight_kg = forms.DecimalField(required=False, min_value=20, max_value=250)


class PlayerJourneyExperienceForm(forms.Form):
    playing_experience = forms.IntegerField(min_value=0, max_value=60, label='Years of playing experience')
    academy_or_club = forms.CharField(required=False, max_length=180, label='Academy / Club / School')
    highest_level = forms.ChoiceField(choices=(('BEGINNER','Starting my cricket journey'),('SCHOOL','School'),('ACADEMY','Academy / Club'),('DISTRICT','District'),('STATE','State'),('NATIONAL','National'),('PROFESSIONAL','Professional')))
    achievements = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows':4,'placeholder':'Tell us about your best performances or achievements'}))
    emergency_contact_name = forms.CharField(max_length=120)
    emergency_contact_phone = forms.CharField(max_length=30)
    consent_accepted = forms.BooleanField(label='I confirm that the information provided is correct.')


class PaymentReferenceForm(forms.Form):
    payment_reference = forms.CharField(max_length=120, label='Payment / Transaction Reference', widget=forms.TextInput(attrs={'placeholder':'Enter UTR or transaction reference'}))

    def clean_payment_reference(self):
        reference = self.cleaned_data['payment_reference'].strip().upper()
        if len(reference) < 6:
            raise forms.ValidationError('Enter a valid payment reference.')
        if PlayerPaymentTransaction.objects.filter(reference__iexact=reference).exists():
            raise forms.ValidationError('This payment reference has already been submitted.')
        return reference
