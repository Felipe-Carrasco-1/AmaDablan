import { Component, OnInit, inject, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

@Component({
  standalone: true,
  imports: [CommonModule, FormsModule],
  selector: 'app-pos',
  templateUrl: './pos.html',
  styleUrls: ['./pos.css']
})
export class PosComponent implements OnInit {
  http = inject(HttpClient);
  cdr = inject(ChangeDetectorRef);
  router = inject(Router);

  productos: any[] = [];
  categorias: any[] = [];
  categoriaSeleccionada: any = 'todos';
  
  carrito: any[] = [];
  total = 0;
  
  metodoPago = 'efectivo';
  sucursalActual = 'linares_catedral'; 
  
  procesando = false;

  ngOnInit() {
    this.cargarDatos();
  }

  cargarDatos() {
    this.http.get<any[]>('http://localhost:8000/api/categorias/').subscribe(res => this.categorias = res);
    this.http.get<any[]>('http://localhost:8000/api/productos/?estado=true').subscribe(res => {
      this.productos = res;
      this.cdr.detectChanges();
    });
  }

  get productosFiltrados() {
    if (this.categoriaSeleccionada === 'todos') return this.productos;
    return this.productos.filter(p => p.categoria == this.categoriaSeleccionada);
  }

  agregarAlCarrito(producto: any) {
    const existe = this.carrito.find(item => item.id === producto.id);
    if (existe) {
      existe.cantidad++;
    } else {
      this.carrito.push({ ...producto, cantidad: 1 });
    }
    this.calcularTotal();
  }

  quitarDelCarrito(id: number) {
    this.carrito = this.carrito.filter(item => item.id !== id);
    this.calcularTotal();
  }

  cambiarCantidad(id: number, delta: number) {
    const item = this.carrito.find(i => i.id === id);
    if (item) {
      item.cantidad += delta;
      if (item.cantidad <= 0) this.quitarDelCarrito(id);
    }
    this.calcularTotal();
  }

  calcularTotal() {
    this.total = this.carrito.reduce((acc, item) => acc + (item.precio * item.cantidad), 0);
  }

  finalizarVenta() {
    if (this.carrito.length === 0) return;
    
    this.procesando = true;
    const payload = {
      metodo_pago: this.metodoPago,
      sucursal: this.sucursalActual,
      nombre_cliente: 'Venta Presencial',
      items: this.carrito.map(i => ({ producto_id: i.id, cantidad: i.cantidad })),
      estado: 'entregado'
    };

    this.http.post('http://localhost:8000/api/pedidos/', payload).subscribe({
      next: (res: any) => {
        this.procesando = true;
        this.imprimirTicket(res);
        setTimeout(() => {
          this.procesando = false;
          this.carrito = [];
          this.total = 0;
          this.cdr.detectChanges();
        }, 1000);
      },
      error: () => {
        this.procesando = false;
        alert('Error al registrar la venta');
      }
    });
  }

  getIcon(nombre: string): string {
    const key = nombre.toLowerCase();
    if (key.includes('café')) return '☕';
    if (key.includes('sandwich') || key.includes('sándwich')) return '🥪';
    if (key.includes('snack') || key.includes('pasteler') || key.includes('muffin') || key.includes('dulce')) return '🍰';
    if (key.includes('bebida') || key.includes('jugo')) return '🥤';
    return '📦';
  }

  imprimirTicket(pedido: any) {
    const printWindow = window.open('', '_blank', 'width=450,height=600');
    if (!printWindow) return;

    const fecha = new Date().toLocaleString('es-CL');
    const itemsHtml = pedido.detalles.map((d: any) => `
      <tr>
        <td style="padding: 5px 0;">${d.cantidad}x ${d.producto_nombre}</td>
        <td style="text-align: right;">$${Number(d.precio_unitario * d.cantidad).toLocaleString('es-CL')}</td>
      </tr>
    `).join('');

    printWindow.document.write(`
      <html>
        <head>
          <style>
            body { font-family: 'Courier New', monospace; width: 80mm; padding: 5mm; }
            .header { text-align: center; border-bottom: 1px dashed #000; padding-bottom: 5px; }
            table { width: 100%; font-size: 0.9rem; margin-top: 10px; }
            .total { border-top: 1px dashed #000; margin-top: 10px; padding-top: 5px; font-weight: bold; display: flex; justify-content: space-between; }
          </style>
        </head>
        <body>
          <div class="header"><strong>AMA DABLAM COFFEE</strong><br>Venta Presencial #${pedido.id}</div>
          <div style="font-size: 0.8rem; margin-top: 5px;">Fecha: ${fecha}<br>Sucursal: Linares Catedral</div>
          <table>${itemsHtml}</table>
          <div class="total"><span>TOTAL:</span><span>$${Number(pedido.total).toLocaleString('es-CL')}</span></div>
          <div style="text-align: center; font-size: 0.7rem; margin-top: 15px;">¡Gracias por su visita!</div>
          <script>setTimeout(() => { window.print(); window.close(); }, 500);</script>
        </body>
      </html>
    `);
    printWindow.document.close();
  }
}
