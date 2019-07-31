import { Component, OnInit } from '@angular/core';
import { LoaderService, DeviceImpact, GeoData, Device, BucketedImpacts, ImpactSet, CompanyInfo } from "app/loader.service";
import { FocusService } from "app/focus.service";
import { Observable } from 'rxjs';
import * as d3 from 'd3'; 
import { Observer } from 'rxjs';
import * as _ from 'lodash';
import { ActivatedRoute} from "@angular/router";
import { dateMin } from '../utils';

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
	throttledReload: any;
	isLoading = false;
	companydb: any;
   
	constructor(focus: FocusService, private route: ActivatedRoute, private loader: LoaderService) {
    	this.impactChanges = this._makeImpactObservable();
		this._last_load_time = new Date();
		// initialise date pager 
		this.setEndDateOffset(0);

		// debug
		(<any>window)._d3 = d3;
		// debug		
  	}  

	// handling propagating
	_makeImpactObservable(): Observable<any> {
		return Observable.create(observer => { this.impactObservers.push(observer); return; });
	}
	_notifyImpactObservers(): any {
		this.impactObservers.map(obs => obs.next({}));
		if (this.lastTimeSelection) { this.timeSelected(this.lastTimeSelection); }
	}

	// reload ==================	
	
	reload():void {
		const start = this.getStartDate(),
			end = this.isToday(this.endDate) ? new Date() : this.endDate;
		
		console.info(`reload asking for ${start}-${end}`);
		this.isLoading = true;
		
		this.loader.getIoTData(start, end, 1).then( bundle => {
			this.isLoading = false;
			console.info('time:: assigning impacts ', bundle.impacts);
			this.impacts = bundle.impacts;
			this.geodata = bundle.geodata;
			this.devices = bundle.devices;
			this._notifyImpactObservers();
			this._last_load_time = new Date();
		}).catch(e => {
			console.error("ERROR with getIoTData ", e);
			this.isLoading = false;
		});
	}	


	// getIoTData(start: Date, end: Date, delta: number): void {	
	// 	console.info('getIoTData ((', start, '::', start, ' - ', end, '::', end, ' delta ', delta, '))');
	// 	let this_ = this,
	// 	reload = () => {
	// 		const new_end = new Date(); // Math.floor((new Date()).valueOf()/1000.0);
	// 		console.info('time:: reload() ');
	// 		this_.loader.getIoTData(start, new_end, delta).then( bundle => {
	// 			console.info('time:: assigning impacts ', bundle.impacts);
	// 			this_.impacts = bundle.impacts;
	// 			this_.geodata = bundle.geodata;
	// 			this_.devices = bundle.devices;
	// 			this_._notifyImpactObservers();
// 			this_._last_load_time = new Date();
	// 		});
	// 	};		
	// }  

	dateToMinutes(input:Date): number {
		return Math.floor(input.getTime()/(1000*60));
	}	  

	// this updates zoomed_impacts 
	timeSelected(val: TimeSelection) {
		// this can be called with an undefined argument
		// now we want to filter our impacts and update local impacts
		if (this.impacts) { 
			// const st_mins = this.dateToMinutes(val.start),st_end = this.dateToMinutes(val.end);

			// this.zoomed_impacts = _.pickBy(this.impacts, (macip, time) => +time >= st_mins && +time <= st_end);
			this.zoomed_impacts = _.fromPairs(d3.timeMinute.range(val.start, val.end).map((min_date) =>  {
				const min = this.dateToMinutes(min_date);
				return [+min, this.impacts[+min] || {}];
			}));

			// ----
			// console.log('hi');			
		}
		this.lastTimeSelection = val;
	}

	_subscribe_device_impacts():void {
		// eventstream listener 
		this.deviceimpactchangesubscription = this.loader.asyncDeviceImpactChanges().subscribe({
			next(incoming: ImpactSet) {  
				console.info('asyncDeviceImpacts :: incoming ', incoming);
				try { 
					if (this.impacts) {
						// let cur_min = Math.floor((new Date().getTime())/(60000));
						let cur_min = Object.keys(this.impacts).map(x => +x).sort((x,y) => y - x)[0];
						
						if (!cur_min) { 
							cur_min = Math.floor((new Date().getTime())/(60000));
						}
						
						for (const dst of Object.keys(incoming)) {
							for (const mac of Object.keys(incoming[dst])) {
								
								const bucket = this.impacts[cur_min] || {},
								val = incoming[dst][mac];
								
								bucket[mac] = bucket[mac] || {};								
								bucket[mac][dst] = (bucket[mac][dst] || 0) + val;
								this.impacts[""+cur_min] = bucket;
							}
						}
						// console.info("updated impacts[",cur_min,"] -> ", this_.impacts);
						this._notifyImpactObservers();
					}
				} catch(error) { 
					console.error("Error while woring on deviceimpactchange", error);
				}
			},
			error(err) { 
				console.error("Listen error! ", err, err.message); 
				// then attempt to re-subscribe because we'll now be closed! 
				setTimeout(() => this._subscribe_device_impacts(), 1000);
			},
			complete() { console.info("Listen complete"); }
		});
	}

	// on init reload
	async ngOnInit() {
		const throttledReload = _.throttle(() => this.reload(), 10000);
		this.throttledReload = throttledReload;
		this._subscribe_device_impacts();
		this.loader.asyncGeoUpdateChanges().subscribe({
			next() {
				console.info(" ~ got GEO UPDATE, NOW FLUSHING AND STARTING OVER");        
				if (this.impacts) { throttledReload(); }        
			}
		});  
		
		// watchdog interval forces reload every minute to get new updated impacts
		// this should only happen when viewed interval is current
		setInterval(() => {
			let msec_since_reload = (new Date()).valueOf() - this._last_load_time.valueOf();
			// console.info('WATCHDOG checking ~~~~ ', msec_since_reload, ' msec since last reload');
			if (msec_since_reload > 1000*60) {
				console.info('WATCHDOG forcing reload of impacts ~~~~ ', msec_since_reload, 'since last reload');
				throttledReload();
			}
		}, 60*1000); // @TODO this should be set to a much larger value once we get bucket diffs streaming in
		throttledReload();

		this.companydb = await this.loader.getCompanyInfo();
		(<any>window)._cdb = this.companydb;
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
		return d3.timeDay.floor(d3.timeDay.offset(this.endDate, -this.overviewSpanDays));
	}
	isToday(d:Date):boolean {
		const today = new Date();
		return today.toDateString() === d.toDateString()
	}
	suffixToday(d: Date): string {
	 	return this.isToday(d) ? `${d.toDateString()} (Today)` : d.toDateString();
	}
	setEndDateOffset(days : number): Date {
		// console.log(`setEndDateOffset called ${days} on ${this.endDate}`);
		const floornow = d3.timeDay.floor(new Date()),
			floordate = d3.timeDay.floor(d3.timeDay.offset(this.endDate, days)),
			minDate = dateMin(floornow, floordate);

		this.endDate = d3.timeSecond.offset(d3.timeDay.ceil(d3.timeSecond.offset(minDate, 1)), -1);
		// console.info('new endDate ', this.endDate);
		this.endDateStr = this.suffixToday(this.endDate);
		this.startDateStr = this.suffixToday(this.getStartDate());
		this.endDateToday = this.isToday(this.endDate);
		if (this.throttledReload) { this.reload(); }
		return this.endDate;
	}

}

