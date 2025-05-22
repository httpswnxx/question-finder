from django.urls import path
from .views import *

urlpatterns = [
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/signup/', SignupView.as_view(), name='signup'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('generate-questions/', GenerateInterviewQuestionsView.as_view(), name='generate-questions'),
]