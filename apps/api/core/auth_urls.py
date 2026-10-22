from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from core.models import UserProfile, Organization


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """Register a new user and organization"""
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email')
    org_name = request.data.get('org_name')
    
    if not all([username, password, email, org_name]):
        return Response(
            {"error": "Missing required fields"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if user exists
    if User.objects.filter(username=username).exists():
        return Response(
            {"error": "Username already exists"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create user
    user = User.objects.create_user(
        username=username,
        password=password,
        email=email
    )
    
    # Create organization
    org = Organization.objects.create(
        name=org_name,
        slug=org_name.lower().replace(' ', '-')
    )
    
    # Create user profile
    UserProfile.objects.create(
        user=user,
        org=org,
        role='admin'
    )
    
    return Response({
        "message": "Registration successful",
        "user_id": str(user.id),
        "org_id": str(org.id)
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    """Get current user info"""
    from core.serializers import UserProfileSerializer
    
    profile = UserProfile.objects.get(user=request.user)
    serializer = UserProfileSerializer(profile)
    return Response(serializer.data)


urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', register, name='register'),
    path('me/', me, name='me'),
]
