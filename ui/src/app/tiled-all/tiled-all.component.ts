import { Component, OnInit } from '@angular/core';
import { CompanyInfo, APIAppInfo, LoaderService, DeviceImpact, GeoData, Device } from "app/loader.service";
import { FocusTarget, FocusService } from "app/focus.service";
import { UsageListener } from "app/usage-listener/usage-listener.component";
import { UsageConnectorService } from "app/usage-connector.service";
import { ActivatedRoute, Router } from "@angular/router";
import * as _ from 'lodash';
import { Observable } from '../../../node_modules/rxjs/Observable';
import { Observer } from '../../../node_modules/rxjs/Observer';
import { AppUsage } from '../usagetable/usagetable.component';


// target watcher watches for clicks on apps and companies
export class TargetWatcher extends UsageListener {
 
  target : FocusTarget;
  targettype : string;

  constructor(private focus: FocusService, connector: UsageConnectorService) {     
    super(connector);
    this.focus.focusChanged$.subscribe((target: FocusTarget) => { 
      
      if (!target) { 
        delete this.target;
        delete this.targettype;
        return;
      }
      this.target = target; 
      delete this.targettype;
    });
  }

}

@Component({
  selector: 'app-tiled-all',
  templateUrl: './tiled-all.component.html',
  styleUrls: ['./tiled-all.component.scss']
})

export class TiledAllComponent extends TargetWatcher implements OnInit {

	showUsageTable = false;
	mode: string;
	impacts: DeviceImpact[];
	geodata: GeoData[];
	devices : Device[];
	impactChanges: Observable<any>;
	_last_load_time: Date;
	private impactObservers: Observer<any>[] = [];
   
	constructor(focus: FocusService, connector: UsageConnectorService, private route: ActivatedRoute, private loader: LoaderService) {
    	super(focus, connector);
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

	// todo; move this out to loader
	getIoTData(): void {	
    	let this_ = this,
      		reload = () => {
				this_.loader.getIoTDataAggregated().then( bundle => {
					this_.impacts = bundle.impacts;
        			this_.geodata = bundle.geodata;
        			this_.devices = bundle.devices;
        			this_.triggerImpactsChange();
        			this_._last_load_time = new Date();
      			});
    		}, 
    		throttledReload = _.throttle(reload, 1000);

    	this.loader.asyncDeviceImpactChanges().subscribe({
      		next(i: DeviceImpact[]) {  
        		// console.log('DeviceImpact CHANGE!', i.map(x => ''+[x.companyName, x.companyid, ''+x.impact].join('_')).join(' - '))
        		if (this_.impacts) { 
        			this_.impacts = this_.impacts.concat(i);
          			this_.triggerImpactsChange();
        		}
      		},
      		error(err) { console.log("Listen error! ", err, err.message); },
      		complete() { console.log("Listen complete"); }
    	});

    	this.loader.asyncGeoUpdateChanges().subscribe({
      		next(a: any[]) {
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
    this.getIoTData();
  }
}
