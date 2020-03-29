from rest_framework.permissions import IsAuthenticated


class AuthRequiredForCreation(IsAuthenticated):
    def has_permission(self, request, view):
        if request.method.lower() in ['post', 'patch', 'put', 'delete']:
            return bool(request.user and request.user.is_authenticated)
        return True
