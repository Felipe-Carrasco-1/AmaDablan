import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { CartService } from '../../core/services/cart.service';

@Component({
  selector: 'app-carrito',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule],
  templateUrl: './carrito.html',
  styleUrls: ['./carrito.css']
})
export class CarritoComponent {
  cartService = inject(CartService);
  router = inject(Router);
  procesando = false;
  mensaje = '';
  mensajeTipo = 'success';
  metodoPago = 'transferencia';

  increaseQty(item: any) {
    this.cartService.updateQuantity(item.producto_id, item.cantidad + 1);
  }

  decreaseQty(item: any) {
    this.cartService.updateQuantity(item.producto_id, item.cantidad - 1);
  }

  removeItem(item: any) {
    this.cartService.removeFromCart(item.producto_id);
  }

  irACheckout() {
    if (this.cartService.items().length === 0) return;
    this.cartService.toggleCart();
    this.router.navigate(['/checkout'], { queryParams: { pago: this.metodoPago } });
  }
}
