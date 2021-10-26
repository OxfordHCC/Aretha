import { TestBed } from '@angular/core/testing';

import { CompanyInfoService } from './company-info.service';

describe('CompanyInfoService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: CompanyInfoService = TestBed.get(CompanyInfoService);
    expect(service).toBeTruthy();
  });
});
