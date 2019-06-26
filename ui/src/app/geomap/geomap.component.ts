
import { Component, Input, OnChanges, SimpleChanges, ElementRef, AfterViewInit, ViewEncapsulation, HostListener, NgZone } from '@angular/core';
import { LoaderService, CompanyInfo, CompanyDB, APIAppInfo, GeoData, DeviceImpact } from '../loader.service';
import * as d3 from 'd3';
import * as _ from 'lodash';
import * as topojson from 'topojson';
import { HostUtilsService } from 'app/host-utils.service';
import { FocusService } from 'app/focus.service';
import { HoverService} from "app/hover.service";
import { Http, HttpModule} from '@angular/http';
import { Observable } from '../../../node_modules/rxjs/Observable';
import { Subscription } from '../../../node_modules/rxjs/Subscription';

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

	@Input() impacts: DeviceImpact[];
	@Input() geodata: GeoData[];
  
  	private init: Promise<any>;
  	lastMax = 0;
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
      		if (target !== this._hoveringApp) {
		  		this._hoveringApp = target ? target as string : undefined;
		  		console.log("hoverchange", this._hoveringApp);
        		this.render()
      		}
    
    	});
		
		this._ignoredApps = new Array();

    	focus.focusChanged$.subscribe((target) => {
      		if (target !== this._ignoredApps) {
        		this._ignoredApps = target ? target as string[] : [];
        		this.render();
      		}
		});
	}
	
	ngOnChanges(changes: SimpleChanges): void {
    	var this_ = this;
		if (this.impactChanges && this._impact_listener === undefined) {
			this._impact_listener = this.impactChanges.subscribe(target => {        
				this.zone.run(() => this_.render());
			});
			if (this.impacts) {
				this_.render();
			}
		}
		this.init.then(() => { this.render(); });
	}
  
	ngAfterViewInit(): void { this.init.then(() => this.render()); }

  	getSVGElement() {
    	const nE: HTMLElement = this.el.nativeElement;
    	return Array.from(nE.getElementsByTagName('svg'))[0];
  	}

	//combines impacts, geodata, and devices into impacts per device per location
	private compileImpacts(): any {
		var result = [];
		if (this.impacts) {
			this.impacts.filter(obj => this._ignoredApps.indexOf(obj.device) === -1 ).map((imp) => {
				if (this.geodata.filter((x) => x.ip === imp.company).length > 0) {
					result.push({
						"ip": imp.company,
						"device": imp.device,
						"impact": Math.log(imp.impact),
						"lat": this.geodata.filter((geo) => geo.ip === imp.company)[0].latitude,
						"lon": this.geodata.filter((geo) => geo.ip === imp.company)[0].longitude
					});
				}
			});
		}
		return result;
	}

	render() {
		const svgel = this.getSVGElement();
    	if (!svgel)  { return; }

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

      	const impacts = this.compileImpacts(), 
      		minmax = d3.extent(impacts.map( i => i.impact ));            

		let devices = _.uniq(impacts.map((x) => x.device));
		devices.sort();    

    	let margin = { top: 20, right: 20, bottom: -200, left: 40 },
      		width = width_svgel - margin.left - margin.right, 
      		height = height_svgel - margin.top - margin.bottom, 
			z = d3.scaleOrdinal(d3.schemeCategory10).domain(devices);

    if (width < 50 || height < 50) { return; }

    const projection = d3.geoMercator()
      .scale(width / 2 / Math.PI)
      .translate([width / 2, height / 2]),
      path = d3.geoPath().projection(projection);

	this.loader.getWorldMesh().then((mesh) => {
    	svg.append('path')
			.attr("d", path(topojson.mesh(mesh)))
			.attr('opacity', 0.2)
			.attr("stroke", '#000')
			.attr("fill", "none");
    });

    // add circles to svg
	var datas = svg.selectAll("circle").data(impacts);

	//filter out impacts that have lat/lon of 0,0 (i.e. we don't know where they are located)
	datas.filter((d) => {(d.lat == 0 && d.lon == 0) ? 0 : 1});
	  
    datas.enter().append("circle")
      .attr("cx", (d) => {
        const lat = projection([d.lon, d.lat])[0];
        return lat;
      })
      .attr("cy", (d) => {
        const lon = projection([d.lon, d.lat])[1];
        return lon;
      })
      .attr('opacity', (d) => {
        let highApp = this.highlightApp || this._hoveringApp;
        if (highApp) {
          return d.device === highApp ? 0.75 : 0.01;
        }
        return 0.8;
      }).attr("r", (d) => {
        //return Math.floor(80*d.impact / minmax[1]);
		return 8;
	  }).attr("fill", (d) => z(d.ip))
      .on('mouseenter', (d) => this.hover.hoverChanged(undefined))
      .on('mouseleave', (d) => this.hover.hoverChanged(undefined));

    const leading = 26;

  	}
	
	@HostListener('window:resize')
  	onResize() {
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

