from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static

from .views import (
    UsuarioViewSet, CategoriaViewSet, ProductoViewSet,
    InventarioViewSet, AlertaStockViewSet, ReporteViewSet,
    CustomTokenObtainPairView, enviar_contacto  # 👈 IMPORTANTE
)

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet, basename='usuario')
router.register(r'categorias', CategoriaViewSet, basename='categoria')
router.register(r'productos', ProductoViewSet, basename='producto')
router.register(r'inventario', InventarioViewSet, basename='inventario')
router.register(r'alertas', AlertaStockViewSet, basename='alerta')
router.register(r'reportes', ReporteViewSet, basename='reporte')

urlpatterns = [
    path('', include(router.urls)),
    path('contacto/', enviar_contacto),

    # 🔐 JWT AUTH (ESTO TE FALTABA)
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
]