import { Routes } from '@angular/router';

import { LoginComponent } from './login/login';
import { AdminLayout } from './admin-layout/admin-layout';

import { AdminDashboard } from './dashboard/dashboard';
import { AdminProductos } from './productos/productos';
import { AdminCategorias } from './categorias/categorias';
import { AdminInventario } from './inventario/inventario';
import { AdminReportes } from './reportes/reportes';
import { Contacto } from './contacto/contacto';

import { Home } from './public/home/home';
import { ProductosPublic } from './public/productos-public/productos-public';

import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [

  // 🌐 PÚBLICO
  { path: '', component: Home },
  { path: 'productos', component: ProductosPublic },
  { path: 'contacto', component: Contacto }, // ✅ movido aquí

  // 🔐 LOGIN
  { path: 'login', component: LoginComponent },

  // 🔐 ADMIN
  {
    path: 'admin',
    component: AdminLayout,
    canActivate: [authGuard],
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      { path: 'dashboard',  component: AdminDashboard },
      { path: 'productos',  component: AdminProductos },
      { path: 'categorias', component: AdminCategorias },
      { path: 'inventario', component: AdminInventario },
      { path: 'reportes',   component: AdminReportes },
    ]
  },

  // 🚫 fallback
  { path: '**', redirectTo: '' }
];