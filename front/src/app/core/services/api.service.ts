import { HttpClient } from "@angular/common/http";
import { Injectable } from "@angular/core";
import { Observable } from "rxjs";
import { shareReplay } from "rxjs/operators";

@Injectable({ providedIn: 'root' })
export class ApiService {

  private baseUrl = 'http://localhost:8000/api';

  // 🔥 CACHE DASHBOARD
  private dashboardCache$?: Observable<Dashboard>;

  constructor(private http: HttpClient) {}

  // =========================
  // AUTH
  // =========================
  login(data: any) {
    return this.http.post(`${this.baseUrl}/token/`, data);
  }

  // =========================
  // CATEGORIAS
  // =========================
  getCategorias() {
    return this.http.get(`${this.baseUrl}/categorias/`);
  }

  createCategoria(data: any) {
    return this.http.post(`${this.baseUrl}/categorias/`, data);
  }

  updateCategoria(id: number, data: any) {
    return this.http.put(`${this.baseUrl}/categorias/${id}/`, data);
  }

  deleteCategoria(id: number) {
    return this.http.delete(`${this.baseUrl}/categorias/${id}/`);
  }

  toggleCategoria(id: number) {
    return this.http.patch(`${this.baseUrl}/categorias/${id}/toggle_estado/`, {});
  }

  // =========================
  // PRODUCTOS
  // =========================
  getProductos(): Observable<Producto[]> {
    return this.http.get<Producto[]>(`${this.baseUrl}/productos/`);
  }

  createProducto(data: FormData) {
    return this.http.post(`${this.baseUrl}/productos/`, data);
  }

  // 🔥 FIX IMPORTANTE → PATCH EN VEZ DE PUT
  updateProducto(id: number, data: FormData) {
    return this.http.patch(`${this.baseUrl}/productos/${id}/`, data);
  }

  deleteProducto(id: number) {
    return this.http.delete(`${this.baseUrl}/productos/${id}/`);
  }

  toggleDestacado(id: number) {
    return this.http.patch(`${this.baseUrl}/productos/${id}/toggle_destacado/`, {});
  }

  actualizarStock(id: number, cantidad: number, sucursal_id?: number, motivo: string = "Ajuste") {
    return this.http.patch(`${this.baseUrl}/productos/${id}/actualizar_stock/`, { cantidad, sucursal_id, motivo });
  }

  // =========================
  // INVENTARIO
  // =========================
  getAlertasStock(): Observable<AlertaStock[]> {
    return this.http.get<AlertaStock[]>(`${this.baseUrl}/inventario/alertas_activas/`);
  }

  marcarAlertaLeida(id: number) {
    return this.http.patch(`${this.baseUrl}/alertas/${id}/marcar_leida/`, {});
  }

  marcarTodasLeidas() {
    return this.http.patch(`${this.baseUrl}/alertas/marcar_todas_leidas/`, {});
  }

  getInventario() {
    return this.http.get(`${this.baseUrl}/inventario/`);
  }

  getMovimientos() {
    return this.http.get<any[]>(`${this.baseUrl}/movimientos/`);
  }

  getAlertas() {
    return this.http.get<any[]>(`${this.baseUrl}/alertas/`);
  }

  // =========================
  // REPORTES
  // =========================
  getReportes() {
    return this.http.get(`${this.baseUrl}/reportes/`);
  }

  generarReporte(tipo: string) {
    return this.http.post(`${this.baseUrl}/reportes/generar/`, { tipo });
  }

  DeleteReporte(id: number) {
    return this.http.delete(`${this.baseUrl}/reportes/${id}/`);
  }

  // =========================
  // DASHBOARD
  // =========================
  getDashboard(): Observable<Dashboard> {

    if (!this.dashboardCache$) {
      this.dashboardCache$ = this.http
        .get<Dashboard>(`${this.baseUrl}/reportes/dashboard/`)
        .pipe(shareReplay(1)); // 🔥 cachea la respuesta
    }

    return this.dashboardCache$;
  }
}

// =========================
// INTERFACES
// =========================
export interface Categoria {
  id: number;
  nombre: string;
  estado: boolean;
}

export interface Producto {
  id: number;
  nombre: string;
  precio: number;
  stock: number;
  stock_minimo: number;
  categoria: number;
  estado: boolean;
  destacado: boolean;
}

export interface Dashboard {
  total_productos: number;
  total_categorias: number;
  total_usuarios: number;
  sucursales_activas?: number;
  alertas_no_leidas: number;
  productos_sin_stock: number;
  productos_destacados: number;
  productos_por_categoria: { nombre: string; total: number }[];
  productos_bajo_stock: any[];
  ganancias_hoy: number;
  total_pedidos_hoy: number;
  ticket_promedio: number;
  cajas_activas?: any[];
}

export interface AlertaStock {
  id: number;
  producto: string;
  stock: number;
  stock_minimo: number;
  leida: boolean;
}

export interface Reporte {
  id: number;
  tipo: string;
  datos: any;
  fecha: string;
}