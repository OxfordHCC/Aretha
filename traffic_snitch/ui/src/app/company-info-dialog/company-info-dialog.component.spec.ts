import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { CompanyInfoDialogComponent } from './company-info-dialog.component';

describe('CompanyInfoDialogComponent', () => {
  let component: CompanyInfoDialogComponent;
  let fixture: ComponentFixture<CompanyInfoDialogComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ CompanyInfoDialogComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(CompanyInfoDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
