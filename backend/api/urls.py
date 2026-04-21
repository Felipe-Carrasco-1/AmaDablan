from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    UsuarioViewSet, CategoriaViewSet, ProductoViewSet,
    InventarioViewSet, AlertaStockViewSet, ReporteViewSet,
    CustomTokenObtainPairView, enviar_contacto, PedidoViewSet,
    recuperar_password, reset_password, SucursalViewSet, CajaViewSet, MovimientoStockViewSet
)

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet, basename='usuario')
router.register(r'categorias', CategoriaViewSet, basename='categoria')
router.register(r'productos', ProductoViewSet, basename='producto')
router.register(r'inventario', InventarioViewSet, basename='inventario')
router.register(r'alertas', AlertaStockViewSet, basename='alerta')
router.register(r'reportes', ReporteViewSet, basename='reporte')
router.register(r'pedidos', PedidoViewSet, basename='pedido')
router.register(r'sucursales', SucursalViewSet, basename='sucursal')
router.register(r'cajas', CajaViewSet, basename='caja')
router.register(r'movimientos', MovimientoStockViewSet, basename='movimiento')

urlpatterns = [
    # 🔑 RECUPERACIÓN (Mover arriba para evitar conflicto con router)
    path('usuarios/recuperar-password/', recuperar_password),
    path('usuarios/reset-password/', reset_password),

    path('', include(router.urls)),
    path('contacto/', enviar_contacto),

    # 🔐 JWT AUTH
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]