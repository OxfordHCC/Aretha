import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ContentS3Component } from './content-s3.component';

describe('ContentS3Component', () => {
  let component: ContentS3Component;
  let fixture: ComponentFixture<ContentS3Component>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ContentS3Component ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ContentS3Component);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
