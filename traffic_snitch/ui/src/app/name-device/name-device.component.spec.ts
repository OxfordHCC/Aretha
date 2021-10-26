import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { NamedeviceComponent } from './namedevice.component';

describe('NamedeviceComponent', () => {
  let component: NamedeviceComponent;
  let fixture: ComponentFixture<NamedeviceComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ NamedeviceComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(NamedeviceComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
