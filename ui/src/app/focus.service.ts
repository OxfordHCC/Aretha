import { Injectable } from '@angular/core';
import { APIAppInfo, CompanyInfo } from 'app/loader.service';
import { BehaviorSubject } from 'rxjs/BehaviorSubject';
import { Subject } from 'rxjs/Subject';
import { ActivityLogService } from "app/activity-log.service";

export type FocusTarget = string[];

@Injectable()
export class FocusService {
  private focusChangedSource = new BehaviorSubject<FocusTarget>(undefined);  
  focusChanged$ = this.focusChangedSource.asObservable();
  
  constructor(private actlog : ActivityLogService) {}

  focusChanged(focusTarget: FocusTarget) {
    this.focusChangedSource.next(focusTarget);
  }

  clearState() {
    this.focusChanged(undefined);
  }
  
  getState(): FocusTarget { 
    return this.focusChangedSource.getValue();
  }
}
