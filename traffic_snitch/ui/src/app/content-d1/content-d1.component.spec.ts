import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ContentD1Component } from './content-d1.component';

describe('ContentD1Component', () => {
  let component: ContentD1Component;
  let fixture: ComponentFixture<ContentD1Component>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ContentD1Component ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ContentD1Component);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
