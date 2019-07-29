import { Component, OnInit } from '@angular/core';
import { LoaderService, DeviceImpact, GeoData, Device, BucketedImpacts, ImpactSet, CompanyInfo } from "app/loader.service";
import { FocusService } from "app/focus.service";
import { Observable } from 'rxjs';
import * as d3 from 'd3'; 
import { Observer } from 'rxjs';
import * as _ from 'lodash';
import { ActivatedRoute} from "@angular/router";

export class TimeSelection {
	centre: Date;
	start: Date;
	end: Date;
};

@Component({
  selector: 'app-layout-timeseries',
  templateUrl: './layout-timeseries.component.html',
  styleUrls: ['./layout-timeseries.component.scss']
})

export class LayoutTimeseriesComponent implements OnInit {
  mode: string;
  	zoomed_impacts: BucketedImpacts; 	
	impacts: BucketedImpacts; 
	geodata: GeoData[];
	devices : Device[];
	impactChanges: Observable<any>;
	_last_load_time: Date;
	private impactObservers: Observer<any>[] = [];
	deviceimpactchangesubscription: any;
	lastTimeSelection: TimeSelection;
	showCompanyInfo: CompanyInfo;

	// Dayspan for overview
	overviewSpanDays = 2;

	// end date parging
	endDate = new Date(); // 
	endDateStr: string;
	startDateStr: string;
	endDateToday: boolean;
   
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
		(<any>window)._d3 = d3;
		this.setEndDateOffset(0);
  	}  

  // handling propagating
  _make_impact_observable(): Observable<any> {
    return Observable.create( observer => {
      this.impactObservers.push(observer);
    });    
  }
  triggerImpactsChange(): any {
	this.impactObservers.map(obs => obs.next({}));
	if (this.lastTimeSelection) { this.timeSelected(this.lastTimeSelection); }
  }  
  

	getIoTData(start: Date, end: Date, delta: number): void {	
		console.info('getIoTData ((', start, '::', start, ' - ', end, '::', end, ' delta ', delta, '))');
    	let this_ = this,
      		reload = () => {
				const new_end = new Date(); // Math.floor((new Date()).valueOf()/1000.0);
				console.info('time:: reload() ');
				this_.loader.getIoTData(start, new_end, delta).then( bundle => {
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
								cur_min = Math.floor((new Date().getTime())/(60000));
							}

							for (const dst of Object.keys(incoming)) {
								for (const mac of Object.keys(incoming[dst])) {

									const bucket = this_.impacts[cur_min] || {},
										val = incoming[dst][mac];

									bucket[mac] = bucket[mac] || {};
									
									bucket[mac][dst] = (bucket[mac][dst] || 0) + val;
									this_.impacts[""+cur_min] = bucket;
								}
							}
							// console.info("updated impacts[",cur_min,"] -> ", this_.impacts);
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
    	}, 3*1000); // @TODO this should be set to a much larger value once we get bucket diffs streaming in
		
		reload();
	  }  

	  dateToMinutes(input:Date): number {
		  return Math.floor(input.getTime()/(1000*60));
	  }	  

	timeSelected(val: TimeSelection) {
		// this can be called with an undefined argument
		//   console.log("Got time selection", val.start, " -> ", val.end);
		  // now we want to filter our impacts and update local impacts
		  if (this.impacts) { 
			const st_mins = this.dateToMinutes(val.start),st_end = this.dateToMinutes(val.end);
			this.zoomed_impacts = _.pickBy(this.impacts, (macip, time) => +time >= st_mins && +time <= st_end);
		  }
		  this.lastTimeSelection = val;
	  }

	// on init reload
	ngOnInit() {
		this.getIoTData(new Date(new Date().getTime()-24*60*60000), new Date(), 1);
	}

	closeCompanyInfo() { 
		this.showCompanyInfo = undefined;
	}

	selectCompany(c:string) { 
		console.info('company selected ', c);
		this.showCompanyInfo = new CompanyInfo(c, c, [], 'footags');
	}

	selectDevice(d:string) { 
		console.info('device selected', d);
	}

	getStartDate():Date {
		return d3.timeDay.offset(this.endDate, -3);
	}

	dateMin(d1:Date, d2:Date):Date {
		return d1.getDate().valueOf() < d2.getDate().valueOf() ? d1 : d2;
	}
	
	isToday(d:Date):boolean {
		const today = new Date();
		return today.toDateString() === d.toDateString()
	}

	suffixToday(d: Date): string {
	 	return this.isToday(d) ? `${d.toDateString()} (Today)` : d.toDateString();
	}

	setEndDateOffset(days : number): Date {
		const now = new Date();
		this.endDate = d3.timeSecond.offset(d3.timeDay.ceil(this.dateMin(now, d3.timeDay.offset(this.endDate, days))), -1);
		this.endDateStr = this.suffixToday(this.endDate);
		this.startDateStr = this.suffixToday(this.getStartDate());
		this.endDateToday = this.isToday(this.endDate);
		return this.endDate;
	}

}

