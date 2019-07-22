import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ContentD3Component } from './content-d3.component';

describe('ContentD3Component', () => {
  let component: ContentD3Component;
  let fixture: ComponentFixture<ContentD3Component>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ContentD3Component ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ContentD3Component);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
