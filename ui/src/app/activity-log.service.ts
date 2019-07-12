import { Injectable } from '@angular/core';
import {LoaderService} from "./loader.service";

@Injectable()
export class ActivityLogService {

  pid : string;

  constructor(private loader: LoaderService) {
    this.loader.getPid().then((pid) => this.pid = pid['pid']);
  }

  log(type : string, action: string) {
    let time = new Date();
    console.log("ACTLOG", this.pid, time, type + ': ' + action);
    this.loader.setAct(this.pid, type, action);
  }
}
