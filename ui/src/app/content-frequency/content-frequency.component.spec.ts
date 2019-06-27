import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ContentFrequencyComponent } from './content-frequency.component';

describe('ContentFrequencyComponent', () => {
  let component: ContentFrequencyComponent;
  let fixture: ComponentFixture<ContentFrequencyComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ContentFrequencyComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ContentFrequencyComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
