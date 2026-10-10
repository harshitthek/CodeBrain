from django.db import models
from django.contrib.auth.models import User

class TestCase(models.Model):
    """Test Case Model"""
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    BU_CHOICES = [
        ('education', 'Education'),
        ('user_center', 'User Center'),
        ('collaboration', 'Collaboration'),
        ('im', 'IM'),
        ('workspace', 'Workspace'),
        ('recruitment', 'Recruitment'),
        ('work_management', 'Work Management'),
        ('ai_application', 'AI Application'),
        ('operation_platform', 'Operations Platform'),
    ]
    
    PRIORITY_CHOICES = [
        ('p0', 'P0'),
        ('p1', 'P1'),
        ('p2', 'P2'),
        ('p3', 'P3'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Test Case Title")
    description = models.TextField(verbose_name="Test Case Description")
    requirements = models.TextField(verbose_name="Requirements Description", blank=True)
    code_snippet = models.TextField(verbose_name="Code Snippet", blank=True)
    test_steps = models.TextField(verbose_name="Test Steps")
    expected_results = models.TextField(verbose_name="Expected Results")
    actual_results = models.TextField(verbose_name="Actual Results", blank=True)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name="Review Status"
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='created_testcases',
        verbose_name="Created By",
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    llm_provider = models.CharField(max_length=50, null=True, blank=True)
    bu = models.CharField(max_length=50, choices=BU_CHOICES, blank=True, verbose_name='BU')
    feature = models.CharField(max_length=100, blank=True, verbose_name='Feature')
    priority = models.CharField(max_length=2, choices=PRIORITY_CHOICES, blank=True, verbose_name='Priority')
    
    def __str__(self):
        return (
            f"Description:\n{self.description}\n\n"
            f"Test Steps:\n{self.test_steps}\n\n"
            f"Expected Results:\n{self.expected_results}\n"
        )
    
    class Meta:
        verbose_name = "Test Case"
        verbose_name_plural = "Test Cases"

class TestCaseReview(models.Model):
    """Test Case Review Record"""
    test_case = models.ForeignKey(
        TestCase, 
        on_delete=models.CASCADE, 
        related_name='reviews',
        verbose_name="Test Case"
    )
    reviewer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='reviews',
        verbose_name="Reviewer",
        null=True,
        blank=True
    )
    review_comments = models.TextField(verbose_name="Review Comments")
    review_date = models.DateTimeField(auto_now_add=True, verbose_name="Review Date")
    
    def __str__(self):
        return f"Review for {self.test_case.title}"
    
    class Meta:
        verbose_name = "Test Case Review"
        verbose_name_plural = "Test Case Reviews"

class KnowledgeBase(models.Model):
    """Knowledge Base Entry"""
    title = models.CharField(max_length=200, verbose_name="Title")
    content = models.TextField(verbose_name="Content")
    vector_id = models.CharField(max_length=100, blank=True, verbose_name="Vector ID")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "Knowledge Base"
        verbose_name_plural = "Knowledge Bases"