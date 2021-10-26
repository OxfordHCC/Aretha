import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ContentD2Component } from './content-d2.component';

describe('ContentD2Component', () => {
  let component: ContentD2Component;
  let fixture: ComponentFixture<ContentD2Component>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ContentD2Component ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ContentD2Component);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
