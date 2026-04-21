import { Component, inject, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';

@Component({
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule],
  selector: 'app-reset-password',
  template: `
    <div class="login-page">
      <div class="login-card">
        <div class="login-brand">
          <svg width="48" height="48" viewBox="0 0 40 40" fill="none">
            <path d="M20 4 L36 32 L4 32 Z" stroke="#c8923a" stroke-width="2" fill="none"/>
            <path d="M14 24 L26 24" stroke="#c8923a" stroke-width="1.5"/>
          </svg>
          <h1>Ama Dablam <span>Coffee</span></h1>
          <p>Establecer Nueva Contraseña</p>
        </div>

        <div class="alert alert-success" style="background: #dcfce3; color: #15803d; padding: 12px; border-radius: 8px; margin-bottom: 20px; font-size: 0.9rem;" *ngIf="mensaje">{{ mensaje }}</div>
        <div class="alert alert-danger" style="background: #fee2e2; color: #b91c1c; padding: 12px; border-radius: 8px; margin-bottom: 20px; font-size: 0.9rem;" *ngIf="error">{{ error }}</div>

        <form (ngSubmit)="onSubmit()" *ngIf="!exito && !error">
          <div class="form-group" style="margin-bottom: 20px;">
            <label style="display: block; margin-bottom: 8px; color: #64748b; font-size: 0.9rem;">Nueva contraseña</label>
            <input type="password" class="form-control" [(ngModel)]="password" name="password" required placeholder="••••••••" 
              style="width: 100%; padding: 12px; border: 1px solid #e2e8f0; border-radius: 8px; box-sizing: border-box;" />
          </div>
          <button type="submit" class="btn btn-primary" [disabled]="loading"
            style="width: 100%; padding: 14px; background: #c8923a; color: #1a0f08; border: none; border-radius: 8px; font-weight: bold; cursor: pointer;">
            {{ loading ? 'Actualizando...' : 'Cambiar contraseña' }}
          </button>
        </form>

        <p class="login-back" style="text-align: center; margin-top: 25px;">
          <a routerLink="/login" style="color: #64748b; text-decoration: none; font-size: 0.9rem;">Ir al inicio de sesión</a>
        </p>
      </div>
    </div>
  `,
  styleUrls: ['./login.css']
})
export class ResetPasswordComponent implements OnInit {
  http = inject(HttpClient);
  route = inject(ActivatedRoute);
  router = inject(Router);

  uid = '';
  token = '';
  password = '';
  loading = false;
  mensaje = '';
  error = '';
  exito = false;

  ngOnInit() {
    this.uid = this.route.snapshot.queryParams['uid'];
    this.token = this.route.snapshot.queryParams['token'];

    if (!this.uid || !this.token) {
      this.error = 'El enlace de recuperación no es válido o está incompleto.';
    }
  }

  onSubmit() {
    if (!this.password || this.password.length < 6) {
      this.error = 'La contraseña debe tener al menos 6 caracteres.';
      return;
    }

    this.loading = true;
    this.error = '';
    const payload = { uid: this.uid, token: this.token, password: this.password };
    
    this.http.post('http://localhost:8000/api/usuarios/reset-password/', payload).subscribe({
      next: (res: any) => {
        this.loading = false;
        this.mensaje = res.mensaje;
        this.exito = true;
        // Redirigir al login tras 3 segundos
        setTimeout(() => this.router.navigate(['/login']), 3000);
      },
      error: () => {
        this.loading = false;
        this.error = 'No se pudo actualizar la contraseña. Es posible que el enlace haya expirado.';
      }
    });
  }
}
