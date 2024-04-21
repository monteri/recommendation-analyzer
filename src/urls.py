from django.urls import path
from . import views

urlpatterns = [
    path('log_activity/', views.log_activity, name='log_activity'),
    path('get_data/', views.get_data),
    path('popular_items/', views.popular_items, name='popular_items'),
    path('get_recommendations/', views.get_user_recommendations),
    path('get_content_based_recommendations/', views.get_content_based_recommendations)
]
