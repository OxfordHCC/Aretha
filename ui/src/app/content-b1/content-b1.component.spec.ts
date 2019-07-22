import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ContentB1Component } from './content-b1.component';

describe('ContentB1Component', () => {
  let component: ContentB1Component;
  let fixture: ComponentFixture<ContentB1Component>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ContentB1Component ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ContentB1Component);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
