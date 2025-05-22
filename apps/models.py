from django.db.models import *
from django.contrib.auth.models import User

class UserProfile(Model):
    user = OneToOneField(User, on_delete=CASCADE, related_name='profile')
    position = CharField(max_length=100, blank=True)
    skills = TextField(blank=True)
    experience_years = PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.user.username}'s Profile"