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
      this.cdr.detectChanges(); // ✅
    });
  }

  cargar(): void {
    this.api.getProductos().subscribe((data: any) => {
      this.productos          = data;
      this.productosFiltrados = data;
      this.cdr.detectChanges(); // ✅
    });
  }

  emptyForm() {
    return { nombre: '', precio: 0, stock: 0, stock_minimo: 10, categoria: '', descripcion: '', estado: true, destacado: false };
  }

  openModal(p?: any) {
    this.editando  = !!p;
    this.form      = p ? { ...p } : this.emptyForm();
    this.showModal = true;
    this.cdr.detectChanges(); // ✅
  }

  closeModal() {
    this.showModal = false;
    this.cdr.detectChanges(); // ✅
  }

  guardar() {
  this.loading = true;
  this.error = ''; // Limpiar errores previos
  
  const fd = new FormData();

  // 1. Enviamos los campos de texto uno por uno
  // Evitamos enviar objetos complejos o URLs de imágenes viejas
  fd.append('nombre', this.form.nombre);
  fd.append('precio', this.form.precio.toString());
  fd.append('stock', this.form.stock.toString());
  fd.append('stock_minimo', this.form.stock_minimo.toString());
  fd.append('categoria', this.form.categoria);
  fd.append('descripcion', this.form.descripcion || '');
  fd.append('estado', this.form.estado ? 'true' : 'false');
  fd.append('destacado', this.form.destacado ? 'true' : 'false');

  // 2. LA CLAVE: Solo anexar la imagen si es un ARCHIVO nuevo
  if (this.selectedFile) {
    fd.append('imagen', this.selectedFile);
  }

  // 3. Decidir si es UPDATE o CREATE
  const req = this.editando
    ? this.api.updateProducto(this.form.id, fd) // Asegúrate que use .patch() internamente
    : this.api.createProducto(fd);

  req.subscribe({
    next: () => {
      this.loading = false;
      this.successMsg = this.editando ? 'Producto actualizado' : 'Producto creado';
      this.selectedFile = null; // Resetear archivo
      this.closeModal();
      this.cargar();
      setTimeout(() => { 
        this.successMsg = ''; 
        this.cdr.detectChanges(); 
      }, 2500);
    },
    error: (err) => {
      this.loading = false;
      // Mostrar un mensaje más amigable que el JSON crudo
      this.error = err.error?.imagen ? 'El archivo de imagen no es válido.' : 'Error al guardar el producto.';
      console.error(err);
      this.cdr.detectChanges();
    }
  });
}

filtrar() {
  this.productosFiltrados = this.productos.filter(p => {

    // 🔍 BUSCADOR
    const coincideBusqueda =
      !this.search ||
      p.nombre?.toLowerCase().includes(this.search.toLowerCase());

    // 📦 CATEGORÍA (usa ID)
    const coincideCategoria =
      !this.filtroCategoria ||
      p.categoria == this.filtroCategoria;

    // ✅ ESTADO (true / false como string)
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