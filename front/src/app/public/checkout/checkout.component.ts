import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router, ActivatedRoute } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { CartService } from '../../core/services/cart.service';

@Component({
  selector: 'app-checkout',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule],
  templateUrl: './checkout.html',
  styleUrls: ['./checkout.css']
})
export class CheckoutComponent implements OnInit {
  cartService = inject(CartService);
  router = inject(Router);
  route = inject(ActivatedRoute);

  metodoPago = 'transferencia';
  sucursal = 'linares_catedral';
  nombre = '';
  telefono = '';
  correo = '';

  procesando = false;
  mensaje = '';
  mensajeTipo = 'success';

  ngOnInit() {
    this.route.queryParams.subscribe(params => {
      if (params['pago']) {
        this.metodoPago = params['pago'];
      }
    });

    if (this.cartService.items().length === 0) {
      this.router.navigate(['/productos']);
    }
  }

  confirmarPedido() {
    if (!this.nombre || !this.telefono || !this.correo) {
      this.mensajeTipo = 'error';
      this.mensaje = 'Por favor, completa todos tus datos de contacto.';
      return;
    }

    this.procesando = true;
    this.cartService.checkout({
      metodo_pago: this.metodoPago,
      sucursal: this.sucursal,
      nombre_cliente: this.nombre,
      telefono_cliente: this.telefono,
      correo_cliente: this.correo
    }).subscribe({
      next: (res) => {
        this.procesando = false;

        if (this.metodoPago === 'transferencia') {
          this.mensajeTipo = 'success';
          this.mensaje = '¡Pedido agendado con éxito! Recibimos tus datos. Ya puedes realizar la transferencia para confirmar.';
        } else {
          this.mensajeTipo = 'info';
          this.mensaje = '¡Pedido agendado con éxito! Te esperamos en el local para el retiro y pago.';
        }

        this.cartService.clearCart();
        setTimeout(() => {
          this.router.navigate(['/']);
        }, 8000);
      },
      error: (err) => {
        this.procesando = false;
        this.mensajeTipo = 'error';
        this.mensaje = 'Ocurrió un error al agendar tu pedido. Intenta nuevamente.';
        console.error(err);
      }
    });
  }
}
