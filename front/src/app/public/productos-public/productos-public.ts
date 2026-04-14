import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { ActivatedRoute, RouterModule } from '@angular/router'; // 👈 Necesario para leer la URL

@Component({
  standalone: true,
  selector: 'app-productos-public',
  imports: [CommonModule, RouterModule],
  templateUrl: './productos-public.html',
  styleUrls: ['./productos-public.css']
})
export class ProductosPublic implements OnInit {

  productos: any[] = [];
  loading = true;
  error = '';
  categoriaId: string | null = null; // Guardar el filtro actual

  constructor(
    private http: HttpClient, 
    private route: ActivatedRoute, // 👈 Inyectamos la ruta activa
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit() {
    // Escuchamos los cambios en la URL (por si el usuario pincha filtros sin recargar la página)
    this.route.queryParams.subscribe(params => {
      this.categoriaId = params['categoria'] || null;
      this.cargarProductos();
    });
  }

  cargarProductos() {
    this.loading = true;
    
    // Construimos la URL con los filtros de Django
    // Filtramos por activos=true y opcionalmente por categoría
    let url = 'http://localhost:8000/api/productos/?estado=true';
    
    if (this.categoriaId) {
      url += `&categoria=${this.categoriaId}`;
    }

    this.http.get<any[]>(url).subscribe({
      next: (res) => {
        this.productos = res;
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.loading = false;
        this.error = 'No se pudieron cargar los productos.';
        console.error(err);
        this.cdr.detectChanges();
      }
    });
  }
}