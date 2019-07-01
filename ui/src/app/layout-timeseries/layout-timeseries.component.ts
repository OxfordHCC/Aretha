import { Component, OnInit } from '@angular/core';
import { LoaderService, DeviceImpact, GeoData, Device, BucketedImpacts, ImpactSet } from "app/loader.service";
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
	impacts: BucketedImpacts; 
	geodata: GeoData[];
	devices : Device[];
	impactChanges: Observable<any>;
	_last_load_time: Date;
	private impactObservers: Observer<any>[] = [];
	deviceimpactchangesubscription: any;
   
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

		// console.info("SUBSCRIBING TO ASYNCDEVICEIMPACTHANGES");
		// (<any>window)._l = this.loader;
		// (<any>window)._g = this;
		
		const resubscribe = () => {
			this.deviceimpactchangesubscription = this.loader.asyncDeviceImpactChanges().subscribe({
				next(incoming: ImpactSet) {  
					console.info('asyncDeviceImpacts :: incoming ', incoming);
					try { 
						if (this_.impacts) {
							// let cur_min = Math.floor((new Date().getTime())/(60000));
							let cur_min = Object.keys(this_.impacts).map(x => +x).sort((x,y) => y - x)[0];
							if (!cur_min) { 
								// cur_min = Math.floor((new Date().getTime())/(60000));
							}

							for (const dst of Object.keys(incoming)) {
								for (const mac of Object.keys(incoming[dst])) {

									const bucket = this_.impacts[cur_min] || {},
										val = incoming[dst][mac];

									bucket[mac] = bucket[mac] || {};
									
									// BEGIN DEBUG ==>
									if (bucket[mac][dst]) { 
										console.info("IMPUD: incr ", mac, "//", dst, " :: ", bucket[mac][dst], " + ",val," => ", (bucket[mac][dst]+val));
									} else {
										console.info("IMPUD: add dest ", mac, "//", dst, " :: ", val);									
									}
									// <== END DEBUG
									
									bucket[mac][dst] = (bucket[mac][dst] || 0) + val;
									this_.impacts[""+cur_min] = bucket;

									// original broken code >> 
									// const rows = this_.impacts.filter((x) => x.company === key);
									// if (rows.length === 0) {
									// 	this_.impacts.push({
									// 		"company": key,
									// 		"device": key2,
									// 		"impact": incoming[key][key2],
									// 		"minute": Math.floor((new Date().getTime()/1000) + 3600)
									// 	});
									// } else {
									// 	rows[0].impact += incoming[key][key2];
									// }
								}
							}
							console.info("updated impacts[",cur_min,"] -> ", this_.impacts);
							this_.triggerImpactsChange();
						}
					} catch(error) { 
						console.error("Error while woring on deviceimpactchange", error);
					}
				},
				error(err) { 
					console.error("Listen error! ", err, err.message); 
					// then attempt to re-subscribe because we'll now be closed! 
					setTimeout(resubscribe, 1000);
				},
				complete() { console.info("Listen complete"); }
			});
		};

		resubscribe();

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
		this.getIoTData(now - 5*60, now, 1);
		
		// seconds since the epoch
	}
}

