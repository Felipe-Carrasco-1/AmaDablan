import { Injectable, inject, PLATFORM_ID } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { isPlatformBrowser } from '@angular/common';
import { tap } from 'rxjs/operators';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private url = 'http://localhost:8000/api';
  private platformId = inject(PLATFORM_ID);
  private router = inject(Router);
  private http = inject(HttpClient);

  currentUser: any = null;

  constructor() {
    this.loadUser();
  }

  private loadUser() {
    if (isPlatformBrowser(this.platformId)) {
      const saved = localStorage.getItem('user');
      if (saved) this.currentUser = JSON.parse(saved);
    }
  }

  login(email: string, password: string) {
    return this.http.post<any>(`${this.url}/token/`, { email, password }).pipe(
      tap(res => {
        if (isPlatformBrowser(this.platformId)) {
          localStorage.setItem('access', res.access);
          localStorage.setItem('refresh', res.refresh);
          localStorage.setItem('user', JSON.stringify(res));
          this.currentUser = res;
        }
      })
    );
  }

  logout() {
    this.currentUser = null;
    if (isPlatformBrowser(this.platformId)) {
      localStorage.removeItem('access');
      localStorage.removeItem('refresh');
      localStorage.removeItem('user');
    }
    this.router.navigate(['/login']); // Redirección inmediata
  }

  get isLoggedIn(): boolean {
    if (!isPlatformBrowser(this.platformId)) return false;
    return !!localStorage.getItem('access');
  }

  get isAdmin(): boolean {
    return this.currentUser?.rol === 'admin' || this.currentUser?.is_staff === true;
  }

  get isCajero(): boolean {
    return this.currentUser?.rol === 'cajero';
  }

  get isEncargadoStock(): boolean {
    return this.currentUser?.rol === 'encargado_stock';
  }

  get sucursalId(): number | null {
    return this.currentUser?.sucursal || null;
  }

  get sucursalName(): string {
    return this.currentUser?.sucursal_nombre || 'Sede Principal';
  }
}