import { Input, Component, OnInit, OnChanges, HostListener, ElementRef, SimpleChanges, AfterViewInit, NgZone } from '@angular/core';
import { LoaderService, DeviceImpact, GeoData, Device } from '../loader.service';
import { Http, HttpModule, Headers, URLSearchParams } from '@angular/http';
import { Observable } from '../../../node_modules/rxjs/Observable';
import { HostUtilsService } from 'app/host-utils.service';
import { FocusService } from 'app/focus.service';
import { HoverService, HoverTarget } from "app/hover.service";
import { Subscription } from '../../../node_modules/rxjs/Subscription';
import * as d3 from 'd3';
import * as _ from 'lodash';

@Component({
  selector: 'app-timeseries',
  templateUrl: './timeseries.component.html',
  styleUrls: ['./timeseries.component.css']
})

export class TimeseriesComponent implements AfterViewInit, OnChanges {

	@Input() impacts: DeviceImpact[];
	@Input() geodata: GeoData[];
	@Input() impactChanges : Observable<any>;
  	@Input('devices') devices :Device[];
  	
	_hoveringApp: string;
  	_ignoredApps: string[];
  	_impact_listener : Subscription;
	vbox = { width: 700, height: 1024 };
	scale = false;

	margin = { top: 20, right: 20, bottom: 10, left: 20 };
	svgel: any; // actually an HTMLElement	

	constructor(private httpM: HttpModule, 
    	private http: Http, 
    	private el: ElementRef,
    	private loader: LoaderService,
    	private hostutils: HostUtilsService,
    	private focus: FocusService,
    	private hover: HoverService,
    	private zone:NgZone) {
  
    	hover.HoverChanged$.subscribe((target) => {
      		if (target !== this._hoveringApp) {
        		this._hoveringApp = target ? target as string : undefined;
        		this.render();
      		}
		});

    	this._ignoredApps = new Array();

    	focus.focusChanged$.subscribe((target) => {
      		if (target !== this._ignoredApps) {
        		this._ignoredApps = target ? target as string[] : [];
        		this.render();
      		}
    	});

    	this.loader.asyncDeviceChanges().subscribe(devices => {
        	console.info(` ~ device name update ${devices.length} devices`);                
        	devices.map( d => { 
          		console.info(`adding mac::name binding ${d.mac} -> ${d.nickname}`);
          		this.devices[d.mac] = d.name; 
        	});
        	this.render();
    	});  
  	}
	
	ngAfterViewInit(): void { this.render(); }
	
	getSVGElement() {
    	const nE: HTMLElement = this.el.nativeElement;
    	return Array.from(nE.getElementsByTagName('svg'))[0];
  	}
  	
	// this gets called when this.usage_in changes
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
    	if (this.devices) { this.devices = Object.assign({}, this.devices);}	
		this.render();
  	}

	render() {

		const svgel = this.svgel || this.getSVGElement();	
    	if (!svgel || this.impacts === undefined ) { 
      		console.info('timeseries: impacts undefined, chilling');
      		return; 
		}

		this.svgel = svgel;
		// svgel



		let rect = svgel.getBoundingClientRect(),
			width_svgel = Math.round(rect.width - 5),
			height_svgel = Math.round(rect.height - 5),
			svg = d3.select(svgel);

		if (!this.scale) {
			svg.attr('width', width_svgel).attr('height', height_svgel);
		} else {
			svg.attr('viewBox', `0 0 ${this.vbox.width} ${this.vbox.height}`)
				.attr('virtualWidth', this.vbox.width)
				.attr('virtualHeight', this.vbox.height)
				.attr('preserveAspectRatio', 'none') //  "xMinYMin meet")
			width_svgel = this.vbox.width;
			height_svgel = this.vbox.height;
		}

		const width = width_svgel - this.margin.left - this.margin.right;
		const height = height_svgel - this.margin.top - this.margin.bottom; 
		
		let impacts = this.impacts;
      	let devices = this.devices;
		let geodata = this.geodata; 

		svg.selectAll('*').remove();

		console.info('impacts ', impacts);
		console.info('devices', devices);

		// d3 wants an array, not an object so we unpack the times and turn them into 
		// a single simple arry
		let minutes = Object.keys(impacts);
		minutes.sort();
		const impacts_arr = minutes.map(m => ({ date: new Date(+m*60*1000), impacts: impacts[m] })),
			// this hellish line simply does a union over all impact keys : which is the total set of 
			// destination IP addresses.  We do this instead of taking the first one to be ultra careful
			// that the back end doesn't do anything sneaky like omit some hosts for certain time indexes
			stack_keys = new Array(...impacts_arr.map(v => Object.keys(v.impacts)).reduce((a,x) => new Set<string>([...a, ...x]), new Set<string>())),
			// now we turn this into a stack.			
			series = d3.stack()
				.keys(stack_keys)
				.offset(d3.stackOffsetWiggle)
				.order(d3.stackOrderInsideOut)
				.value((d,key) => _.values(d.impacts[key]).reduce((x,y)=>x+y, 0))(impacts_arr); // sum contributions from each device

		// DEBUGGING HOOKS >> 
		// console.info('impacts arr', impacts_arr, 'stack keys', stack_keys, 'series', series);
		// (<any>window).d3 = d3;
		// (<any>window)._ss = series;
		// (<any>window)._ia = impacts_arr;
		// (<any>window)._sk = stack_keys;			
		// END DEBUGGING HOOKS
		
		// now create scales
		const stackscale = d3.scaleOrdinal().domain(stack_keys).range(d3.schemeCategory10),
			xscale = d3.scaleTime()
				.domain(d3.extent(impacts_arr, d=>d.date))
				.range([this.margin.left, width_svgel - this.margin.right]),
			yscale = d3.scaleLinear()
    			.domain([d3.min(series, d => d3.min(d, dd => dd[0])), d3.max(series, d => d3.max(d, dd => dd[1]))])
				.range([height - this.margin.bottom, this.margin.top]);

		// single area which operates directly on the stack structure inner values
		const area = d3.area()
				.x((d) => xscale(d.data.date)) 
				.y0(d => yscale(d[0]))
    			.y1(d => yscale(d[1]));

		svg.append("g")
			.selectAll("path")
			.data(series)
			.join("path") // join is only defined in d3@5 and newer
			  .attr("fill", ({key}) => stackscale(key))
			  .attr("d", area)
			.append("title")
			  .text(({key}) => key);		

		/*
		//plot x axis
		svg.append("g")
      		.call(xAxis);
		*/
	}
	
	@HostListener('window:resize')
  	onResize() {
    	this.render();
	}
}
