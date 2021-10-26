import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ContentB4Component } from './content-b4.component';

describe('ContentB4Component', () => {
  let component: ContentB4Component;
  let fixture: ComponentFixture<ContentB4Component>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ContentB4Component ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ContentB4Component);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
