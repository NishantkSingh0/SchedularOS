from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from core.models import UserProfile, Organization


class OrganizationMiddleware(MiddlewareMixin):
    """
    Middleware to attach organization to request based on JWT token.
    Extracts org_id from JWT and attaches Organization instance as request.org.
    """
    
    def process_request(self, request):
        # Skip if already has org (e.g., from tests)
        if hasattr(request, 'org'):
            return
        
        # Try to get user from JWT
        user = self.get_user_from_request(request)
        
        if user and not isinstance(user, AnonymousUser):
            # Get user profile
            try:
                profile = UserProfile.objects.select_related('org').get(user=user)
                request.org = profile.org
            except UserProfile.DoesNotExist:
                request.org = None
        else:
            request.org = None
    
    def get_user_from_request(self, request):
        """Extract user from JWT token"""
        authenticator = JWTAuthentication()
        try:
            result = authenticator.authenticate(request)
            if result:
                return result[0]
            return None
        except (InvalidToken, AuthenticationFailed):
            return None
