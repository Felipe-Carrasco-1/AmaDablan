import { Component, OnInit } from '@angular/core';
import { ApiService } from '../core/services/api.service';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';

interface CategoriaProducto {
  nombre: string;
  total: number;
}

interface Dashboard {
  total_productos: number;
  total_categorias: number;
  total_usuarios: number;
  alertas_no_leidas: number;
  productos_sin_stock: number;
  productos_destacados: number;
  productos_por_categoria: CategoriaProducto[];
  productos_bajo_stock: any[];
}

const DEFAULT_DASHBOARD: Dashboard = {
  total_productos: 0,
  total_categorias: 0,
  total_usuarios: 0,
  alertas_no_leidas: 0,
  productos_sin_stock: 0,
  productos_destacados: 0,
  productos_por_categoria: [],
  productos_bajo_stock: []
};

@Component({
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule],
  selector: 'app-admin-dashboard',
  templateUrl: './dashboard.html',
  styleUrls: ['./dashboard.css']
})
export class AdminDashboard implements OnInit {

  dashboard: Dashboard = DEFAULT_DASHBOARD;

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.api.getDashboard().subscribe({
      next: (data: Dashboard) => {
        this.dashboard = {
          ...DEFAULT_DASHBOARD,
          ...data
        };
      },
      error: (err) => {
        console.error('Error cargando dashboard:', err);
        this.dashboard = DEFAULT_DASHBOARD;
      }
    });
  }

  barPct(val: number): number {
    const categorias = this.dashboard.productos_por_categoria || [];

    if (categorias.length === 0) return 0;

    const max = Math.max(...categorias.map(c => c.total), 1);

    return (val / max) * 100;
  }
}