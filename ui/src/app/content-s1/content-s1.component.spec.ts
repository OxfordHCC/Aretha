import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ContentS1Component } from './content-s1.component';

describe('ContentS1Component', () => {
  let component: ContentS1Component;
  let fixture: ComponentFixture<ContentS1Component>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ContentS1Component ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ContentS1Component);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
