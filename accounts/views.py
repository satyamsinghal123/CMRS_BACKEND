from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CMRSObtainPairSerializer


class CMRSObtainPairView(TokenObtainPairView):
    serializer_class = CMRSObtainPairSerializer
