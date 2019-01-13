
import { Component, Input, OnInit, OnChanges, SimpleChanges, ViewChild, ElementRef, AfterViewInit, ViewEncapsulation, EventEmitter, Output, HostListener, NgZone } from '@angular/core';
import { LoaderService, App2Hosts, String2String, CompanyInfo, CompanyDB, APIAppInfo, GeoIPInfo } from '../loader.service';
import { AppUsage } from '../usagetable/usagetable.component';
import * as d3 from 'd3';
import * as _ from 'lodash';
import * as topojson from 'topojson';
import { HostUtilsService } from 'app/host-utils.service';
import { FocusService } from 'app/focus.service';
import { HoverService, HoverTarget } from "app/hover.service";
import { Http, HttpModule, Headers, URLSearchParams } from '@angular/http';
import * as colorbrewer from 'colorbrewer';
import { Observable } from '../../../node_modules/rxjs/Observable';
import { AppImpact } from '../refinebar/refinebar.component';
import { Subscription } from '../../../node_modules/rxjs/Subscription';


interface AppImpactGeo {
  appid: string;
  impact: number;
  geo: GeoIPInfo
};

@Component({
  selector: 'app-geomap',
  templateUrl: './geomap.component.html',
  styleUrls: ['./geomap.component.scss'],
  encapsulation: ViewEncapsulation.None
})

export class GeomapComponent implements AfterViewInit, OnChanges {

  // still in use!
  companyid2info: CompanyDB;

    
  
  @Input() impactChanges : Observable<any>;
  private _impact_listener : Subscription;

  @Input('impacts') impacts_in: AppImpact[];
  private impacts: AppImpactGeo[];
  
  // these two will die
  @Input('appusage') usage: AppUsage[];
  // private usage: AppUsage[];

  private init: Promise<any>;
  lastMax = 0;
  _byTime = 'yes';
  normaliseImpacts = false;

  apps: string[]; // keeps app ordering between renders

  // @ViewChild('thing') svg: ElementRef; // this gets a direct el reference to the svg element
  // incoming attribute
  @Input() showModes = true;
  @Input() highlightApp: APIAppInfo;
  @Input() showLegend = false;
  @Input() showTypesLegend = true;
  @Input() showXAxis = true;

  @Input() scale = false;
  vbox = { width: 700, height: 1024 };
  highlightColour = '#FF066A';

  _companyHovering: CompanyInfo;
  _hoveringApp: string ;
  _ignoredApps: string[];

  constructor(private httpM: HttpModule, 
    private http: Http, 
    private el: ElementRef,
    private loader: LoaderService,
    private hostutils: HostUtilsService,
    private focus: FocusService,
    private hover: HoverService,
    private zone : NgZone) {

    this.init = Promise.all([
      this.loader.getCompanyInfo().then((ci) => this.companyid2info = ci),
    ]);
    hover.HoverChanged$.subscribe((target) => {
      // console.log('hover changed > ', target);
      if (target !== this._hoveringApp) {
        this._hoveringApp = target ? target as string : undefined;
        this.render()
      }
    
    });
    this._ignoredApps = new Array();

    focus.focusChanged$.subscribe((target) => {
      // console.log('hover changed > ', target);
      if (target !== this._ignoredApps) {
        this._ignoredApps = target ? target as string[] : [];
        this.render();
      }
    });
  }
  // getIoTData(): void {
	//   this.loader.getIoTData().then(bundle => {
  //     this.usage = bundle.usage;

  //     let minMax = bundle.impacts.reduce((acc, val) => {
  //       acc[0] = ( acc[0] === undefined || val.impact < acc[0] ) ? val.impact : acc[0]
  //       acc[1] = ( acc[1] === undefined || val.impact > acc[1] ) ? val.impact : acc[1]
  //       return acc;
  //     }, []);

  //     this.impacts = bundle.impacts.map(impact => ({impact: impact.impact/minMax[1], geo: impact, appid: impact.appid }))
  //     this.render()
  //   });
  // }
  // this gets called when this.usage_in changes
  ngOnChanges(changes: SimpleChanges): void {
    // subscribing to the changes impact
    let convert_in = () => {
      if (this.impacts_in) { 
        // let minMax = this.impacts_in.reduce((acc, val) => {
        //   acc[0] = ( acc[0] === undefined || val.impact < acc[0] ) ? val.impact : acc[0]
        //   acc[1] = ( acc[1] === undefined || val.impact > acc[1] ) ? val.impact : acc[1]
        //   return acc;
        // }, []);
        this.impacts = this.impacts_in.map(impact => ({impact: impact.impact, /* impact.impact/minMax[1],*/ geo: <any>impact, appid: impact.appid }))
        this.zone.run(() => this.render());
      }
    };

    if (this.impactChanges && this._impact_listener === undefined) {
      this._impact_listener = this.impactChanges.subscribe(target => {        
        // console.info('geomap : change notification coming in.');         
        convert_in();
      });      
    }
    // if (!this.usage_in) { return; }
    // this.init.then(() => {  convert_in();   });
  }
  
  ngAfterViewInit(): void { this.init.then(() => this.render()); }

  getSVGElement() {
    const nE: HTMLElement = this.el.nativeElement;
    return Array.from(nE.getElementsByTagName('svg'))[0];
  }

  private _getApp(appid: string): Promise<APIAppInfo> {
    return this.loader.getCachedAppInfo(appid) && Promise.resolve(this.loader.getCachedAppInfo(appid))
      || this.loader.getFullAppInfo(appid);
  }

  // compileImpacts(usage: AppUsage[]): Promise<AppImpactGeo[]> {
  //   // folds privacy impact in simply by doing a weighted sum over hosts
  //   // usage has to be in a standard unit: days, minutes
  //   // first, normalise usage

  //   const timebased = this.byTime === 'yes',
  //     total = _.reduce(usage, (tot, appusage): number => tot + (timebased ? appusage.mins : 1.0), 0),
  //     impacts = usage.map((u) => ({ ...u, impact: (timebased ? u.mins : 1.0) / (1.0 * (this.normaliseImpacts ? total : 1.0)) }));

  //   return Promise.all(impacts.map((usg): Promise<AppImpactGeo[]> => {

  //     return this._getApp(usg.appid).then(app => {
  //       const hosts = app.hosts, geos = app.host_locations;
  //       if (!hosts || !geos) { console.warn('No hosts found for app ', usg.appid); return []; }
  //       return geos.map(geo => ({
  //         appid: usg.appid,
  //         geo: geo,
  //         impact: usg.impact,
  //       }));
  //     });
  //   })).then((nested_impacts: AppImpactGeo[][]): AppImpactGeo[] => _.flatten(_.flatten(nested_impacts)));
  // }


  // accessors for .byTime 
  set byTime(val) {
    this.lastMax = 0;
    this._byTime = val;
    this.init.then(() => this.render());
  }
  get byTime() { return this._byTime; }

  render() {
    // console.log(':: render usage:', this.usage && this.usage.length);
    const svgel = this.getSVGElement();
    if (!svgel || !this.usage || !this.impacts) { return; }
    // console.log('refinebar render! getSVGElement > ', svgel);

    let rect = svgel.getBoundingClientRect(),
      width_svgel = Math.round(rect.width - 5),
      height_svgel = Math.round(rect.height - 5),
      svg = d3.select(svgel);

    if (!this.scale) {
      svg.attr('width', width_svgel)
        .attr('height', height_svgel);
    } else {
      svg.attr('viewBox', `0 0 ${this.vbox.width} ${this.vbox.height}`)
        .attr('virtualWidth', this.vbox.width)
        .attr('virtualHeight', this.vbox.height)
        .attr('preserveAspectRatio', 'none') //  "xMinYMin meet")
      width_svgel = this.vbox.width;
      height_svgel = this.vbox.height;
    }

    svg.selectAll('*').remove();

    const usage = this.usage.filter(obj => this._ignoredApps.indexOf(obj.appid) === -1 ),
      impacts = this.impacts.filter(obj => this._ignoredApps.indexOf(obj.appid) === -1 ),
      minmax = d3.extent(impacts.map( i => i.impact ));            

      // console.log(impacts);

    let apps = _.uniq(impacts.map((x) => x.appid));
    apps.sort();    
    // if (this.apps === undefined) {
    //   // sort apps
    //   apps.sort((a, b) => _.filter(usage, { appid: b })[0].mins - _.filter(usage, { appid: a })[0].mins);
    //   this.apps = apps;
    // } else {
    //   apps = this.apps;
    // }
    let margin = { top: 20, right: 20, bottom: -200, left: 40 },
      width = width_svgel - margin.left - margin.right, // +svg.attr('width') - margin.left - margin.right,
      height = height_svgel - margin.top - margin.bottom, // +svg.attr('height') - margin.top - margin.bottom,
      z = d3.scaleOrdinal(d3.schemeCategory20).domain(apps);

    if (width < 50 || height < 50) { return; }

    const projection = d3.geoMercator()
      .scale(width / 2 / Math.PI)
      .translate([width / 2, height / 2]),
      path = d3.geoPath().projection(projection);

    this.loader.getWorldMesh().then((mesh) => {
      svg.append('path').attr("d", path(topojson.mesh(mesh))).attr('opacity', 0.2).attr("stroke", '#000').attr("fill", "none");
    });

    // add circles to svg
    var datas = svg.selectAll("circle")
      .data(impacts);

    datas.enter()
      .append("circle")
      .attr("cx", (d) => {
        const lat = projection([d.geo.longitude, d.geo.latitude])[0];
        return lat;
      })
      .attr("cy", (d) => {
        const lon = projection([d.geo.longitude, d.geo.latitude])[1];
        return lon;
      })
      .attr('opacity', (d) => {
        let highApp = this.highlightApp || this._hoveringApp;
        if (highApp) {
          return d.appid === highApp ? 0.75 : 0.01;
        }
        return 0.8;
      }).attr("r", (d) => {
        // console.log('d impact ', d.impact, Math.floor(200*(d.impact / minmax[1])), minmax[1]);
        return Math.floor(80*d.impact / minmax[1]);
      }).attr("fill", (d) => z(d.appid))
      .on('mouseenter', (d) => this.hover.hoverChanged(undefined))
      .on('mouseleave', (d) => this.hover.hoverChanged(undefined));

      console.info('map ending render');
    // datas.enter().append('text')
    //   .attr('x', (d) => projection([d.geo.longitude, d.geo.latitude])[0] + 5)
    //   .attr('y', (d) => projection([d.geo.longitude, d.geo.latitude])[1] + 5)
    //   .attr('opacity', d => this._hoveringApp && d.appid === this._hoveringApp ? 1 : 0)
    //   .text((d) => d.geo.region_name || d.geo.country);

    const leading = 26;

    if (this.showLegend) {
      let g = svg.append('g').attr('transform', 'translate(' + margin.left + ',' + margin.top / 2 + ')');
      const legend = g.append('g')
        .attr('class', 'legend')
        .attr('transform', 'translate(0,0)')
        .selectAll('g')
        .data(apps.slice().reverse())
        .enter()
        .append('g')
        .attr('transform', function (d, i) { return 'translate(0,' + i * leading + ')'; })
        .on('mouseenter', (d) => this.hover.hoverChanged(undefined))
        .on('mouseout', (d) => this.hover.hoverChanged(undefined))
        // .on('click', (d) => {
        //  this.focus.focusChanged(this.loader.getCachedAppInfo(d));
        // })
        .attr('opacity', (d) => {
          let highApp = this.highlightApp || this._hoveringApp;
          if (highApp) {
            return d === highApp ? 1.0 : 0.2;
          }
          return 1.0;
        });

      console.log('maplegend ! ', legend);

      legend.append('rect')
        .attr('x', this.showTypesLegend ? width - 140 - 19 : width - 19)
        .attr('width', 19)
        .attr('height', 19)
        .attr('fill', z);

      legend.append('text')
        .attr('x', this.showTypesLegend ? width - 140 - 24 : width - 24)
        .attr('y', 9.5)
        .attr('dy', '0.32em')
        .text((d) => this.loader.getCachedAppInfo(d) && this.loader.getCachedAppInfo(d).storeinfo.title || d);
    }

  }
  @HostListener('window:resize')
  onResize() {
    // call our matchHeight function here
    this.render();
  }
  @HostListener('mouseenter')
  mouseEnter() {
    // this.actlog.log('mouseenter', 'geomap');
  }

  @HostListener('mouseleave')
  mouseLv() {
    // this.actlog.log('mouseleave', 'geomap');
  }

}
