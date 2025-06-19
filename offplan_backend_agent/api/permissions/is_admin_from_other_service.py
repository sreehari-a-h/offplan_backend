from rest_framework.permissions import BasePermission
import jwt

class IsAdminFromOtherService(BasePermission):
    def has_permission(self, request, view):
        token = request.headers.get('Authorization', '').split('Bearer ')[-1]

        if not token:
            return False

        try:
            payload = jwt.decode(token, 'your-secret-key', algorithms=['HS256'])
            return payload.get('role') == 'admin'  # or however your other backend marks admins
        except jwt.ExpiredSignatureError:
            return False
        except jwt.InvalidTokenError:
            return False
