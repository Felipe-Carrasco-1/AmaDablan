import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { ApiService, Producto, AlertaStock } from '../core/services/api.service';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../core/services/auth.service';

@Component({
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule],
  selector: 'app-admin-inventario',
  templateUrl: './inventario.html',
  styleUrls: ['./inventario.css']
})
export class AdminInventario implements OnInit {

  inventarios: any[] = [];
  alertas: any[] = [];
  movimientos: any[] = [];
  cargando: boolean = false;
  activeTab: string = 'inventario';

  filtroEstado: string = 'todos';
  busqueda: string = '';

  // cantidad a ajustar por inventario
  ajustes: { [id: number]: number } = {};

  constructor(
    private api: ApiService,
    public auth: AuthService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.cargarDatos();
  }

  cambiarTab(tab: string) {
    this.activeTab = tab;
    if (tab === 'alertas') {
      this.cargarAlertas();
    } else if (tab === 'movimientos') {
      this.cargarMovimientos();
    }
  }

  cargarDatos() {
    this.cargando = true;
    this.api.getInventario().subscribe({
      next: (data: any) => {
        this.inventarios = data;
        this.cargando = false;
        this.cdr.detectChanges();
        this.cargarAlertas();
      },
      error: () => this.cargando = false
    });
  }

  cargarAlertas() {
    this.api.getAlertas().subscribe(res => {
      this.alertas = res.filter(a => !a.leida);
      this.cdr.detectChanges();
    });
  }

  cargarMovimientos() {
    this.api.getMovimientos().subscribe(res => {
      this.movimientos = res;
      this.cdr.detectChanges();
    });
  }

  marcarAlertaResuelta(id: number) {
    this.api.marcarAlertaLeida(id).subscribe(() => {
      this.cargarAlertas();
    });
  }

  // 🔥 contador de alertas
  get alertasNoLeidas(): number {
    return this.alertas.filter(a => !a.leida).length;
  }

  // 🔥 AJUSTAR STOCK
  ajustarStock(inv: any, delta: number) {
    const nuevoStock = inv.stock + delta;
    if (nuevoStock < 0) return;
    
    // El motivo lo podemos manejar si actualizamos el backend para aceptarlo, por ahora pasamos lo que el servicio acepte.
    this.api.actualizarStock(inv.producto.id, delta, inv.sucursal, "Ajuste manual").subscribe({
      next: () => {
        inv.stock = nuevoStock;
        this.cargarAlertas();
        this.cargarMovimientos();
      },
      error: (err: any) => alert('Error al actualizar stock')
    });
  }

  // 🔥 ALERTAS
  marcarLeida(a: AlertaStock): void {
    this.api.marcarAlertaLeida(a.id).subscribe(() => this.cargarAlertas());
  }

  marcarTodasLeidas(): void {
    this.api.marcarTodasLeidas().subscribe(() => this.cargarAlertas());
  }

  get filteredInventarios() {
    let list = this.inventarios;
    if (this.filtroEstado !== 'todos') {
      if (this.filtroEstado === 'ok') list = list.filter(i => i.stock > i.stock_minimo);
      if (this.filtroEstado === 'bajo') list = list.filter(i => i.stock <= i.stock_minimo && i.stock > 0);
      if (this.filtroEstado === 'agotado') list = list.filter(i => i.stock === 0);
    }
    if (this.busqueda.trim()) {
      const q = this.busqueda.toLowerCase();
      list = list.filter(i => i.producto.nombre.toLowerCase().includes(q));
    }
    return list;
  }

  getTotalProductos() { return this.inventarios.length; }
  getStockOk() { return this.inventarios.filter(i => i.stock > i.stock_minimo).length; }
  getStockBajo() { return this.inventarios.filter(i => i.stock <= i.stock_minimo && i.stock > 0).length; }
  getAgotados() { return this.inventarios.filter(i => i.stock === 0).length; }

  getEstadoTexto(inv: any) {
    if (inv.stock === 0) return 'AGOTADO';
    if (inv.stock <= inv.stock_minimo) return 'BAJO';
    return 'OK';
  }
}