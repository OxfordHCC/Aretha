import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ContentD4Component } from './content-d4.component';

describe('ContentD4Component', () => {
  let component: ContentD4Component;
  let fixture: ComponentFixture<ContentD4Component>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ContentD4Component ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ContentD4Component);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
