from django.db.models import Count
from django.core.mail import send_mail

from rest_framework import viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
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
# PRODUCTOS (🔥 FIX FILTROS)
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

    # 🔥 STOCK (SUMA Y RESTA)
    @action(detail=True, methods=['patch'])
    def actualizar_stock(self, request, pk=None):
        producto = self.get_object()
        cantidad = int(request.data.get('cantidad', 0))

        producto.stock = producto.stock + cantidad

        if producto.stock < 0:
            producto.stock = 0

        producto.save()

        return Response({
            "mensaje": "Stock actualizado",
            "stock": producto.stock
        })


# =========================
# INVENTARIO
# =========================
class InventarioViewSet(viewsets.ModelViewSet):
    queryset = Inventario.objects.select_related('producto')
    serializer_class = InventarioSerializer
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=['get'])
    def alertas_activas(self, request):
        data = []

        for inv in self.get_queryset():
            if inv.producto.stock <= inv.stock_minimo:
                data.append({
                    "id": inv.id,
                    "producto": inv.producto.nombre,
                    "stock": inv.producto.stock,
                    "stock_minimo": inv.stock_minimo,
                    "leida": False
                })

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


# =========================
# REPORTES + DASHBOARD
# =========================
class ReporteViewSet(viewsets.ModelViewSet):
    queryset = Reporte.objects.all().order_by('-id')
    serializer_class = ReporteSerializer
    permission_classes = [IsAdminUser]

    # 🔥 DASHBOARD
    @action(detail=False, methods=['get'])
    def dashboard(self, request):

        alertas = 0

        for inv in Inventario.objects.select_related('producto'):
            if inv.producto.stock <= inv.stock_minimo:
                alertas += 1

        return Response({
            "total_productos": Producto.objects.count(),
            "total_categorias": Categoria.objects.count(),
            "total_usuarios": Usuario.objects.count(),

            "alertas_no_leidas": alertas,

            "productos_sin_stock": Producto.objects.filter(stock=0).count(),

            "productos_por_categoria": list(
                Categoria.objects.annotate(total=Count('productos'))
                .values('nombre', 'total')
            ),

            "productos_bajo_stock": list(
                Producto.objects.filter(stock__lte=5)
                .values('nombre', 'stock')
            )
        })

    # 🔥 REPORTES (FIX STOCK + DECIMAL)
    @action(detail=False, methods=['post'])
    def generar(self, request):

        tipo = request.data.get('tipo')

        if not tipo:
            return Response({'error': 'Debe enviar tipo de reporte'}, status=400)

        datos = {}

        # PRODUCTOS
        if tipo == 'productos':
            datos['items'] = [
                {
                    "nombre": p["nombre"],
                    "precio": float(p["precio"]),
                    "stock": p["stock"]
                }
                for p in Producto.objects.values('nombre', 'precio', 'stock')
            ]

        # CATEGORIAS
        elif tipo == 'categorias':
            datos['items'] = list(
                Categoria.objects.annotate(total=Count('productos'))
                .values('nombre', 'total')
            )

        # STOCK / INVENTARIO
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