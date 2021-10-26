import { TestBed, inject, async } from '@angular/core/testing';
import { HttpModule } from '@angular/http';
import { LoaderService } from './loader.service';
import { AppComponent } from './app.component';

describe('LoaderService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpModule],
      providers: [LoaderService]
    });
  });

  it('should be created', inject([LoaderService], (service: LoaderService) => {
    expect(service).toBeTruthy();
  }));

});
