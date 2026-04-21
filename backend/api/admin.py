# tienda/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Categoria, Producto, Inventario, Reporte, AlertaStock, Sucursal, Caja, Pedido, DetallePedido


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    model = Usuario
    list_display = ['email', 'rol', 'sucursal', 'estado', 'fecha_creacion']
    list_filter = ['rol', 'estado', 'sucursal']
    ordering = ['email']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Info', {'fields': ('rol', 'sucursal', 'estado')}),
        ('Permisos', {'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'rol', 'sucursal', 'estado'),
        }),
    )
    search_fields = ['email']


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'estado']
    list_filter = ['estado']


class InventarioInline(admin.StackedInline):
    model = Inventario
    extra = 1


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'precio', 'categoria', 'destacado', 'estado']
    list_filter = ['estado', 'destacado', 'categoria']
    search_fields = ['nombre']
    inlines = [InventarioInline]


@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = ['producto', 'sucursal', 'stock', 'stock_minimo']
    list_filter = ['sucursal']


@admin.register(AlertaStock)
class AlertaStockAdmin(admin.ModelAdmin):
    list_display = ['producto', 'sucursal', 'mensaje', 'fecha', 'leida']
    list_filter = ['leida', 'sucursal']


@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):
    list_display = ['tipo', 'fecha', 'generado_por']
    list_filter = ['tipo']


@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'direccion', 'telefono', 'estado']
    list_filter = ['estado']


@admin.register(Caja)
class CajaAdmin(admin.ModelAdmin):
    list_display = ['sucursal', 'usuario', 'fecha_apertura', 'fecha_cierre', 'estado']
    list_filter = ['estado', 'sucursal']


class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 1

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ['id', 'sucursal', 'caja', 'estado', 'fecha', 'total']
    list_filter = ['estado', 'sucursal']
    inlines = [DetallePedidoInline]