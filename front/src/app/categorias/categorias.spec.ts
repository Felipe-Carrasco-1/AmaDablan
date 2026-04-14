import { ComponentFixture, TestBed } from '@angular/core/testing';
import { AdminCategorias } from './categorias';

describe('Categorias', () => {
  let component: AdminCategorias;
  let fixture: ComponentFixture<AdminCategorias>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [AdminCategorias],
    }).compileComponents();

    fixture = TestBed.createComponent(AdminCategorias);
    component = fixture.componentInstance;

    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});