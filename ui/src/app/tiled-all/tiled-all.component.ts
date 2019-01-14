import { Component, OnInit } from '@angular/core';
import { CompanyInfo, APIAppInfo, LoaderService } from "app/loader.service";
import { FocusTarget, FocusService } from "app/focus.service";
import { UsageListener } from "app/usage-listener/usage-listener.component";
import { UsageConnectorService } from "app/usage-connector.service";
import { ActivatedRoute, Router } from "@angular/router";
import { AppImpact } from '../refinebar/refinebar.component';
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
      /*
      if ((<APIAppInfo>target).app !== undefined) { 
        this.targettype = 'app'; 
        return; 
      }
      if ((<CompanyInfo>target).company !== undefined) { 
        this.targettype = 'company'; 
        return; 
      }  */
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
  impacts: AppImpact[];
  usage : AppUsage[];
  impactChanges: Observable<any>;
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
      this_.loader.getIoTData().then( bundle => {
        // console.log('!@#ILJ!@#L@!J# got bundle ', bundle);
        this_.usage = bundle.usage;
        this_.impacts = bundle.impacts;
        console.log("yooo assigning impacts ", this_.impacts);
        this_.triggerImpactsChange();
        // this_.render();
      });
    }, 
    throttledReload = _.throttle(reload, 1000);

    this.loader.asyncAppImpactChanges().subscribe({
      next(i: AppImpact[]) {  
        console.log('AppImpact CHANGE!', i.map(x => ''+[x.companyName, x.companyid, ''+x.impact].join('_')).join(' - '))
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
    reload();
  }  

  ngOnInit() {
    this.getIoTData();
  }
}
