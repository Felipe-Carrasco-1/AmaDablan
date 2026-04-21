import { Component, OnInit } from '@angular/core';
import { ApiService } from '../core/services/api.service';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

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
  ganancias_hoy: number;
  total_pedidos_hoy: number;
  ticket_promedio: number;
  sucursales_activas?: number;
  cajas_activas?: any[];
}

const DEFAULT_DASHBOARD: Dashboard = {
  total_productos: 0,
  total_categorias: 0,
  total_usuarios: 0,
  alertas_no_leidas: 0,
  productos_sin_stock: 0,
  productos_destacados: 0,
  productos_por_categoria: [],
  productos_bajo_stock: [],
  ganancias_hoy: 0,
  total_pedidos_hoy: 0,
  ticket_promedio: 0
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
  pedidosRecientes: any[] = [];

  constructor(private api: ApiService, private http: HttpClient) {}

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

    // Cargar los últimos pedidos
    this.http.get<any[]>('http://localhost:8000/api/pedidos/').subscribe({
      next: (data) => {
        this.pedidosRecientes = data.slice(0, 15); // Mostrar los 15 más recientes
      },
      error: (err) => console.error('Error cargando pedidos', err)
    });
  }

  actualizarEstado(pedido: any, event: any) {
    const nuevoEstado = event.target.value;
    const estadoAnterior = pedido.estado;
    
    // 1. Actualización optimista (cambia la UI al instante)
    pedido.estado = nuevoEstado;

    // 2. Enviar en segundo plano
    this.http.patch(`http://localhost:8000/api/pedidos/${pedido.id}/`, { estado: nuevoEstado }).subscribe({
      next: () => {
        // Éxito: no hacemos nada porque la UI ya se actualizó
      },
      error: (err) => {
        console.error('Error actualizando pedido', err);
        // Si falla, revertimos al estado anterior
        pedido.estado = estadoAnterior;
        event.target.value = estadoAnterior;
        alert('Hubo un error al conectar con el servidor. Intenta de nuevo.');
      }
    });
  }

  barPct(val: number): number {
    const categorias = this.dashboard.productos_por_categoria || [];

    if (categorias.length === 0) return 0;

    const max = Math.max(...categorias.map(c => c.total), 1);

    return (val / max) * 100;
  }

  formatSucursal(val: string): string {
    const dict: any = {
      'linares_catedral': '📍 Linares Catedral',
      'linares_hospital': '🏥 Linares Hospital',
      'talca': '🏙️ Sucursal Talca'
    };
    return dict[val] || val;
  }

  imprimirBoleta(pedido: any) {
    const printWindow = window.open('', '_blank', 'width=450,height=600');
    if (!printWindow) return;

    const fecha = new Date(pedido.fecha).toLocaleString('es-CL');
    const itemsHtml = pedido.detalles.map((d: any) => `
      <tr>
        <td style="padding: 5px 0;">${d.cantidad}x ${d.producto_nombre}</td>
        <td style="text-align: right;">$${Number(d.precio_unitario * d.cantidad).toLocaleString('es-CL')}</td>
      </tr>
    `).join('');

    printWindow.document.write(`
      <html>
        <head>
          <title>Ticket #${pedido.id}</title>
          <style>
            @page { margin: 0; }
            body { 
              font-family: 'Courier New', Courier, monospace; 
              width: 80mm; 
              margin: 0; 
              padding: 10mm; 
              color: #000; 
              background: white;
            }
            .header { text-align: center; border-bottom: 1px dashed #000; padding-bottom: 10px; margin-bottom: 10px; }
            .logo { font-weight: bold; font-size: 1.2rem; text-transform: uppercase; }
            .info { font-size: 0.85rem; margin-bottom: 15px; line-height: 1.4; }
            table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
            .total-row { border-top: 1px dashed #000; margin-top: 10px; padding-top: 10px; font-weight: bold; font-size: 1.1rem; display: flex; justify-content: space-between; }
            .footer { text-align: center; font-size: 0.75rem; margin-top: 30px; border-top: 1px solid #eee; padding-top: 10px; }
            .no-print { display: none; }
          </style>
        </head>
        <body>
          <div class="header">
            <div class="logo">Ama Dablam Coffee</div>
            <div style="font-size: 0.7rem;">Tostamos tu próximo café</div>
          </div>
          
          <div class="info">
            <strong>TICKET DE VENTA #${pedido.id}</strong><br>
            📅 Fecha: ${fecha}<br>
            📍 Sucursal: ${this.formatSucursal(pedido.sucursal)}<br>
            👤 Cliente: ${pedido.nombre_cliente || 'Invitado'}<br>
            📞 Tel: ${pedido.telefono_cliente || '-'}<br>
            💳 Pago: ${pedido.metodo_pago.toUpperCase()}
          </div>

          <table>
            <thead>
              <tr style="border-bottom: 1px solid #eee;">
                <th style="text-align: left;">Detalle</th>
                <th style="text-align: right;">Subtotal</th>
              </tr>
            </thead>
            <tbody>
              ${itemsHtml}
            </tbody>
          </table>

          <div class="total-row">
            <span>TOTAL:</span>
            <span>$${Number(pedido.total).toLocaleString('es-CL')}</span>
          </div>

          <div class="footer">
            ¡Gracias por preferirnos!<br>
            www.amadablam.cl<br>
            Linares, Chile
          </div>

          <script>
            setTimeout(() => {
              window.print();
              window.close();
            }, 500);
          </script>
        </body>
      </html>
    `);
    printWindow.document.close();
  }
}