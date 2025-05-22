import openai
import os
from openai import APIError, RateLimitError
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema
from .serializers import UserSerializer, GenerateQuestionsSerializer, UserProfileSerializer
from .models import UserProfile


openai.api_key = os.getenv("OPENAI_API_KEY")


@extend_schema(tags=['auth'])
class LoginView(APIView):
    permission_classes = [AllowAny]
    serializer_class = UserSerializer

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        return Response({"error": "Invalid credentials"}, status=401)


@extend_schema(tags=['auth'])
class SignupView(APIView):
    permission_classes = [AllowAny]
    serializer_class = UserSerializer

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=201)
        return Response(serializer.errors, status=400)


@extend_schema(tags=['profile'])
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get(self, request):
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)

    def post(self, request):
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


@extend_schema(tags=['interviews'])
class GenerateInterviewQuestionsView(APIView):
    permission_classes = [AllowAny]
    serializer_class = GenerateQuestionsSerializer

    def post(self, request):
        if not request.data:
            try:
                profile = request.user.profile
                data = {
                    'position': profile.position,
                    'skills': profile.skills.split(',') if profile.skills else [],
                    'experience_years': profile.experience_years
                }
            except UserProfile.DoesNotExist:
                return Response({"error": "User profile not found. Please update your profile."}, status=400)
        else:
            data = request.data

        serializer = GenerateQuestionsSerializer(data=data)
        if serializer.is_valid():
            prompt = serializer.get_prompt()
            try:
                response = openai.chat.completions.create(
                    model=os.getenv("OPENAI_MODEL", "gpt-4"),
                    messages=[
                        ChatCompletionSystemMessageParam(
                            role="system",
                            content="You're an expert software interviewer. Return a numbered list of questions."
                        ),
                        ChatCompletionUserMessageParam(
                            role="user",
                            content=prompt
                        )
                    ],
                    max_tokens=1500
                )
                questions_text = response.choices[0].message.content
                questions = [q.strip() for q in questions_text.split('\n') if q.strip() and q[0].isdigit()]
                return Response({"questions": questions})
            except APIError as e:
                return Response({"error": f"OpenAI API error: {str(e)}"}, status=500)
            except RateLimitError:
                return Response({"error": "Rate limit exceeded for OpenAI API."}, status=429)
            except Exception as e:
                return Response({"error": f"Unexpected error: {str(e)}"}, status=500)
        return Response(serializer.errors, status=400)