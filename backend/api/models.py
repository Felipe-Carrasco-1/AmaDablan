"""
api/models.py — Ama Dablam Coffee (FINAL PRO)
"""

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


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
        ('cliente', 'Cliente')
    ]

    email = models.EmailField(unique=True)
    rol = models.CharField(max_length=10, choices=ROL_CHOICES, default='cliente')
    estado = models.BooleanField(default=True)

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
    stock = models.IntegerField(default=0)
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

    # 🔥 MÉTODO CENTRALIZADO
    def verificar_stock_minimo(self):
        try:
            inventario = self.inventario

            if self.stock <= inventario.stock_minimo:

                existe = AlertaStock.objects.filter(
                    producto=self,
                    leida=False
                ).exists()

                if not existe:
                    AlertaStock.objects.create(
                        producto=self,
                        mensaje=f'Stock bajo en {self.nombre}: {self.stock} unidades (mínimo: {inventario.stock_minimo})'
                    )
                return True

        except Inventario.DoesNotExist:
            pass

        return False

    # 🔥 OPCIONAL PRO (AUTO)
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.verificar_stock_minimo()


# ─────────────────────────────────────────────
# INVENTARIO
# ─────────────────────────────────────────────
class Inventario(models.Model):
    stock_minimo = models.IntegerField()

    producto = models.OneToOneField(
        Producto,
        on_delete=models.CASCADE,
        related_name='inventario'
    )

    def __str__(self):
        return f'Inventario - {self.producto.nombre}'

    def actualizar_stock(self, cantidad):
        if cantidad == 0:
            return

        nuevo_stock = self.producto.stock + cantidad

        if nuevo_stock < 0:
            nuevo_stock = 0

        self.producto.stock = nuevo_stock
        self.producto.save()

        # 🔥 SOLO LLAMA AL MÉTODO CENTRAL
        self.producto.verificar_stock_minimo()


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
    sucursal = models.CharField(
        max_length=50,
        choices=[
            ('linares_catedral', 'Linares Catedral'),
            ('linares_hospital', 'Linares Hospital'),
            ('talca', 'Sucursal Talca')
        ],
        default='linares_catedral'
    )
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
