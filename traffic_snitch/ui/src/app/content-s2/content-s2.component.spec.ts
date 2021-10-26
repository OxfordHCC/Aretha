import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ContentS2Component } from './content-s2.component';

describe('ContentS2Component', () => {
  let component: ContentS2Component;
  let fixture: ComponentFixture<ContentS2Component>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ContentS2Component ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ContentS2Component);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
