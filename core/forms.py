from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field, Div, HTML
from .models import ContactMessage, Newsletter, BlogComment
import re


class ContactForm(forms.ModelForm):
    """Enhanced contact form with Tailwind CSS styling and validation"""
    
    # Honeypot field for spam protection
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'style': 'display:none;',
            'tabindex': '-1',
            'autocomplete': 'off'
        })
    )
    
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'subject', 'message', 'budget', 'timeline']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 dark:border-gray-600 rounded-lg focus:border-blue-500 focus:outline-none transition-colors dark:bg-gray-800 dark:text-white',
                'placeholder': 'Your Full Name *',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 dark:border-gray-600 rounded-lg focus:border-blue-500 focus:outline-none transition-colors dark:bg-gray-800 dark:text-white',
                'placeholder': 'your.email@example.com *',
                'required': True
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 dark:border-gray-600 rounded-lg focus:border-blue-500 focus:outline-none transition-colors dark:bg-gray-800 dark:text-white',
                'placeholder': '+1 (555) 123-4567 (optional)',
                'type': 'tel'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 dark:border-gray-600 rounded-lg focus:border-blue-500 focus:outline-none transition-colors dark:bg-gray-800 dark:text-white',
                'placeholder': 'What would you like to discuss? *',
                'required': True
            }),
            'budget': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 dark:border-gray-600 rounded-lg focus:border-blue-500 focus:outline-none transition-colors dark:bg-gray-800 dark:text-white',
            }, choices=[
                ('', 'Select Budget Range (optional)'),
                ('< $5,000', 'Less than $5,000'),
                ('$5,000 - $10,000', '$5,000 - $10,000'),
                ('$10,000 - $25,000', '$10,000 - $25,000'),
                ('$25,000 - $50,000', '$25,000 - $50,000'),
                ('$50,000+', '$50,000+'),
                ('Not sure', 'Not sure yet'),
            ]),
            'timeline': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 dark:border-gray-600 rounded-lg focus:border-blue-500 focus:outline-none transition-colors dark:bg-gray-800 dark:text-white',
            }, choices=[
                ('', 'Expected Timeline (optional)'),
                ('ASAP', 'As soon as possible'),
                ('1-2 weeks', '1-2 weeks'),
                ('1 month', '1 month'),
                ('2-3 months', '2-3 months'),
                ('3+ months', '3+ months'),
                ('Flexible', 'Flexible'),
            ]),
            'message': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 dark:border-gray-600 rounded-lg focus:border-blue-500 focus:outline-none transition-colors resize-none dark:bg-gray-800 dark:text-white',
                'placeholder': 'Tell me about your project, ideas, or questions... *',
                'rows': 6,
                'required': True
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'space-y-4'
        
        # Add labels
        self.fields['name'].label = 'Full Name'
        self.fields['email'].label = 'Email Address'
        self.fields['phone'].label = 'Phone Number'
        self.fields['subject'].label = 'Subject'
        self.fields['budget'].label = 'Project Budget'
        self.fields['timeline'].label = 'Timeline'
        self.fields['message'].label = 'Message'
    
    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if len(name) < 2:
            raise forms.ValidationError('Please enter your full name.')
        if not re.match(r'^[a-zA-Z\s\-\'\.]+$', name):
            raise forms.ValidationError('Name contains invalid characters.')
        return name
    
    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        
        # Check for disposable email domains
        disposable_domains = [
            'tempmail.com', 'throwaway.email', '10minutemail.com',
            'guerrillamail.com', 'mailinator.com'
        ]
        
        domain = email.split('@')[1] if '@' in email else ''
        if domain in disposable_domains:
            raise forms.ValidationError('Please use a permanent email address.')
        
        return email
    
    def clean_message(self):
        message = self.cleaned_data.get('message', '').strip()
        if len(message) < 10:
            raise forms.ValidationError('Please provide more details (at least 10 characters).')
        if len(message) > 2000:
            raise forms.ValidationError('Message is too long (maximum 2000 characters).')
        
        # Check for spam patterns
        spam_patterns = [
            r'viagra|cialis|pharmacy',
            r'click here|buy now',
            r'winner|congratulations.*prize',
        ]
        
        for pattern in spam_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                raise forms.ValidationError('Your message contains prohibited content.')
        
        return message


class NewsletterForm(forms.ModelForm):
    """Enhanced newsletter subscription form"""
    
    class Meta:
        model = Newsletter
        fields = ['email', 'name']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'flex-1 px-6 py-4 rounded-full text-gray-900 dark:text-white dark:bg-gray-800 border-2 border-white dark:border-gray-600 focus:outline-none focus:ring-4 focus:ring-white/50',
                'placeholder': 'Enter your email address',
                'required': True
            }),
            'name': forms.TextInput(attrs={
                'class': 'w-full px-6 py-4 rounded-full text-gray-900 dark:text-white dark:bg-gray-800 border-2 border-gray-300 dark:border-gray-600 focus:outline-none focus:ring-4 focus:ring-blue-500/50',
                'placeholder': 'Your name (optional)'
            }),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        
        # Validate email format
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise forms.ValidationError('Please enter a valid email address.')
        
        # Check if already subscribed and active
        if Newsletter.objects.filter(email=email, is_active=True).exists():
            raise forms.ValidationError('This email is already subscribed.')
        
        return email


class BlogCommentForm(forms.ModelForm):
    """Blog comment form with moderation"""
    
    class Meta:
        model = BlogComment
        fields = ['name', 'email', 'website', 'content']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 dark:border-gray-600 rounded-lg focus:border-blue-500 focus:outline-none transition-colors dark:bg-gray-800 dark:text-white',
                'placeholder': 'Your Name *',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 dark:border-gray-600 rounded-lg focus:border-blue-500 focus:outline-none transition-colors dark:bg-gray-800 dark:text-white',
                'placeholder': 'your.email@example.com *',
                'required': True
            }),
            'website': forms.URLInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 dark:border-gray-600 rounded-lg focus:border-blue-500 focus:outline-none transition-colors dark:bg-gray-800 dark:text-white',
                'placeholder': 'https://yourwebsite.com (optional)'
            }),
            'content': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 dark:border-gray-600 rounded-lg focus:border-blue-500 focus:outline-none transition-colors resize-none dark:bg-gray-800 dark:text-white',
                'placeholder': 'Share your thoughts... *',
                'rows': 5,
                'required': True
            }),
        }
    
    def clean_content(self):
        content = self.cleaned_data.get('content', '').strip()
        
        if len(content) < 5:
            raise forms.ValidationError('Comment must be at least 5 characters long.')
        
        if len(content) > 1000:
            raise forms.ValidationError('Comment is too long (maximum 1000 characters).')
        
        # Check for spam patterns
        if re.search(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content):
            # Has links - might be spam, will need manual approval
            pass
        
        return content


class QuickContactForm(forms.Form):
    """Quick contact form for modals/popups"""
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-300 dark:border-gray-600 rounded-lg focus:border-blue-500 focus:outline-none transition-colors dark:bg-gray-800 dark:text-white',
            'placeholder': 'Your Name *'
        })
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-300 dark:border-gray-600 rounded-lg focus:border-blue-500 focus:outline-none transition-colors dark:bg-gray-800 dark:text-white',
            'placeholder': 'your.email@example.com *'
        })
    )
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-300 dark:border-gray-600 rounded-lg focus:border-blue-500 focus:outline-none transition-colors resize-none dark:bg-gray-800 dark:text-white',
            'placeholder': 'Quick message... *',
            'rows': 4
        })
    )