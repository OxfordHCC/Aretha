import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ContentEncryptionComponent } from './content-encryption.component';

describe('ContentEncryptionComponent', () => {
  let component: ContentEncryptionComponent;
  let fixture: ComponentFixture<ContentEncryptionComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ContentEncryptionComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ContentEncryptionComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
