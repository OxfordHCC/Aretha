import { Component, OnInit } from '@angular/core';
import { LoaderService, DeviceImpact, GeoData, Device, ImpactSet } from "app/loader.service";
import { FocusService } from "app/focus.service";
import { ActivatedRoute} from "@angular/router";
import * as _ from 'lodash';
import { Observable } from 'rxjs';
import { Observer } from 'rxjs';

@Component({
  selector: 'app-tiled-all',
  templateUrl: './tiled-all.component.html',
  styleUrls: ['./tiled-all.component.scss']
})

export class TiledAllComponent implements OnInit {
  mode: string;
	impacts: any;
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

	getIoTData(start: number, end: number): void {	
    	let this_ = this,
      		reload = () => {
				this_.loader.getIoTDataAggregated(start, end).then( bundle => {
					this_.impacts = bundle.impacts;
        			this_.geodata = bundle.geodata;
        			this_.devices = bundle.devices;
        			this_.triggerImpactsChange();
        			this_._last_load_time = new Date();
      			});
    		}, 
    		throttledReload = _.throttle(reload, 10000);

    	this.loader.asyncDeviceImpactChanges().subscribe({
      		next(incoming: ImpactSet) {  
				if (this_.impacts) {
					console.log("incoming!");
					try {
						console.log(this_.impacts);
						for (var key in incoming) {
							for (var key2 in incoming[key]) {
								if (this_.impacts.filter ((x) => x.company === key && x.device === key2).length === 0) {
									this_.impacts.push({
										"company": key,
										"device": key2,
										"impact": incoming[key][key2]
									});
								} else {
									for (var key3 in this_.impacts) {
										if (this_.impacts[key3].company === key && this_.impacts[key3].device === key2) {
											this_.impacts[key3].impact += incoming[key][key2];
											break;
										}
									}
								}
							}
						}
					} catch(e) { console.error(e); }
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
		let now = Math.floor(new Date().getTime()/1000); // seconds since the epoch
		// this.getIoTData(now - 3600, now); // 
		this.getIoTData(0, now);
	}
}
