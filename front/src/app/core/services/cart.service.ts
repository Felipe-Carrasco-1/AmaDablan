import { Injectable, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface CartItem {
  producto_id: number;
  nombre: string;
  precio: number;
  cantidad: number;
  imagen?: string;
}

@Injectable({
  providedIn: 'root'
})
export class CartService {
  private apiUrl = 'http://localhost:8000/api/pedidos/';
  
  // Usamos signals de Angular para que la UI se actualice automáticamente en tiempo real
  private cartItemsSignal = signal<CartItem[]>(this.loadCartFromStorage());
  
  // Variables derivadas que se recalculan solas
  public items = this.cartItemsSignal.asReadonly();
  public total = computed(() => this.items().reduce((acc, item) => acc + (item.precio * item.cantidad), 0));
  public totalItems = computed(() => this.items().reduce((acc, item) => acc + item.cantidad, 0));

  public isCartOpen = signal(false);

  toggleCart() {
    this.isCartOpen.update(v => !v);
  }

  constructor(private http: HttpClient) {}

  private loadCartFromStorage(): CartItem[] {
    // Verificación para evitar errores en Angular SSR (Server-Side Rendering)
    if (typeof window !== 'undefined' && window.localStorage) {
      const saved = localStorage.getItem('cart');
      return saved ? JSON.parse(saved) : [];
    }
    return [];
  }

  private saveCartToStorage(items: CartItem[]) {
    if (typeof window !== 'undefined' && window.localStorage) {
      localStorage.setItem('cart', JSON.stringify(items));
    }
  }

  addToCart(producto: any, cantidad: number = 1) {
    this.cartItemsSignal.update(items => {
      const existing = items.find(i => i.producto_id === producto.id);
      let newItems;
      if (existing) {
        newItems = items.map(i => i.producto_id === producto.id ? { ...i, cantidad: i.cantidad + cantidad } : i);
      } else {
        newItems = [...items, {
          producto_id: producto.id,
          nombre: producto.nombre,
          precio: producto.precio,
          cantidad: cantidad,
          imagen: producto.imagen_url || producto.imagen
        }];
      }
      this.saveCartToStorage(newItems);
      return newItems;
    });
  }

  removeFromCart(producto_id: number) {
    this.cartItemsSignal.update(items => {
      const newItems = items.filter(i => i.producto_id !== producto_id);
      this.saveCartToStorage(newItems);
      return newItems;
    });
  }

  updateQuantity(producto_id: number, cantidad: number) {
    if (cantidad <= 0) {
      this.removeFromCart(producto_id);
      return;
    }
    this.cartItemsSignal.update(items => {
      const newItems = items.map(i => i.producto_id === producto_id ? { ...i, cantidad } : i);
      this.saveCartToStorage(newItems);
      return newItems;
    });
  }

  clearCart() {
    this.cartItemsSignal.set([]);
    this.saveCartToStorage([]);
  }

  checkout(data: { metodo_pago: string, sucursal: string, nombre_cliente: string, telefono_cliente: string, correo_cliente: string }): Observable<any> {
    const payload = {
      ...data,
      items: this.items().map(i => ({
        producto_id: i.producto_id,
        cantidad: i.cantidad
      }))
    };
    return this.http.post(this.apiUrl, payload);
  }
}
