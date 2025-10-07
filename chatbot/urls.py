from django.urls import path
from . import views

urlpatterns = [
    path('ask/', views.chatbot_response, name='chatbot_response'),
]
