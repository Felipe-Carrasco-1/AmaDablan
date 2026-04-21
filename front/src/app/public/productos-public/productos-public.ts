import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { ActivatedRoute, RouterModule } from '@angular/router'; // 👈 Necesario para leer la URL
import { CartService } from '../../core/services/cart.service';

import { FormsModule } from '@angular/forms'; // 👈 Importante para el buscador

@Component({
  standalone: true,
  selector: 'app-productos-public',
  imports: [CommonModule, RouterModule, FormsModule],
  templateUrl: './productos-public.html',
  styleUrls: ['./productos-public.css']
})
export class ProductosPublic implements OnInit {

  productos: any[] = [];
  loading = true;
  error = '';
  categoriaId: string | null = null;
  searchTerm = ''; // 🔍 Para el buscador

  constructor(
    private http: HttpClient,
    private route: ActivatedRoute, // 👈 Inyectamos la ruta activa
    private cdr: ChangeDetectorRef,
    public cartService: CartService
  ) { }

  ngOnInit() {
    // Escuchamos los cambios en la URL (por si el usuario pincha filtros sin recargar la página)
    this.route.queryParams.subscribe(params => {
      this.categoriaId = params['categoria'] || null;
      this.cargarProductos();
    });
  }

  cargarProductos() {
    this.loading = true;

    // Construimos la URL con los filtros de Django
    // Filtramos por activos=true y opcionalmente por categoría
    let url = 'http://localhost:8000/api/productos/?estado=true';

    if (this.categoriaId) {
      url += `&categoria=${this.categoriaId}`;
    }

    this.http.get<any[]>(url).subscribe({
      next: (res) => {
        this.productos = res;
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.loading = false;
        this.error = 'No se pudieron cargar los productos.';
        console.error(err);
        this.cdr.detectChanges();
      }
    });
  }

  get filteredProductos() {
    if (!this.searchTerm) return this.productos;
    const term = this.searchTerm.toLowerCase();
    return this.productos.filter(p => 
      p.nombre.toLowerCase().includes(term) || 
      (p.descripcion && p.descripcion.toLowerCase().includes(term))
    );
  }

  addToCart(producto: any) {
    this.cartService.addToCart(producto, 1);
    // Opcional: mostrar una notificación o abrir el carrito
    if (!this.cartService.isCartOpen()) {
      this.cartService.toggleCart();
    }
  }

  getIcon(nombre: string): string {
    const key = nombre.toLowerCase();
    if (key.includes('café')) return '☕';
    if (key.includes('congel')) return '🍦';
    if (key.includes('sandwich') || key.includes('sándwich')) return '🥪';
    if (key.includes('snack') || key.includes('picoteo')) return '🥐';
    if (key.includes('bebida') || key.includes('jugo')) return '🥤';
    if (key.includes('pasteler') || key.includes('torta') || key.includes('dulce')) return '🍰';
    return '📦';
  }

  getProductoIcon(nombre: string): string {
    const key = nombre.toLowerCase();
    if (key.includes('sandwich') || key.includes('sándwich')) return '🥪';
    if (key.includes('snack') || key.includes('picoteo') || key.includes('papa')) return '🥐';
    if (key.includes('bebida') || key.includes('jugo')) return '🥤';
    if (key.includes('pasteler') || key.includes('torta') || key.includes('dulce') || key.includes('muffin') || key.includes('snack')) return '🍰';
    return '☕';
  }
}