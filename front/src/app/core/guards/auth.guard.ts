import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const authGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);

  // ❌ no logueado
  if (!auth.isLoggedIn) {
    return router.createUrlTree(['/login']);
  }

  // ❌ logueado pero NO es admin
  if (!auth.isAdmin) {
    return router.createUrlTree(['/']);
  }

  // ✅ es admin
  return true;
};