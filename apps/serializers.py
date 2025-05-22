from rest_framework.serializers import *
from django.contrib.auth.models import User
from .models import UserProfile


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        UserProfile.objects.create(user=user)
        return user


class UserProfileSerializer(ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['position', 'skills', 'experience_years']


class GenerateQuestionsSerializer(Serializer):
    position = CharField(max_length=100, required=True)
    skills = ListField(child=CharField(), required=True, allow_empty=False)
    experience_years = IntegerField(min_value=0, max_value=50, required=True)

    def validate_position(self, value):
        if not value.strip():
            raise ValidationError("Position cannot be empty.")
        return value.strip()

    def validate_skills(self, value):
        if not value:
            raise ValidationError("Skills cannot be empty.")
        skills = [skill.strip().lower() for skill in value if skill.strip()]
        if len(skills) != len(set(skills)):
            raise ValidationError("Skills must be unique.")
        return skills

    def get_prompt(self):
        skills_str = ", ".join(self.validated_data['skills'])
        return (
            f"You are an expert software interviewer. Generate 30 interview questions for a {self.validated_data['position']} "
            f"with {self.validated_data['experience_years']} years of experience and skills in: {skills_str}. "
            "Include a mix of technical questions (e.g., coding, system design), behavioral questions (e.g., teamwork, problem-solving), "
            "and role-specific questions tailored to the position and skills. "
            "Ensure questions are clear, concise, and relevant to the candidate's experience level. "
            "Return the questions in a numbered list format (e.g., '1. Question text')."
        )