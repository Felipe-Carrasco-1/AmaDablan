import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { ApiService, Reporte } from '../core/services/api.service';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-admin-reportes',
  templateUrl: './reportes.html',
  styleUrls: ['./reportes.css'],
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule]
})
export class AdminReportes implements OnInit {

  reportes:            any[]    = [];
  reporteSeleccionado: any      = null;
  loading                       = false;
  successMsg                    = '';

  tipos = [
    { value: 'stock',      icon: '📦', label: 'Reporte Stock' },
    { value: 'productos',  icon: '☕', label: 'Reporte Productos' },
    { value: 'categorias', icon: '🗂️', label: 'Reporte Categorías' },
    { value: 'inventario', icon: '📋', label: 'Reporte Inventario' },
  ];
  reporteService: any;

  constructor(private api: ApiService, private cdr: ChangeDetectorRef) {}

  ngOnInit() {
    this.api.getReportes().subscribe((d: any) => {
      this.reportes = d;
      this.cdr.detectChanges(); // ✅
    });
  }

  generar(tipo: string) {
  this.loading = true;
  this.cdr.detectChanges(); // ✅ muestra el loading inmediatamente
  
  this.api.generarReporte(tipo).subscribe({
    next: (r: any) => {
      this.loading    = false;
      this.successMsg = 'Reporte generado exitosamente.';
      this.reportes.unshift(r);
      this.cdr.detectChanges(); // ✅
      setTimeout(() => {
        this.successMsg = '';
        this.cdr.detectChanges(); // ✅
      }, 2500);
    },
    error: (err) => {
      this.loading = false;
      console.error(err);
      this.cdr.detectChanges(); // ✅
    }
  });
}

DeleteReporte(id: number) {
  const ok = confirm('¿Seguro que quieres eliminar este reporte?');
  if (!ok) return;

  this.api.DeleteReporte(id).subscribe({
    next: () => {
      this.reportes = this.reportes.filter(r => r.id !== id);
      this.cdr.detectChanges(); // ✅ FALTABA ESTO
    },
    error: (err) => {
      console.error(err);
      this.cdr.detectChanges(); // ✅
    }
  });
}

  verDetalle(r: Reporte) {
    this.reporteSeleccionado = r;
    this.cdr.detectChanges(); // ✅
  }

  getColumns(row: any): string[] {
    return Object.keys(row);
  }
}