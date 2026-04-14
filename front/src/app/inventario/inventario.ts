import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { ApiService, Producto, AlertaStock } from '../core/services/api.service';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';

@Component({
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule],
  selector: 'app-admin-inventario',
  templateUrl: './inventario.html',
  styleUrls: ['./inventario.css']
})
export class AdminInventario implements OnInit {

  productos: Producto[] = [];
  alertas: AlertaStock[] = [];

  // cantidad a ajustar por producto
  ajustes: { [id: number]: number } = {};

  constructor(
    private api: ApiService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.cargar();
  }

  // 🔥 CARGA PRODUCTOS Y ALERTAS
  cargar(): void {
    this.api.getProductos().subscribe((d: Producto[]) => {
      this.productos = d;

      // inicializar ajustes en 0
      d.forEach((p: Producto) => {
        this.ajustes[p.id] = 0;
      });

      this.cdr.detectChanges();
    });

    this.api.getAlertasStock().subscribe((d: AlertaStock[]) => {
      this.alertas = d;
      this.cdr.detectChanges();
    });
  }

  // 🔥 contador de alertas
  get alertasNoLeidas(): number {
    return this.alertas.filter(a => !a.leida).length;
  }

  // 🔥 AJUSTAR STOCK (SUMA Y RESTA FUNCIONA)
  ajustarStock(p: Producto): void {
    const cantidad = Number(this.ajustes[p.id]);

    if (isNaN(cantidad) || cantidad === 0) return;

    this.api.actualizarStock(p.id, cantidad).subscribe({
      next: () => {
        this.ajustes[p.id] = 0;
        this.cargar();
      },
      error: (err) => {
        console.error('Error actualizando stock:', err);
      }
    });
  }

  // 🔥 ALERTAS
  marcarLeida(a: AlertaStock): void {
    this.api.marcarAlertaLeida(a.id).subscribe(() => this.cargar());
  }

  marcarTodasLeidas(): void {
    this.api.marcarTodasLeidas().subscribe(() => this.cargar());
  }
}