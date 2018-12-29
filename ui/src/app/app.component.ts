import { Component } from '@angular/core';
import { Router, NavigationEnd } from "@angular/router";
import { ActivityLogService } from "app/activity-log.service";
import { LoaderService } from './loader.service';

(<any>window)._listen_count = 0;

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  title = 'app';
  
  constructor(private router: Router, private actlog: ActivityLogService, private loader: LoaderService) {
    this.router.events.subscribe(routeEvent => {
      // console.info('routeEvent ', routeEvent);
      if (routeEvent instanceof NavigationEnd) {
        console.log("nav end");
        try { this.actlog.log('routeChange', routeEvent.url); } catch(e) { }
      }      
    });

    // startup loader listener
    this.loader.connectToAsyncDBUpdates();

    // let updates = this.loader.listenToUpdates().subscribe({
    //   next(x) {  
    //     // console.log("Listen next! ", x); 
    //     (<any>window)._listen_count++
    //   },
    //   error(err) {
    //     console.log("Listen error! ", err, err.message);
    //   },
    //   complete() { 
    //     console.log("Listen complete"); 
    //   }
    // });
  }

  // isActive(instruction: any[]): boolean {
  //   console.log('create tree > ', instruction, this.router.createUrlTree(instruction), "active? ", this.router.isActive(this.router.createUrlTree(instruction), true));
  //   console.log('create tree document location ', document.location.href);
  //   return this.router.isActive(this.router.createUrlTree(instruction), true);
  // }

  isActive(s: string): boolean {    
    return document.location.href.endsWith(s);
  }



}
