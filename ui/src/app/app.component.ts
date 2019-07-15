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
				let re = /\//;
				let route = routeEvent.url.replace(re, "");
				if (route === "") { route = "root"; }
        		try { this.actlog.log('routeChange', route); } catch(e) { }
      		}      
    	});
    
    	// startup loader listener
    	this.loader.connectToAsyncDBUpdates();

		this.loader.contentChanged.subscribe(() => this.content -= 1);
  	}

  	ngOnInit() {
		this.loader.getContent().then((cn) => {
      this.content = cn.length;
		});

		let this_ = this;
		setInterval(function() {
			console.log("app.component refreshing live content");
			this_.loader.getContent().then((cn) => {
				this_.content = cn.length;
			});
		}, 1000*60*15, this);
	}

}
