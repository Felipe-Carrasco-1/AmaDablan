import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ProductosPublic } from './productos-public';

describe('ProductosPublic', () => {
  let component: ProductosPublic;
  let fixture: ComponentFixture<ProductosPublic>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ProductosPublic],
    }).compileComponents();

    fixture = TestBed.createComponent(ProductosPublic);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
