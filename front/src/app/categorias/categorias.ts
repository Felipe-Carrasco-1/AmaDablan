import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { ApiService, Categoria } from '../core/services/api.service';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';

@Component({
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule],
  selector: 'app-admin-categorias',
  templateUrl: './categorias.html',
  styleUrls: ['./categorias.css']
})
export class AdminCategorias implements OnInit {

  categorias: any[] = [];
  showModal  = false;
  editando   = false;
  loading    = false;
  error      = '';
  successMsg = '';
  form: any  = { nombre: '', estado: true };

  constructor(
    private api: ApiService,
    private cdr: ChangeDetectorRef  // ✅ agrega esto
  ) {}

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.api.getCategorias().subscribe((d: any) => {
      this.categorias = d;
      this.cdr.detectChanges(); // ✅ fuerza actualización de la vista
    });
  }

  openModal(c?: Categoria): void {
    this.error      = '';
    this.successMsg = '';
    this.editando   = !!c;
    this.form       = c ? { ...c } : { nombre: '', estado: true };
    this.showModal  = true;
    this.cdr.detectChanges(); // ✅
  }

  closeModal(): void {
    this.showModal = false;
    this.cdr.detectChanges(); // ✅
  }

  guardar(): void {
    this.loading = true;
    this.error   = '';

    const request = this.editando
      ? this.api.updateCategoria(this.form.id, this.form)
      : this.api.createCategoria(this.form);

    request.subscribe({
      next: () => {
        this.loading    = false;
        this.successMsg = 'Guardado correctamente';
        this.closeModal();
        this.cargar();
        setTimeout(() => {
          this.successMsg = '';
          this.cdr.detectChanges(); // ✅
        }, 2500);
      },
      error: (e: any) => {
        this.loading = false;
        this.error   = JSON.stringify(e?.error);
        this.cdr.detectChanges(); // ✅
      }
    });
  }

  toggleEstado(c: Categoria): void {
    this.api.toggleCategoria(c.id).subscribe(() => this.cargar());
  }

  eliminar(c: Categoria): void {
    if (confirm(`¿Eliminar categoría "${c.nombre}"?`)) {
      this.api.deleteCategoria(c.id).subscribe(() => this.cargar());
    }
  }
}