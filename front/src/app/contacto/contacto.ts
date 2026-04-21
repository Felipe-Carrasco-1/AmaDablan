import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { AuthService } from '../core/services/auth.service';

@Component({
  standalone: true,
  selector: 'app-contacto',
  imports: [CommonModule, FormsModule],
  templateUrl: './contacto.html'
})
export class Contacto {
  http = inject(HttpClient);
  auth = inject(AuthService);

  form = {
    nombre: '',
    email: '',
    mensaje: ''
  };

  loading = false;
  enviado = false;

  enviar() {
    if (!this.form.nombre || !this.form.email || !this.form.mensaje) {
      alert('Por favor completa todos los campos.');
      return;
    }

    this.loading = true;
    this.http.post('http://localhost:8000/api/contacto/', this.form).subscribe({
      next: () => {
        this.loading = false;
        this.enviado = true;
      },
      error: () => {
        this.loading = false;
        alert('Hubo un error al enviar el mensaje. Por favor intenta de nuevo.');
      }
    });
  }
}