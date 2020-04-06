from rest_framework.permissions import BasePermission


class UpdateTestPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method.lower() in ['put', 'patch'] and obj.published:
            return False
        return True
