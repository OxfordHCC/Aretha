import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ContentInferenceComponent } from './content-inference.component';

describe('ContentInferenceComponent', () => {
  let component: ContentInferenceComponent;
  let fixture: ComponentFixture<ContentInferenceComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ContentInferenceComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ContentInferenceComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
