import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { LayoutTimeseriesComponent } from './layout-timeseries.component';

describe('LayoutTimeseriesComponent', () => {
  let component: LayoutTimeseriesComponent;
  let fixture: ComponentFixture<LayoutTimeseriesComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ LayoutTimeseriesComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(LayoutTimeseriesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
