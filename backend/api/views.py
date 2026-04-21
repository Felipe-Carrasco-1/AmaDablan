from django.db.models import Count
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth import get_user_model

from rest_framework import viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import (
    Usuario, Categoria, Producto,
    Inventario, Reporte, AlertaStock, Pedido, DetallePedido, Sucursal, Caja, MovimientoStock
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
    PedidoSerializer,
    DetallePedidoSerializer,
    SucursalSerializer,
    CajaSerializer,
    MovimientoStockSerializer
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
# SUCURSALES Y CAJAS
# =========================
class SucursalViewSet(viewsets.ModelViewSet):
    queryset = Sucursal.objects.all()
    serializer_class = SucursalSerializer
    permission_classes = [IsAdminOrReadOnly]

class CajaViewSet(viewsets.ModelViewSet):
    queryset = Caja.objects.all().order_by('-fecha_apertura')
    serializer_class = CajaSerializer
    permission_classes = [AllowAny] # Permiso manejado en vista/frontend por ahora

    @action(detail=False, methods=['post'])
    def abrir(self, request):
        usuario = request.user
        if not usuario.is_authenticated or not usuario.sucursal:
            return Response({'error': 'Usuario no tiene sucursal asignada o no autenticado'}, status=400)
        
        caja_abierta = Caja.objects.filter(sucursal=usuario.sucursal, estado='abierta').first()
        if caja_abierta:
            return Response({'error': 'Ya existe una caja abierta en esta sucursal'}, status=400)

        monto_inicial = request.data.get('monto_inicial', 0)
        caja = Caja.objects.create(
            sucursal=usuario.sucursal,
            usuario=usuario,
            monto_inicial=monto_inicial,
            estado='abierta'
        )
        return Response(CajaSerializer(caja).data, status=201)

    @action(detail=True, methods=['post'])
    def cerrar(self, request, pk=None):
        caja = self.get_object()
        if caja.estado == 'cerrada':
            return Response({'error': 'La caja ya está cerrada'}, status=400)
            
        monto_final = request.data.get('monto_final')
        from django.utils import timezone
        caja.estado = 'cerrada'
        caja.fecha_cierre = timezone.now()
        if monto_final is not None:
            caja.monto_final = monto_final
        caja.save()
        return Response(CajaSerializer(caja).data)


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
        sucursal_id = request.data.get('sucursal_id')
        
        if not sucursal_id:
             if request.user.is_authenticated and request.user.sucursal:
                 sucursal_id = request.user.sucursal.id
             else:
                 return Response({'error': 'Debe especificar sucursal_id'}, status=400)

        inv, _ = Inventario.objects.get_or_create(producto=producto, sucursal_id=sucursal_id)
        inv.actualizar_stock(cantidad)

        return Response({
            "mensaje": "Stock actualizado",
            "stock": inv.stock
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
        queryset = AlertaStock.objects.filter(leida=False)
        if request.user.is_authenticated and request.user.rol == 'encargado_stock' and request.user.sucursal:
            queryset = queryset.filter(sucursal=request.user.sucursal)

        data = []
        for a in queryset:
            inv = Inventario.objects.filter(producto=a.producto, sucursal=a.sucursal).first()
            if inv:
                data.append({
                    "id": a.id,
                    "producto": a.producto.nombre,
                    "sucursal": a.sucursal.nombre if a.sucursal else 'Global',
                    "stock": inv.stock,
                    "stock_minimo": inv.stock_minimo,
                    "leida": a.leida
                })

        return Response(data)


class MovimientoStockViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MovimientoStock.objects.select_related('producto', 'sucursal', 'usuario')
    serializer_class = MovimientoStockSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.rol in ['cajero', 'encargado_stock'] and user.sucursal:
            qs = qs.filter(sucursal=user.sucursal)
        return qs

# =========================
# ALERTAS
# =========================
class AlertaStockViewSet(viewsets.ModelViewSet):
    queryset = AlertaStock.objects.all()
    serializer_class = AlertaStockSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.rol in ['cajero', 'encargado_stock'] and user.sucursal:
            qs = qs.filter(sucursal=user.sucursal)
        return qs

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

        inventarios = Inventario.objects.select_related('producto', 'sucursal')
        if request.user.is_authenticated and request.user.rol in ['cajero', 'encargado_stock'] and request.user.sucursal:
            inventarios = inventarios.filter(sucursal=request.user.sucursal)

        productos_bajo_stock = [
            {
                "nombre": inv.producto.nombre,
                "sucursal": inv.sucursal.nombre if inv.sucursal else "Global",
                "stock": inv.stock,
                "minimo": inv.stock_minimo
            }
            for inv in inventarios
            if inv.stock <= inv.stock_minimo
        ]

        # Finanzas del día (Excluye cancelados)
        hoy = timezone.now().date()
        from datetime import datetime, time
        inicio_dia = timezone.make_aware(datetime.combine(hoy, time.min))
        fin_dia = timezone.make_aware(datetime.combine(hoy, time.max))
        
        pedidos_hoy = Pedido.objects.filter(fecha__range=(inicio_dia, fin_dia))
        if request.user.is_authenticated and request.user.rol in ['cajero', 'encargado_stock'] and request.user.sucursal:
            pedidos_hoy = pedidos_hoy.filter(sucursal=request.user.sucursal)
            
        ganancias_hoy = sum(p.total for p in pedidos_hoy if p.estado == 'entregado')
        total_pedidos_hoy = pedidos_hoy.exclude(estado='cancelado').count()
        pedidos_entregados_count = pedidos_hoy.filter(estado='entregado').count()
        ticket_promedio = ganancias_hoy / pedidos_entregados_count if pedidos_entregados_count > 0 else 0

        productos_sin_stock = inventarios.filter(stock=0).count()

        return Response({
            "total_productos": Producto.objects.count(),
            "total_categorias": Categoria.objects.count(),
            "total_usuarios": Usuario.objects.count(),
            "sucursales_activas": Sucursal.objects.filter(estado=True).count(),
            "alertas_no_leidas": len(productos_bajo_stock),
            "productos_sin_stock": productos_sin_stock,
            "cajas_activas": list(Caja.objects.filter(estado='abierta').values('id', 'sucursal__nombre', 'usuario__email', 'fecha_apertura', 'monto_inicial')) if request.user.rol == 'admin' else [],
            "productos_por_categoria": list(
                Categoria.objects.annotate(total=Count('productos'))
                .values('nombre', 'total')
            ),
            "productos_bajo_stock": productos_bajo_stock,
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
                    "nombre": p.nombre,
                    "precio": float(p.precio),
                    "stock_total": sum(inv.stock for inv in p.inventarios.all())
                }
                for p in Producto.objects.prefetch_related('inventarios').all()
            ]

        elif tipo == 'categorias':
            datos['items'] = list(
                Categoria.objects.annotate(total=Count('productos'))
                .values('nombre', 'total')
            )

        elif tipo in ['stock', 'inventario']:
            inventarios = Inventario.objects.select_related('producto', 'sucursal')
            if request.user.is_authenticated and request.user.rol in ['cajero', 'encargado_stock'] and request.user.sucursal:
                inventarios = inventarios.filter(sucursal=request.user.sucursal)
                
            datos['items'] = [
                {
                    "producto": inv.producto.nombre,
                    "sucursal": inv.sucursal.nombre,
                    "stock": inv.stock,
                    "stock_minimo": inv.stock_minimo
                }
                for inv in inventarios
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