import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { ApiService } from '../core/services/api.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';

@Component({
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule],
  selector: 'app-productos',
  templateUrl: './productos.html',
  styleUrls: ['./productos.css']
})
export class AdminProductos implements OnInit {

  productos: any[]          = [];
  productosFiltrados: any[] = [];
  categorias: any[]         = [];

  search          = '';
  filtroCategoria = '';
  filtroEstado    = '';
  showModal       = false;
  editando        = false;
  loading         = false;
  error           = '';
  successMsg      = '';
  selectedFile: File | null = null;

  form: any = this.emptyForm();

  constructor(private api: ApiService, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    this.cargar();

    this.api.getCategorias().subscribe((data: any) => {
      this.categorias = data;
      this.cdr.detectChanges();
    });
  }

  cargar(): void {
    this.api.getProductos().subscribe((data: any) => {
      this.productos = data;
      this.productosFiltrados = data;
      this.cdr.detectChanges();
    });
  }

  emptyForm() {
    return {
      nombre: '',
      precio: '',
      stock: 0,
      stock_minimo: 10,
      categoria: null,
      descripcion: '',
      estado: true,
      destacado: false
    };
  }

  openModal(p?: any) {
    this.editando = !!p;

    this.form = p
      ? {
          ...p,
          categoria: p.categoria?.id ?? p.categoria,
          precio: p.precio?.toString() // 🔥 evitar problemas con decimal
        }
      : this.emptyForm();

    this.showModal = true;
    this.cdr.detectChanges();
  }

  closeModal() {
    this.showModal = false;
    this.cdr.detectChanges();
  }

  guardar() {
    this.loading = true;
    this.error = '';

    const fd = new FormData();

    // 🔥 LIMPIAR PRECIO (FIX CLAVE)
    let precioRaw = this.form.precio?.toString() || '0';

    // eliminar comas (ej: 2,500 → 2500)
    precioRaw = precioRaw.replace(/,/g, '').trim();

    const precio = Number(precioRaw);

    if (isNaN(precio) || precio <= 0) {
      this.error = 'Precio inválido';
      this.loading = false;
      return;
    }

    // ✅ Campos
    fd.append('nombre', this.form.nombre);
    fd.append('precio', precio.toString());
    fd.append('stock', String(Number(this.form.stock)));
    fd.append('stock_minimo', String(this.form.stock_minimo ?? 10));

    // ✅ categoría
    const categoriaId =
      typeof this.form.categoria === 'object'
        ? this.form.categoria.id
        : this.form.categoria;

    fd.append('categoria', String(Number(categoriaId)));

    fd.append('descripcion', this.form.descripcion || '');
    fd.append('estado', this.form.estado ? 'true' : 'false');
    fd.append('destacado', this.form.destacado ? 'true' : 'false');

    // ✅ imagen
    if (this.selectedFile) {
      fd.append('imagen', this.selectedFile);
    }

    // 🧪 DEBUG
    console.log('--- DATA QUE SE ENVÍA ---');
    for (let pair of fd.entries()) {
      console.log(pair[0], pair[1]);
    }

    const req = this.editando
      ? this.api.updateProducto(this.form.id, fd)
      : this.api.createProducto(fd);

    req.subscribe({
      next: () => {
        this.loading = false;
        this.successMsg = this.editando
          ? 'Producto actualizado'
          : 'Producto creado';

        this.selectedFile = null;
        this.closeModal();
        this.cargar();

        setTimeout(() => {
          this.successMsg = '';
          this.cdr.detectChanges();
        }, 2500);
      },
      error: (err) => {
        this.loading = false;
        console.error('ERROR BACKEND:', err);

        if (err.error) {
          this.error = Object.values(err.error).flat().join(' ');
        } else {
          this.error = 'Error al guardar el producto.';
        }

        this.cdr.detectChanges();
      }
    });
  }

  filtrar() {
    this.productosFiltrados = this.productos.filter(p => {

      const coincideBusqueda =
        !this.search ||
        p.nombre?.toLowerCase().includes(this.search.toLowerCase());

      const coincideCategoria =
        !this.filtroCategoria ||
        p.categoria == this.filtroCategoria;

      const coincideEstado =
        this.filtroEstado === '' ||
        p.estado.toString() === this.filtroEstado;

      return coincideBusqueda && coincideCategoria && coincideEstado;
    });

    this.cdr.detectChanges();
  }

  onFileChange(event: any) {
    this.selectedFile = event.target.files[0];
  }

  toggleDestacado(p: any) {
    this.api.toggleDestacado(p.id).subscribe(() => this.cargar());
  }

  eliminar(p: any) {
    if (confirm('¿Eliminar?')) {
      this.api.deleteProducto(p.id).subscribe(() => this.cargar());
    }
  }
}