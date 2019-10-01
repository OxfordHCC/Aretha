import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ContentBreachComponent } from './content-breach.component';

describe('ContentBreachComponent', () => {
  let component: ContentBreachComponent;
  let fixture: ComponentFixture<ContentBreachComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ContentBreachComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ContentBreachComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
