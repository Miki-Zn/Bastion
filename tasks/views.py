from rest_framework import viewsets, permissions
from .models import Task
from .serializers import TaskSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .throttling import LoginRateThrottle
import logging
from .utils import get_client_ip

security_logger = logging.getLogger('security')

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class ThrottledTokenObtainPairView(TokenObtainPairView):
    throttle_classes = [LoginRateThrottle]

    def post(self, request, *args, **kwargs):
        ip = get_client_ip(request)
        username = request.data.get('username', 'unknown')

        try:
            response = super().post(request, *args, **kwargs)
        except Exception:
            security_logger.warning(f"Failed login attempt: username={username} ip={ip}")
            raise

        security_logger.info(f"Successful login: username={username} ip={ip}")
        return response