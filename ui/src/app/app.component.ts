import { Component, OnInit } from '@angular/core';
import { Router, NavigationEnd } from "@angular/router";
import { ActivityLogService } from "app/activity-log.service";
import { LoaderService } from './loader.service';

(<any>window)._listen_count = 0;

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})

export class AppComponent implements OnInit {
  	title = 'app';
	content = 0;

	constructor(private router: Router, private actlog: ActivityLogService, private loader: LoaderService) {
    	this.router.events.subscribe(routeEvent => {
      		if (routeEvent instanceof NavigationEnd) {
        		console.log("nav end");
        		try { this.actlog.log('routeChange', routeEvent.url); } catch(e) { }
      		}      
    	});
    
    	// startup loader listener
    	this.loader.connectToAsyncDBUpdates();

		this.loader.contentChanged.subscribe((x) => this.content -= 1);
  	}
  
	isActive(s: string): boolean {    
    	return document.location.href.endsWith(s);
	}

	ngOnInit() {
		this.loader.getContent().then((cn) => {
			this.content = cn.length;
		});
	}

}
