from django.db.models import Count
from django.core.mail import send_mail

from rest_framework import viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import (
    Usuario, Categoria, Producto,
    Inventario, Reporte, AlertaStock
)

from .serializers import (
    CustomTokenObtainPairSerializer,
    UsuarioSerializer,
    CategoriaSerializer,
    ProductoSerializer,
    ProductoCreateSerializer,
    InventarioSerializer,
    AlertaStockSerializer,
    ReporteSerializer
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

            # 🔥 FIX REAL AQUÍ
            "productos_bajo_stock": productos_bajo_stock
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