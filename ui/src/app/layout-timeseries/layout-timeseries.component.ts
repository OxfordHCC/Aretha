import { Component, OnInit } from '@angular/core';
import { LoaderService, DeviceImpact, GeoData, Device } from "app/loader.service";
import { FocusService } from "app/focus.service";
import { Observable } from 'rxjs';
import { Observer } from 'rxjs';
import * as _ from 'lodash';
import { ActivatedRoute} from "@angular/router";

@Component({
  selector: 'app-layout-timeseries',
  templateUrl: './layout-timeseries.component.html',
  styleUrls: ['./layout-timeseries.component.css']
})

export class LayoutTimeseriesComponent implements OnInit {
  mode: string;
	impacts: DeviceImpact[];
	geodata: GeoData[];
	devices : Device[];
	impactChanges: Observable<any>;
	_last_load_time: Date;
	private impactObservers: Observer<any>[] = [];
   
	constructor(focus: FocusService, private route: ActivatedRoute, private loader: LoaderService) {
    	this.route.params.subscribe(params => { 
      		console.log("SETTING MODE", params.mode);
      		this.mode = params.mode; 
    	});
    	this.route.queryParams.subscribe(params => { 
      		console.log("SETTING QUERY PARAMS MODE", params.mode);
      		this.mode = params.mode; 
    	});
    	this.impactChanges = this._make_impact_observable();
        this._last_load_time = new Date();
  	}  

  // handling propagating
  _make_impact_observable(): Observable<any> {
    return Observable.create( observer => {
      this.impactObservers.push(observer);
    });    
  }
  triggerImpactsChange(): any {
    this.impactObservers.map(obs => obs.next({}));
  }  

	getIoTData(start: number, end: number, delta: number): void {	
		console.info('getIoTData ((', start, '::', new Date(start*1000), ' - ', end, '::', new Date(end*1000), ' delta ', delta, '))');
    	let this_ = this,
      		reload = () => {
				console.info('time:: reload() ');
				this_.loader.getIoTData(start, end, delta).then( bundle => {
					console.info('time:: assigning impacts ', bundle.impacts);
					this_.impacts = bundle.impacts;
        			this_.geodata = bundle.geodata;
        			this_.devices = bundle.devices;
        			this_.triggerImpactsChange();
        			this_._last_load_time = new Date();
      			});
    		}, 
    		throttledReload = _.throttle(reload, 10000);

		console.info("SUBSCRIBING TO ASYNCDEVICEIMPACTHANGES");
		(<any>window)._l = this.loader;
		(<any>window)._g = this;
    	this.loader.asyncDeviceImpactChanges().subscribe({
      		next(i: DeviceImpact[]) {  
				console.info('asyncDeviceImpacts :: incoming ', i);
				if (this_.impacts) {
					for (const key of Object.keys(i)) {
						for (const key2 of Object.keys(i[key])) {
							const rows = this_.impacts.filter((x) => x.company === key);
							if (rows.length === 0) {
								this_.impacts.push({
									"company": key,
									"device": key2,
									"impact": i[key][key2],
									"minute": Math.floor((new Date().getTime()/1000) + 3600)
								});
							} else {
								rows[0].impact += i[key][key2];
							}
						}
					}
          			this_.triggerImpactsChange();
        		}
      		},
      		error(err) { console.error("Listen error! ", err, err.message); },
      		complete() { console.info("Listen complete"); }
    	});

    	this.loader.asyncGeoUpdateChanges().subscribe({
      		next() {
        		console.info(" ~ got GEO UPDATE, NOW FLUSHING AND STARTING OVER");        
        		if (this_.impacts) { throttledReload(); }        
      		}
    	});  

    	setInterval(() => {
      		let msec_since_reload = (new Date()).valueOf() - this_._last_load_time.valueOf();
      		console.info('WATCHDOG checking ~~~~ ', msec_since_reload, ' msec since last reload');
      		if (msec_since_reload > 1000*60) {
        		console.info('WATCHDOG forcing reload of impacts ~~~~ ', msec_since_reload, 'since last reload');
        		reload();
      		}
    	}, 10*1000); 
		
		reload();
  	}  

	ngOnInit() {
		let now = Math.floor(new Date().getTime()/1000);
    	this.getIoTData(now - 3600, now, 1);
	}
}

