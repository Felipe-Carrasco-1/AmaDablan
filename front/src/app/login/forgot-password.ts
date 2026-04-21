import { Component, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';

@Component({
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule],
  selector: 'app-forgot-password',
  template: `
    <div class="login-page">
      <div class="login-card">
        <div class="login-brand">
          <svg width="48" height="48" viewBox="0 0 40 40" fill="none">
            <path d="M20 4 L36 32 L4 32 Z" stroke="#c8923a" stroke-width="2" fill="none"/>
            <path d="M14 24 L26 24" stroke="#c8923a" stroke-width="1.5"/>
          </svg>
          <h1>Ama Dablam <span>Coffee</span></h1>
          <p>Recuperar Contraseña</p>
        </div>

        <div class="alert alert-success" style="background: #dcfce3; color: #15803d; padding: 12px; border-radius: 8px; margin-bottom: 20px; font-size: 0.9rem;" *ngIf="mensaje">{{ mensaje }}</div>
        <div class="alert alert-danger" style="background: #fee2e2; color: #b91c1c; padding: 12px; border-radius: 8px; margin-bottom: 20px; font-size: 0.9rem;" *ngIf="error">{{ error }}</div>

        <form (ngSubmit)="onSubmit()" *ngIf="!enviado">
          <div class="form-group" style="margin-bottom: 20px;">
            <label style="display: block; margin-bottom: 8px; color: #64748b; font-size: 0.9rem;">Correo electrónico</label>
            <input type="email" class="form-control" [(ngModel)]="email" name="email" required placeholder="tu@email.com" 
              style="width: 100%; padding: 12px; border: 1px solid #e2e8f0; border-radius: 8px; box-sizing: border-box;" />
          </div>
          <button type="submit" class="btn btn-primary" [disabled]="loading"
            style="width: 100%; padding: 14px; background: #c8923a; color: #1a0f08; border: none; border-radius: 8px; font-weight: bold; cursor: pointer;">
            {{ loading ? 'Enviando...' : 'Enviar enlace de recuperación' }}
          </button>
        </form>

        <p class="login-back" style="text-align: center; margin-top: 25px;">
          <a routerLink="/login" style="color: #64748b; text-decoration: none; font-size: 0.9rem;">← Volver al inicio de sesión</a>
        </p>
      </div>
    </div>
  `,
  styleUrls: ['./login.css']
})
export class ForgotPasswordComponent {
  http = inject(HttpClient);
  email = '';
  loading = false;
  mensaje = '';
  error = '';
  enviado = false;

  onSubmit() {
    if (!this.email) return;
    this.loading = true;
    this.error = '';
    this.http.post('http://localhost:8000/api/usuarios/recuperar-password/', { email: this.email }).subscribe({
      next: (res: any) => {
        this.loading = false;
        this.mensaje = res.mensaje;
        this.enviado = true;
      },
      error: () => {
        this.loading = false;
        this.error = 'Hubo un error al procesar tu solicitud. Intenta de nuevo.';
      }
    });
  }
}
