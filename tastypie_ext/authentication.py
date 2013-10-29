from django.contrib.auth import authenticate, login

from tastypie.authentication import Authentication
from tastypie.http import HttpUnauthorized

class FacebookOAUTH2Authentication(Authentication):
    """
    Handles authentication delegating to Facebook OAuth 2.0,
    using the Django-facebook package.
    
    See tastypie_ext.resources.GETAPIFacebookTokenAuthenticationResource
    for more documentation on the typical flow using this.
    
    """

    def is_authenticated(self, request, **kwargs):
        """
        Authenticate with facebook, and return
        user upon success.
        
        """

        # Make sure user supplied access token in request
        try:
            access_token = request.GET['access_token']
        except KeyError:
            return self._unauthorized()

        # Authenticate with facebook
        from open_facebook import OpenFacebook
        from django_facebook.connect import connect_user

        facebook = OpenFacebook(access_token)

        try:
            if not facebook or \
                not facebook.is_authenticated():
                return self._unauthorized()
        except:
            return self._unauthorized()
        
        
        # Facebook authenticated, now associate
        # with own internal user, Creating a new user if 
        # necessary.
        action, user = connect_user(request, access_token, facebook)
        request.user = user
  
        return True
    

    def _unauthorized(self):
        response = HttpUnauthorized()
        return response
        


 
class ApiTokenAuthentication(Authentication):
    """
    Handles API Token auth, in which an user provide just a temporary
    token using the 'HTTP-X' headers.
    """

    def _unauthorized(self):
        response = HttpUnauthorized()
        response['WWW-Authenticate'] = 'Token'
        return response

    def is_authenticated(self, request, **kwargs):
        """
        Finds the user with the API Token.
        """

        if not request.META.get('HTTP_AUTHORIZATION'):
            return self._unauthorized()

        try:
            http_authorization = request.META['HTTP_AUTHORIZATION']
            (auth_type, data) = http_authorization.split(' ', 1)

            if auth_type != 'Token':
                return self._unauthorized()
        except:
            return self._unauthorized()

        # Get api_token.
        from tastypie_ext.models import ApiToken

        try:
            api_token = ApiToken.objects.get(token=data)
        except ApiToken.DoesNotExist:
            return self._unauthorized()

        # Check if still valid.
        if not api_token.is_valid():
            return self._unauthorized()

        request.user = api_token.user
        return True
