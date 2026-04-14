// pages/auth/login/login.component.ts
import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../core/services/auth.service';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';

@Component({
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule],
  selector: 'app-login',
  templateUrl: './login.html',
  styleUrls: ['./login.css']
})
export class LoginComponent {

  email = '';
  password = '';
  loading = false;
  error = '';

 constructor(
  private auth: AuthService,
  private router: Router
) {
  if (this.auth.isLoggedIn) {
    this.router.navigate([
      this.auth.isAdmin ? '/admin/dashboard' : '/'
    ]);
  }
}

onSubmit(): void {
  this.error = '';
  this.loading = true;

  this.auth.login(this.email, this.password).subscribe({
    next: (res: any) => {
      this.loading = false;

      const role = res.user?.rol || res.rol;

      this.router.navigate([
        role === 'admin' ? '/admin/dashboard' : '/'
      ]);
    },
    error: () => {
      this.loading = false;
      this.error = 'Credenciales incorrectas. Verifica tu email y contraseña.';
    }
  });
}
}
