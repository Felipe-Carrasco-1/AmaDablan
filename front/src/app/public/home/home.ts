// home.ts
import { Component, OnInit, OnDestroy, ChangeDetectorRef, ViewEncapsulation } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { AuthService } from '../../core/services/auth.service';

@Component({
  standalone: true,
  selector: 'app-home',
  imports: [CommonModule, RouterModule],
  templateUrl: './home.html',
  styleUrls: ['./home.css'],
  encapsulation: ViewEncapsulation.None
})
export class Home implements OnInit, OnDestroy {

  currentSlide = 0;
  private sliderInterval: any;

slides = [
  { titulo: 'Tostamos tu próximo café',      bg: 'assets/images/hero1.jpg' },
  { titulo: 'Café de especialidad chileno',  bg: 'assets/images/hero2.jpg' },
  { titulo: 'Del origen a tu taza',          bg: 'assets/images/hero3.jpg' },
  { titulo: 'Granos seleccionados a mano',   bg: 'assets/images/hero4.jpg' },
];

  categorias: any[]          = [];
  productosDestacados: any[] = [];
  mapUrl: SafeResourceUrl;

  sucursales = [
    { nombre: 'Catedral de Linares',   distancia: '~97.5662 km' },
    { nombre: 'Hospital Base Linares', distancia: '~52.504 km'  },
    { nombre: '2 Oriente Talca',       distancia: '~94.504 km'  },
  ];

  iconosCategorias: { [key: string]: string } = {
  'Cafés': '☕',
  'Congelados': '🍦',
  'Snacks': '🍰',
  'Bebidas': '🥤'
};

getIcon(nombre: string): string {
  const key = nombre.toLowerCase();

  if (key.includes('café')) return '☕';
  if (key.includes('congel')) return '🍦';

  return '📦';
}

  constructor(
    private http: HttpClient,
    private sanitizer: DomSanitizer,
    private cdr: ChangeDetectorRef,
    public auth: AuthService
  ) {
    this.mapUrl = this.sanitizer.bypassSecurityTrustResourceUrl(
      'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3275.9831520733716!2d-71.59824492394283!3d-35.84665337240633!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x9669237e3a9b4e4b%3A0x32f7b02b9a5c2e4d!2sLinares%2C%20Maule!5e0!3m2!1ses!2scl!4v1'
    );
  }

  ngOnInit(): void {
    this.http.get<any[]>('http://localhost:8000/api/categorias/?activas=true').subscribe({
      next: (d) => { this.categorias = d; this.cdr.detectChanges(); },
      error: () => {}
    });

    this.http.get<any[]>('http://localhost:8000/api/productos/?destacado=true&activos=true').subscribe({
      next: (d) => { this.productosDestacados = d; this.cdr.detectChanges(); },
      error: () => {}
    });

    this.sliderInterval = setInterval(() => {
      this.currentSlide = (this.currentSlide + 1) % this.slides.length;
      this.cdr.detectChanges();
    }, 5000);
  }

  ngOnDestroy(): void { clearInterval(this.sliderInterval); }

  prevSlide(): void {
    this.currentSlide = (this.currentSlide - 1 + this.slides.length) % this.slides.length;
    this.cdr.detectChanges();
  }

  nextSlide(): void {
    this.currentSlide = (this.currentSlide + 1) % this.slides.length;
    this.cdr.detectChanges();
  }

  goSlide(i: number): void {
    this.currentSlide = i;
    this.cdr.detectChanges();
  }

  menuAbierto = false;

toggleMenu(): void {
  this.menuAbierto = !this.menuAbierto;
  this.cdr.detectChanges();
}


  formatPrecio(precio: any): string {
    return '$' + Number(precio).toLocaleString('es-CL', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    });
  }
}