"""
tienda/serializers.py — Ama Dablam Coffee
"""
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Usuario, Categoria, Producto, Inventario, Reporte, AlertaStock, Pedido, DetallePedido, Sucursal, Caja, MovimientoStock


# ─────────────────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────────────────
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['rol'] = user.rol
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['email'] = self.user.email
        data['rol'] = self.user.rol
        data['id'] = self.user.id
        data['sucursal'] = self.user.sucursal_id
        data['sucursal_nombre'] = self.user.sucursal.nombre if self.user.sucursal else 'Sede Principal'
        return data


class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=4)

    class Meta:
        model = Usuario
        fields = ['id', 'email', 'password', 'rol', 'estado', 'sucursal', 'fecha_creacion']
        read_only_fields = ['id', 'fecha_creacion']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = Usuario(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


# ─────────────────────────────────────────────────────────
# CATEGORÍA
# ─────────────────────────────────────────────────────────
class CategoriaSerializer(serializers.ModelSerializer):
    total_productos = serializers.SerializerMethodField()

    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'estado', 'total_productos']

    def get_total_productos(self, obj):
        return obj.productos.filter(estado=True).count()


class SucursalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sucursal
        fields = '__all__'


class CajaSerializer(serializers.ModelSerializer):
    sucursal_nombre = serializers.CharField(source='sucursal.nombre', read_only=True)
    usuario_email = serializers.CharField(source='usuario.email', read_only=True)

    class Meta:
        model = Caja
        fields = '__all__'


# ─────────────────────────────────────────────────────────
# INVENTARIO
# ─────────────────────────────────────────────────────────
class InventarioSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    sucursal_nombre = serializers.CharField(source='sucursal.nombre', read_only=True)

    class Meta:
        model = Inventario
        fields = ['id', 'producto', 'producto_nombre', 'sucursal', 'sucursal_nombre', 'stock', 'stock_minimo']


# ─────────────────────────────────────────────────────────
# PRODUCTO
# ─────────────────────────────────────────────────────────
class ProductoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    stock = serializers.SerializerMethodField()
    stock_minimo = serializers.SerializerMethodField()
    alerta_stock = serializers.SerializerMethodField()
    imagen_url = serializers.SerializerMethodField()

    class Meta:
        model = Producto
        fields = [
            'id', 'nombre', 'precio', 'estado', 'destacado',
            'descripcion', 'imagen', 'imagen_url',
            'categoria', 'categoria_nombre',
            'stock', 'stock_minimo', 'alerta_stock'
        ]

    def _get_inventario(self, obj):
        request = self.context.get('request')
        sucursal_id = request.query_params.get('sucursal') if request else None
        if not sucursal_id and request and request.user.is_authenticated and request.user.sucursal_id:
            sucursal_id = request.user.sucursal_id

        if sucursal_id:
            return Inventario.objects.filter(producto=obj, sucursal_id=sucursal_id).first()
        return None

    def get_stock(self, obj):
        inv = self._get_inventario(obj)
        return inv.stock if inv else 0

    def get_stock_minimo(self, obj):
        inv = self._get_inventario(obj)
        return inv.stock_minimo if inv else 0

    def get_alerta_stock(self, obj):
        inv = self._get_inventario(obj)
        if inv:
            return inv.stock <= inv.stock_minimo
        return False

    def get_imagen_url(self, obj):
        request = self.context.get('request')
        if obj.imagen and request:
            return request.build_absolute_uri(obj.imagen.url)
        return None


class ProductoCreateSerializer(serializers.ModelSerializer):
    imagen = serializers.ImageField(required=False, allow_null=True)
    class Meta:
        model = Producto
        fields = [
            'id', 'nombre', 'precio', 'estado', 'destacado',
            'descripcion', 'imagen', 'categoria'
        ]

    def create(self, validated_data):
        producto = Producto.objects.create(**validated_data)
        # Create default empty inventory for all branches
        for sucursal in Sucursal.objects.all():
            Inventario.objects.get_or_create(producto=producto, sucursal=sucursal, defaults={'stock': 0, 'stock_minimo': 10})
        return producto

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        # Ensure inventory exists for all branches
        for sucursal in Sucursal.objects.all():
            Inventario.objects.get_or_create(producto=instance, sucursal=sucursal, defaults={'stock': 0, 'stock_minimo': 10})
        return instance


# ─────────────────────────────────────────────────────────
# ALERTA STOCK
# ─────────────────────────────────────────────────────────
class AlertaStockSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)

    class Meta:
        model = AlertaStock
        fields = ['id', 'mensaje', 'fecha', 'leida', 'producto', 'producto_nombre', 'sucursal']

class MovimientoStockSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    sucursal_nombre = serializers.CharField(source='sucursal.nombre', read_only=True)
    usuario_email = serializers.CharField(source='usuario.email', read_only=True)

    class Meta:
        model = MovimientoStock
        fields = '__all__'


# ─────────────────────────────────────────────────────────
# REPORTE
# ─────────────────────────────────────────────────────────
class ReporteSerializer(serializers.ModelSerializer):
    generado_por_email = serializers.CharField(source='generado_por.email', read_only=True)

    class Meta:
        model = Reporte
        fields = ['id', 'tipo', 'fecha', 'generado_por_email', 'datos']


# ─────────────────────────────────────────────────────────
# PEDIDOS (CARRITO)
# ─────────────────────────────────────────────────────────
class DetallePedidoSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)

    class Meta:
        model = DetallePedido
        fields = ['id', 'producto', 'producto_nombre', 'cantidad', 'precio_unitario']


class PedidoSerializer(serializers.ModelSerializer):
    detalles = DetallePedidoSerializer(many=True, read_only=True)
    
    # Lista de items que enviará el frontend [{producto_id: 1, cantidad: 2}, ...]
    items = serializers.ListField(child=serializers.DictField(), write_only=True, required=False)

    class Meta:
        model = Pedido
        fields = [
            'id', 'usuario', 'fecha', 'estado', 'metodo_pago', 'sucursal', 'caja',
            'nombre_cliente', 'telefono_cliente', 'correo_cliente',
            'total', 'detalles', 'items'
        ]
        read_only_fields = ['usuario', 'fecha', 'total', 'detalles', 'caja']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        
        request = self.context.get('request')
        usuario = request.user if request and request.user.is_authenticated else None
        
        # Asignar caja abierta si es cajero
        caja_abierta = None
        if usuario and usuario.rol == 'cajero' and usuario.sucursal:
            caja_abierta = Caja.objects.filter(usuario=usuario, sucursal=usuario.sucursal, estado='abierta').first()

        pedido = Pedido.objects.create(usuario=usuario, total=0, caja=caja_abierta, **validated_data)
        
        total_pedido = 0
        for item in items_data:
            producto = Producto.objects.get(id=item['producto_id'])
            cantidad = item['cantidad']
            precio = producto.precio
            
            DetallePedido.objects.create(
                pedido=pedido,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=precio
            )
            
            total_pedido += (precio * cantidad)
            
            # Descontar stock por sucursal
            if pedido.sucursal:
                inv, _ = Inventario.objects.get_or_create(producto=producto, sucursal=pedido.sucursal)
                inv.actualizar_stock(-cantidad)
            
        pedido.total = total_pedido
        pedido.save()
        
        return pedido