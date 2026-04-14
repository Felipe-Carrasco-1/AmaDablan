"""
api/models.py — Ama Dablam Coffee (CORREGIDO)
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

        # SUMAR O RESTAR
        nuevo_stock = self.producto.stock + cantidad

        # Evitar negativos
        if nuevo_stock < 0:
            nuevo_stock = 0

        self.producto.stock = nuevo_stock
        self.producto.save()

        # ALERTA
        if self.producto.stock <= self.stock_minimo:

            existe = AlertaStock.objects.filter(
                producto=self.producto,
                leida=False
            ).exists()

            if not existe:
                AlertaStock.objects.create(
                    producto=self.producto,
                    mensaje=f'Stock bajo en {self.producto.nombre}: {self.producto.stock} unidades (mínimo: {self.stock_minimo})'
                )


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