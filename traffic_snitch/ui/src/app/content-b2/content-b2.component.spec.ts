import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ContentB2Component } from './content-b2.component';

describe('ContentB2Component', () => {
  let component: ContentB2Component;
  let fixture: ComponentFixture<ContentB2Component>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ContentB2Component ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ContentB2Component);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
