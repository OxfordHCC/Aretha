import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ContentSd1Component } from './content-sd1.component';

describe('ContentSd1Component', () => {
  let component: ContentSd1Component;
  let fixture: ComponentFixture<ContentSd1Component>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ContentSd1Component ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ContentSd1Component);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
