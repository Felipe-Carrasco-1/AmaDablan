import { Component, ViewEncapsulation } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../core/services/auth.service'; // ajusta ruta

@Component({
  standalone: true,
  selector: 'app-contacto',
  imports: [CommonModule, RouterModule, FormsModule],
  templateUrl: './contacto.html',
  styleUrls: ['./contacto.css'],
  encapsulation: ViewEncapsulation.None
})
export class Contacto {

  form = { nombre: '', email: '', mensaje: '' };
  enviado = false;
  loading = false;

  constructor(public auth: AuthService) {}

  get isLoggedIn() { return this.auth.isLoggedIn; }
  get isAdmin()    { return this.auth.isAdmin; }

  enviar() {
    this.loading = true;
    setTimeout(() => {
      this.loading = false;
      this.enviado = true;
      this.form = { nombre: '', email: '', mensaje: '' };
    }, 1200);
  }
}