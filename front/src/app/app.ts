import { Component, inject, HostListener } from '@angular/core';
import { RouterOutlet, Router, RouterModule } from '@angular/router';
import { CommonModule } from '@angular/common';
import { CarritoComponent } from './public/carrito/carrito.component';
import { CartService } from './core/services/cart.service';
import { AuthService } from './core/services/auth.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, CommonModule, CarritoComponent, RouterModule],
  templateUrl: './app.html',
  styleUrls: ['./app.css']
})
export class App {
  cartService = inject(CartService);
  auth = inject(AuthService);
  router = inject(Router);

  isScrolled = false;
  menuAbierto = false;

  @HostListener('window:scroll', [])
  onWindowScroll() {
    this.isScrolled = window.scrollY > 50;
  }

  toggleMenu() {
    this.menuAbierto = !this.menuAbierto;
  }

  mostrarCarrito(): boolean {
    const url = this.router.url;
    // Ocultar carrito en admin, login y checkout para evitar distracciones
    return !url.includes('/admin') && !url.includes('/login') && !url.includes('/checkout') && !url.includes('/pos');
  }

  esPublico(): boolean {
    const url = this.router.url;
    // El Navbar y Footer solo se ven en la parte pública (no en admin, ni login, ni pos)
    return !url.includes('/admin') && !url.includes('/login') && !url.includes('/pos');
  }
}