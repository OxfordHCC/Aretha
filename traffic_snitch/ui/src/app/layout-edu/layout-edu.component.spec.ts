import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { LayoutEduComponent } from './layout-edu.component';

describe('LayoutEduComponent', () => {
  let component: LayoutEduComponent;
  let fixture: ComponentFixture<LayoutEduComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ LayoutEduComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(LayoutEduComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
