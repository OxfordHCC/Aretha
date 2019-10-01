import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs/BehaviorSubject';
import { ActivityLogService } from "app/activity-log.service";

export type HoverTarget = string;

@Injectable()
export class HoverService {
  private HoverChangedSource = new BehaviorSubject<HoverTarget>(undefined);  
  HoverChanged$ = this.HoverChangedSource.asObservable();
  
  constructor(private actlog : ActivityLogService) {
  }

  hoverChanged(target: HoverTarget) {
    this.actlog.log('hover-app', target || 'unhover');
    this.HoverChangedSource.next(target);
  }
  clearState() {
    this.hoverChanged(undefined);
  }
  getState(): HoverTarget { 
    return this.HoverChangedSource.getValue();
  }
}
