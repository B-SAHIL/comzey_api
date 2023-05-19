from rest_framework import permissions

class IsBuilder(permissions.BasePermission):
    def has_permissions(self, request, view):
        if request.user.user_type=="builder":
            return True
        return False
class IsWorker(permissions.BasePermission):
    def has_permissions(self, request, view):
        if request.user.user_type=="worker":
            return True
        return False
class IsClient(permissions.BasePermission):
    def has_permissions(self, request, view):
        if request.user.user_type=="client":
            return True
        return False