import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ContentB3Component } from './content-b3.component';

describe('ContentB3Component', () => {
  let component: ContentB3Component;
  let fixture: ComponentFixture<ContentB3Component>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ContentB3Component ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ContentB3Component);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
