from django.urls import path
from . import views

app_name = 'prd_analyzer'

urlpatterns = [
    # Page routes
    path('', views.prd_analyzer, name='prd_analyzer'),
    path('prd_analyzer/', views.prd_analyzer, name='prd_analyzer'),

    # API routes
]