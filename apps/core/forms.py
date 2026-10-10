from django import forms
from .models import TestCase, KnowledgeBase

class TestCaseForm(forms.ModelForm):
    """Test Case Form"""
    class Meta:
        model = TestCase
        fields = ['title', 'description', 'requirements', 'code_snippet', 
                 'test_steps', 'expected_results']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'requirements': forms.Textarea(attrs={'rows': 5}),
            'code_snippet': forms.Textarea(attrs={'rows': 8, 'class': 'code-editor'}),
            'test_steps': forms.Textarea(attrs={'rows': 8}),
            'expected_results': forms.Textarea(attrs={'rows': 5}),
        }

class TestCaseReviewForm(forms.Form):
    """Test Case Review Form"""
    comments = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5}),
        label="Review Comments"
    )
    status = forms.ChoiceField(
        choices=[
            ('approved', 'Approved'),
            ('rejected', 'Rejected')
        ],
        label="Review Result"
    )

class KnowledgeBaseForm(forms.ModelForm):
    """Knowledge Base Entry Form"""
    class Meta:
        model = KnowledgeBase
        fields = ['title', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10}),
        }