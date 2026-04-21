"""
tienda/serializers.py — Ama Dablam Coffee
"""
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Usuario, Categoria, Producto, Inventario, Reporte, AlertaStock, Pedido, DetallePedido


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
        return data


class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=4)

    class Meta:
        model = Usuario
        fields = ['id', 'email', 'password', 'rol', 'estado', 'fecha_creacion']
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


# ─────────────────────────────────────────────────────────
# INVENTARIO
# ─────────────────────────────────────────────────────────
class InventarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventario
        fields = ['id', 'stock_minimo', 'producto']


# ─────────────────────────────────────────────────────────
# PRODUCTO
# ─────────────────────────────────────────────────────────
class ProductoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    stock_minimo = serializers.SerializerMethodField()
    alerta_stock = serializers.SerializerMethodField()
    imagen_url = serializers.SerializerMethodField()

    class Meta:
        model = Producto
        fields = [
            'id', 'nombre', 'precio', 'stock', 'estado', 'destacado',
            'descripcion', 'imagen', 'imagen_url',
            'categoria', 'categoria_nombre',
            'stock_minimo', 'alerta_stock'
        ]

    def get_stock_minimo(self, obj):
        try:
            return obj.inventario.stock_minimo
        except Inventario.DoesNotExist:
            return None

    def get_alerta_stock(self, obj):
        try:
            inv = obj.inventario
            return obj.stock <= inv.stock_minimo
        except Inventario.DoesNotExist:
            return False

    def get_imagen_url(self, obj):
        request = self.context.get('request')
        if obj.imagen and request:
            return request.build_absolute_uri(obj.imagen.url)
        return None


class ProductoCreateSerializer(serializers.ModelSerializer):
    stock_minimo = serializers.IntegerField(write_only=True, required=False, default=10)
    imagen = serializers.ImageField(required=False, allow_null=True)
    class Meta:
        model = Producto
        fields = [
            'id', 'nombre', 'precio', 'stock', 'estado', 'destacado',
            'descripcion', 'imagen', 'categoria', 'stock_minimo'
        ]

    def create(self, validated_data):
        stock_minimo = validated_data.pop('stock_minimo', 10)
        producto = Producto.objects.create(**validated_data)
        Inventario.objects.create(producto=producto, stock_minimo=stock_minimo)
        producto.verificar_stock_minimo()
        return producto

    def update(self, instance, validated_data):
        stock_minimo = validated_data.pop('stock_minimo', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if stock_minimo is not None:
            inv, _ = Inventario.objects.get_or_create(producto=instance, defaults={'stock_minimo': stock_minimo})
            if inv.stock_minimo != stock_minimo:
                inv.stock_minimo = stock_minimo
                inv.save()
        instance.verificar_stock_minimo()
        return instance


# ─────────────────────────────────────────────────────────
# ALERTA STOCK
# ─────────────────────────────────────────────────────────
class AlertaStockSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)

    class Meta:
        model = AlertaStock
        fields = ['id', 'mensaje', 'fecha', 'leida', 'producto', 'producto_nombre']


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
            'id', 'usuario', 'fecha', 'estado', 'metodo_pago', 'sucursal',
            'nombre_cliente', 'telefono_cliente', 'correo_cliente',
            'total', 'detalles', 'items'
        ]
        read_only_fields = ['usuario', 'fecha', 'total', 'detalles']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        
        request = self.context.get('request')
        usuario = request.user if request and request.user.is_authenticated else None
        
        pedido = Pedido.objects.create(usuario=usuario, total=0, **validated_data)
        
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
            
            # Descontar stock
            producto.stock -= cantidad
            if producto.stock < 0:
                producto.stock = 0
            producto.save() # Esto también dispara la alerta de stock si corresponde
            
        pedido.total = total_pedido
        pedido.save()
        
        return pedido