from django.urls import path
from . import views

app_name = 'test_case_generator'

urlpatterns = [
    # Page routes
    path('', views.generate, name='generate'),

    # API routes
    path('save-test-case/', views.save_test_case, name='save_test_case'),
]