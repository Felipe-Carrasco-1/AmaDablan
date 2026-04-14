import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AdminProductos } from './productos';

describe('Productos', () => {
  let component: AdminProductos;
  let fixture: ComponentFixture<AdminProductos>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AdminProductos],
    }).compileComponents();

    fixture = TestBed.createComponent(AdminProductos);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
