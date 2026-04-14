# tienda/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Categoria, Producto, Inventario, Reporte, AlertaStock


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    model = Usuario
    list_display = ['email', 'rol', 'estado', 'fecha_creacion']
    list_filter = ['rol', 'estado']
    ordering = ['email']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Info', {'fields': ('rol', 'estado')}),
        ('Permisos', {'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'rol', 'estado'),
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
    list_display = ['nombre', 'precio', 'stock', 'categoria', 'destacado', 'estado']
    list_filter = ['estado', 'destacado', 'categoria']
    search_fields = ['nombre']
    inlines = [InventarioInline]


@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = ['producto', 'stock_minimo']


@admin.register(AlertaStock)
class AlertaStockAdmin(admin.ModelAdmin):
    list_display = ['producto', 'mensaje', 'fecha', 'leida']
    list_filter = ['leida']


@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):
    list_display = ['tipo', 'fecha', 'generado_por']
    list_filter = ['tipo']