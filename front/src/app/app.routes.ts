import { Routes } from '@angular/router';

import { LoginComponent } from './login/login';
import { ForgotPasswordComponent } from './login/forgot-password';
import { ResetPasswordComponent } from './login/reset-password';
import { PosComponent } from './cajero/pos/pos';
import { AdminLayout } from './admin-layout/admin-layout';

import { AdminDashboard } from './dashboard/dashboard';
import { AdminProductos } from './productos/productos';
import { AdminCategorias } from './categorias/categorias';
import { AdminInventario } from './inventario/inventario';
import { AdminReportes } from './reportes/reportes';
import { Contacto } from './contacto/contacto';
import { NuestroGranoComponent } from './public/nuestro-grano/nuestro-grano';

import { Home } from './public/home/home';
import { ProductosPublic } from './public/productos-public/productos-public';
import { CarritoComponent } from './public/carrito/carrito.component';
import { CheckoutComponent } from './public/checkout/checkout.component';

import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [

  // 🌐 PÚBLICO
  { path: '', component: Home },
  { path: 'productos', component: ProductosPublic },
  { path: 'carrito', component: CarritoComponent },
  { path: 'checkout', component: CheckoutComponent },
  { path: 'contacto', component: Contacto },
  { path: 'nuestro-grano', component: NuestroGranoComponent },

  // 🔐 LOGIN
  { path: 'login', component: LoginComponent },
  { path: 'forgot-password', component: ForgotPasswordComponent },
  { path: 'reset-password', component: ResetPasswordComponent },
  { path: 'pos', component: PosComponent, canActivate: [authGuard] },

  // 🔐 ADMIN
  {
    path: 'admin',
    component: AdminLayout,
    canActivate: [authGuard],
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      { path: 'dashboard', component: AdminDashboard },
      { path: 'productos', component: AdminProductos },
      { path: 'categorias', component: AdminCategorias },
      { path: 'inventario', component: AdminInventario },
      { path: 'reportes', component: AdminReportes },
    ]
  },

  // 🚫 fallback
  { path: '**', redirectTo: '' }
];