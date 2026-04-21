"""
api/models.py — Ama Dablam Coffee (FINAL PRO)
"""

from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


# ─────────────────────────────────────────────
# SUCURSAL
# ─────────────────────────────────────────────
class Sucursal(models.Model):
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'Sucursal'


# ─────────────────────────────────────────────
# USUARIO CUSTOM
# ─────────────────────────────────────────────
class UsuarioManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('rol', 'admin')
        extra_fields.setdefault('is_active', True)

        return self.create_user(email, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    ROL_CHOICES = [
        ('admin', 'Administrador'),
        ('cajero', 'Cajero'),
        ('encargado_stock', 'Encargado de Stock'),
        ('cliente', 'Cliente')
    ]

    email = models.EmailField(unique=True)
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='cliente')
    estado = models.BooleanField(default=True)
    sucursal = models.ForeignKey(Sucursal, on_delete=models.SET_NULL, null=True, blank=True, related_name='usuarios')

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='api_usuarios_groups',
        blank=True
    )

    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='api_usuarios_permissions',
        blank=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UsuarioManager()

    def __str__(self):
        return self.email

    @property
    def es_admin(self):
        return self.rol == 'admin'

    class Meta:
        db_table = 'Usuario'


# ─────────────────────────────────────────────
# CAJA
# ─────────────────────────────────────────────
class Caja(models.Model):
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE, related_name='cajas')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='cajas_abiertas')
    fecha_apertura = models.DateTimeField(auto_now_add=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    monto_inicial = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    monto_final = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    estado = models.CharField(max_length=20, choices=[('abierta', 'Abierta'), ('cerrada', 'Cerrada')], default='abierta')

    def __str__(self):
        return f"Caja {self.id} - {self.sucursal.nombre} ({self.estado})"

    class Meta:
        db_table = 'Caja'
        ordering = ['-fecha_apertura']


# ─────────────────────────────────────────────
# CATEGORÍA
# ─────────────────────────────────────────────
class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'Categoria'


# ─────────────────────────────────────────────
# PRODUCTO
# ─────────────────────────────────────────────
class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.BooleanField(default=True)
    destacado = models.BooleanField(default=False)

    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    descripcion = models.TextField(blank=True, default='')

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True,
        related_name='productos'
    )

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'Producto'


# ─────────────────────────────────────────────
# INVENTARIO
# ─────────────────────────────────────────────
class Inventario(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='inventarios')
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE, related_name='inventarios', null=True, blank=True)
    stock = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=0)

    class Meta:
        db_table = 'Inventario'
        unique_together = ('producto', 'sucursal')

    def __str__(self):
        return f'Inventario - {self.producto.nombre} - {self.sucursal.nombre}'

    def verificar_stock_minimo(self):
        if self.stock <= self.stock_minimo:
            existe = AlertaStock.objects.filter(
                producto=self.producto,
                sucursal=self.sucursal,
                leida=False
            ).exists()

            if not existe:
                AlertaStock.objects.create(
                    producto=self.producto,
                    sucursal=self.sucursal,
                    mensaje=f'Stock bajo en {self.producto.nombre} ({self.sucursal.nombre}): {self.stock} unidades (mínimo: {self.stock_minimo})'
                )
            return True
        return False

    def actualizar_stock(self, cantidad, motivo="Ajuste", usuario=None):
        if cantidad == 0:
            return

        stock_antes = self.stock
        nuevo_stock = self.stock + cantidad
        if nuevo_stock < 0:
            nuevo_stock = 0

        self.stock = nuevo_stock
        self.save()
        
        # Registrar el movimiento
        tipo = 'ENTRADA' if cantidad > 0 else 'SALIDA'
        MovimientoStock.objects.create(
            producto=self.producto,
            sucursal=self.sucursal,
            tipo=tipo,
            cantidad=cantidad,
            stock_antes=stock_antes,
            stock_despues=self.stock,
            motivo=motivo,
            usuario=usuario
        )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.verificar_stock_minimo()

class MovimientoStock(models.Model):
    TIPO_CHOICES = [
        ('ENTRADA', 'Entrada'),
        ('SALIDA', 'Salida'),
    ]
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='movimientos')
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE, related_name='movimientos', null=True, blank=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    cantidad = models.IntegerField()
    stock_antes = models.IntegerField()
    stock_despues = models.IntegerField()
    motivo = models.CharField(max_length=255, default='Ajuste manual')
    usuario = models.ForeignKey('Usuario', on_delete=models.SET_NULL, null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'MovimientoStock'
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.tipo} {self.cantidad} - {self.producto.nombre}"

# ─────────────────────────────────────────────
# REPORTE
# ─────────────────────────────────────────────
class Reporte(models.Model):
    TIPO_CHOICES = [
        ('ventas', 'Ventas'),
        ('stock', 'Stock'),
        ('productos', 'Productos'),
        ('categorias', 'Categorías'),
        ('inventario', 'Inventario'),
    ]

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='ventas')
    fecha = models.DateTimeField(auto_now_add=True)

    generado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reportes'
    )

    datos = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f'Reporte {self.tipo} - {self.fecha}'

    class Meta:
        db_table = 'Reporte'
        ordering = ['-fecha']


# ─────────────────────────────────────────────
# ALERTA STOCK
# ─────────────────────────────────────────────
class AlertaStock(models.Model):
    mensaje = models.CharField(max_length=255)
    fecha = models.DateTimeField(auto_now_add=True)
    leida = models.BooleanField(default=False)

    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='alertas'
    )
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.CASCADE,
        related_name='alertas',
        null=True, blank=True
    )

    def __str__(self):
        return self.mensaje

    class Meta:
        db_table = 'AlertaStock'
        ordering = ['-fecha']


# ─────────────────────────────────────────────
# PEDIDO Y DETALLES DEL CARRITO
# ─────────────────────────────────────────────
class Pedido(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('enviado', 'Enviado'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]

    usuario = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='pedidos'
    )
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    metodo_pago = models.CharField(
        max_length=20, 
        choices=[('transferencia', 'Transferencia Bancaria'), ('efectivo', 'Efectivo/Presencial')], 
        default='transferencia'
    )
    sucursal = models.ForeignKey(Sucursal, on_delete=models.SET_NULL, null=True, related_name='pedidos')
    caja = models.ForeignKey('Caja', on_delete=models.SET_NULL, null=True, blank=True, related_name='pedidos')
    nombre_cliente = models.CharField(max_length=100, blank=True, null=True)
    telefono_cliente = models.CharField(max_length=20, blank=True, null=True)
    correo_cliente = models.EmailField(blank=True, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        db_table = 'Pedido'
        ordering = ['-fecha']

    def __str__(self):
        return f'Pedido {self.id} - {self.estado}'


class DetallePedido(models.Model):
    pedido = models.ForeignKey(
        Pedido, 
        on_delete=models.CASCADE, 
        related_name='detalles'
    )
    producto = models.ForeignKey(
        Producto, 
        on_delete=models.SET_NULL, 
        null=True
    )
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2) 

    class Meta:
        db_table = 'DetallePedido'

    def __str__(self):
        nombre_prod = self.producto.nombre if self.producto else "Producto eliminado"
        return f'{self.cantidad} x {nombre_prod}'
