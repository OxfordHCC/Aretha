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
    	let this_ = this,
      		reload = () => {
				this_.loader.getIoTData(start, end, delta).then( bundle => {
					this_.impacts = bundle.impacts;
        			this_.geodata = bundle.geodata;
        			this_.devices = bundle.devices;
        			this_.triggerImpactsChange();
        			this_._last_load_time = new Date();
      			});
    		}, 
    		throttledReload = _.throttle(reload, 10000);

    	this.loader.asyncDeviceImpactChanges().subscribe({
      		next(i: DeviceImpact[]) {  
				if (this_.impacts) {
					for (let key in i) {
						for (let key2 in i[key]) {
							if (this_.impacts.filter ((x) => x.company === key).length === 0) {
								this_.impacts.push({
									"company": key,
									"device": key2,
									"impact": i[key][key2],
									"minute": Math.floor((new Date().getTime()/1000) + 3600)
								});
							} else {
								this_.impacts.filter ((x) => x.company === key)[0].impact += i[key][key2];
							}
						}
					}
          			this_.triggerImpactsChange();
        		}
      		},
      		error(err) { console.log("Listen error! ", err, err.message); },
      		complete() { console.log("Listen complete"); }
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
