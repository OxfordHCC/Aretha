import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ContentTrackingComponent } from './content-tracking.component';

describe('ContentTrackingComponent', () => {
  let component: ContentTrackingComponent;
  let fixture: ComponentFixture<ContentTrackingComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ContentTrackingComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ContentTrackingComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
