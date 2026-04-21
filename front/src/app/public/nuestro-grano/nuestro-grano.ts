import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

@Component({
  standalone: true,
  imports: [CommonModule, RouterModule],
  selector: 'app-nuestro-grano',
  templateUrl: './nuestro-grano.html',
  styleUrls: ['./nuestro-grano.css']
})
export class NuestroGranoComponent {}
