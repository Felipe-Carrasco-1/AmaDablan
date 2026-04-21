from django.db.models import Count
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth import get_user_model

from rest_framework import viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import (
    Usuario, Categoria, Producto,
    Inventario, Reporte, AlertaStock, Pedido, DetallePedido
)

from .serializers import (
    CustomTokenObtainPairSerializer,
    UsuarioSerializer,
    CategoriaSerializer,
    ProductoSerializer,
    ProductoCreateSerializer,
    InventarioSerializer,
    AlertaStockSerializer,
    ReporteSerializer,
    PedidoSerializer
)

from .permissions import IsAdminUser, IsAdminOrReadOnly


# =========================
# AUTH
# =========================
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]


# =========================
# CONTACTO
# =========================
@api_view(['POST'])
@permission_classes([AllowAny])
def enviar_contacto(request):
    nombre = request.data.get('nombre', '').strip()
    email = request.data.get('email', '').strip()
    mensaje = request.data.get('mensaje', '').strip()

    if not nombre or not email or not mensaje:
        return Response({'error': 'Todos los campos son obligatorios'}, status=400)

    send_mail(
        subject=f'Contacto — {nombre}',
        message=f'Nombre: {nombre}\nEmail: {email}\n\n{mensaje}',
        from_email='contacto@amadablam.com',
        recipient_list=['contacto@amadablam.com'],
    )

    return Response({'mensaje': 'Enviado correctamente'})


# =========================
# USUARIOS
# =========================
class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all().order_by('-id')
    serializer_class = UsuarioSerializer
    permission_classes = [IsAdminUser]


# =========================
# CATEGORIAS
# =========================
class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [IsAdminOrReadOnly]


# =========================
# PRODUCTOS
# =========================
class ProductoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = Producto.objects.all()

        categoria = self.request.query_params.get('categoria')
        estado = self.request.query_params.get('estado')

        if categoria:
            queryset = queryset.filter(categoria_id=categoria)

        if estado is not None:
            if estado.lower() == 'true':
                queryset = queryset.filter(estado=True)
            elif estado.lower() == 'false':
                queryset = queryset.filter(estado=False)

        return queryset

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ProductoCreateSerializer
        return ProductoSerializer

    @action(detail=True, methods=['patch'])
    def actualizar_stock(self, request, pk=None):
        producto = self.get_object()
        cantidad = int(request.data.get('cantidad', 0))

        producto.stock += cantidad

        if producto.stock < 0:
            producto.stock = 0

        producto.save()

        return Response({
            "mensaje": "Stock actualizado",
            "stock": producto.stock
        })


# =========================
# INVENTARIO (🔥 FIX ALERTAS REALES)
# =========================
class InventarioViewSet(viewsets.ModelViewSet):
    queryset = Inventario.objects.select_related('producto')
    serializer_class = InventarioSerializer
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=['get'])
    def alertas_activas(self, request):

        alertas = AlertaStock.objects.filter(leida=False)

        data = [
            {
                "id": a.id,
                "producto": a.producto.nombre,
                "stock": a.producto.stock,
                "stock_minimo": a.producto.inventario.stock_minimo,
                "leida": a.leida
            }
            for a in alertas
        ]

        return Response(data)


# =========================
# ALERTAS
# =========================
class AlertaStockViewSet(viewsets.ModelViewSet):
    queryset = AlertaStock.objects.all()
    serializer_class = AlertaStockSerializer
    permission_classes = [IsAdminUser]

    @action(detail=True, methods=['patch'])
    def marcar_leida(self, request, pk=None):
        alerta = self.get_object()
        alerta.leida = True
        alerta.save()
        return Response({'leida': True})

    @action(detail=False, methods=['patch'])
    def marcar_todas_leidas(self, request):
        total = AlertaStock.objects.filter(leida=False).update(leida=True)

        return Response({
            'mensaje': 'Todas las alertas marcadas como leídas',
            'total_actualizadas': total
        })


# =========================
# REPORTES (🔥 FIX DASHBOARD REAL)
# =========================
class ReporteViewSet(viewsets.ModelViewSet):
    queryset = Reporte.objects.all().order_by('-id')
    serializer_class = ReporteSerializer
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        from django.utils import timezone

        inventarios = Inventario.objects.select_related('producto')

        productos_bajo_stock = [
            {
                "nombre": inv.producto.nombre,
                "stock": inv.producto.stock,
                "minimo": inv.stock_minimo
            }
            for inv in inventarios
            if inv.producto.stock <= inv.stock_minimo
        ]

        # Finanzas del día (Excluye cancelados)
        hoy = timezone.now().date()
        from datetime import datetime, time
        inicio_dia = timezone.make_aware(datetime.combine(hoy, time.min))
        fin_dia = timezone.make_aware(datetime.combine(hoy, time.max))
        
        pedidos_hoy = Pedido.objects.filter(fecha__range=(inicio_dia, fin_dia))
        
        # Ganancias: Solo los entregados (Ventas reales)
        ganancias_hoy = sum(p.total for p in pedidos_hoy if p.estado == 'entregado')
        
        # Pedidos Hoy: Todos los que no están cancelados (Flujo de trabajo)
        total_pedidos_hoy = pedidos_hoy.exclude(estado='cancelado').count()
        
        # Ticket promedio: Basado en ventas entregadas
        pedidos_entregados_count = pedidos_hoy.filter(estado='entregado').count()
        ticket_promedio = ganancias_hoy / pedidos_entregados_count if pedidos_entregados_count > 0 else 0

        return Response({
            "total_productos": Producto.objects.count(),
            "total_categorias": Categoria.objects.count(),
            "total_usuarios": Usuario.objects.count(),

            "alertas_no_leidas": len(productos_bajo_stock),

            "productos_sin_stock": Producto.objects.filter(stock=0).count(),

            "productos_por_categoria": list(
                Categoria.objects.annotate(total=Count('productos'))
                .values('nombre', 'total')
            ),

            "productos_bajo_stock": productos_bajo_stock,

            # Nuevas métricas financieras
            "ganancias_hoy": ganancias_hoy,
            "total_pedidos_hoy": total_pedidos_hoy,
            "ticket_promedio": ticket_promedio
        })

    @action(detail=False, methods=['post'])
    def generar(self, request):

        tipo = request.data.get('tipo')

        if not tipo:
            return Response({'error': 'Debe enviar tipo de reporte'}, status=400)

        datos = {}

        if tipo == 'productos':
            datos['items'] = [
                {
                    "nombre": p["nombre"],
                    "precio": float(p["precio"]),
                    "stock": p["stock"]
                }
                for p in Producto.objects.values('nombre', 'precio', 'stock')
            ]

        elif tipo == 'categorias':
            datos['items'] = list(
                Categoria.objects.annotate(total=Count('productos'))
                .values('nombre', 'total')
            )

        elif tipo in ['stock', 'inventario']:
            datos['items'] = [
                {
                    "producto": inv.producto.nombre,
                    "stock": inv.producto.stock,
                    "stock_minimo": inv.stock_minimo
                }
                for inv in Inventario.objects.select_related('producto')
            ]

        else:
            return Response({'error': 'Tipo inválido'}, status=400)

        reporte = Reporte.objects.create(
            tipo=tipo,
            datos=datos,
            generado_por=request.user
        )

        return Response(ReporteSerializer(reporte).data, status=201)


# =========================
# PEDIDOS (CARRITO)
# =========================
class PedidoViewSet(viewsets.ModelViewSet):
    queryset = Pedido.objects.all().order_by('-fecha')
    serializer_class = PedidoSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsAdminUser()]

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def mis_pedidos(self, request):
        if not request.user.is_authenticated:
            return Response({'error': 'Debes iniciar sesión para ver tus pedidos'}, status=401)
        
        pedidos = Pedido.objects.filter(usuario=request.user).order_by('-fecha')
        serializer = self.get_serializer(pedidos, many=True)
        return Response(serializer.data)


# ─────────────────────────────────────────────
# RECUPERACIÓN DE CONTRASEÑA (EXTEND)
# ─────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def recuperar_password(request):
    email = request.data.get('email')
    if not email:
        return Response({'error': 'Email requerido'}, status=400)
    
    User = get_user_model()
    try:
        user = User.objects.get(email=email)
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Simulación en consola (Ya que no hay SMTP configurado)
        print(f"\n--- 📧 SIMULACIÓN DE RECUPERACIÓN ---")
        print(f"Para: {email}")
        print(f"Enlace para el frontend: http://localhost:4200/reset-password?uid={uid}&token={token}")
        print(f"------------------------------------\n")
        
        return Response({'mensaje': 'Se ha enviado un enlace de recuperación a tu correo.'})
    except User.DoesNotExist:
        # Por seguridad no revelamos si existe
        return Response({'mensaje': 'Se ha enviado un enlace de recuperación a tu correo.'})

@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    uid = request.data.get('uid')
    token = request.data.get('token')
    password = request.data.get('password')

    if not uid or not token or not password:
        return Response({'error': 'Datos incompletos'}, status=400)

    User = get_user_model()
    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)

        if default_token_generator.check_token(user, token):
            user.set_password(password)
            user.save()
            return Response({'mensaje': 'Contraseña actualizada con éxito.'})
        else:
            return Response({'error': 'El enlace es inválido o ha expirado.'}, status=400)
    except Exception:
        return Response({'error': 'Error procesando la solicitud.'}, status=400)