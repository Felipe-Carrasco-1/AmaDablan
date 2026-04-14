import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AdminInventario } from './inventario';

describe('Inventario', () => {
  let component: AdminInventario;
  let fixture: ComponentFixture<AdminInventario>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AdminInventario],
    }).compileComponents();

    fixture = TestBed.createComponent(AdminInventario);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
