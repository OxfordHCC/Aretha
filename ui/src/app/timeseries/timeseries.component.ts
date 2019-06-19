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

		const svgel = this.getSVGElement();
    	if (!svgel || this.impacts === undefined ) { 
      		console.info('timeseries: impacts undefined, chilling');
      		return; 
    	}

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
      	
		const margin = { top: 20, right: 20, bottom: 160, left: 50 };
      	const width = width_svgel - margin.left - margin.right;
      	const height = height_svgel - margin.top - margin.bottom; 
		
		let impacts = this.impacts;
      	let devices = this.devices;
		let geodata = this.geodata; 

		/*
		let data = [
			{"name": "a", "value": 100, "date": 1, "values": [-10, -20]}
		];
		
		//configure x axis
		let x = d3.scaleTime()
    		.domain(d3.extent(data, d => d.date))
    		.range([margin.left, width - margin.right])

		let test = [
			d3.min(data, d => d.values[0]), 
			d3.max(data, d => d.values[1])];

		//configure y axis
		let y = d3.scaleLinear()
    		.domain([d3.min(data, d => d.values[0]), d3.max(data, d => d.values[1])])
    		.range([height - margin.bottom, margin.top])

		//set x axis
		let xAxis = g => g
    		.attr("transform", `translate(0,${height - margin.bottom})`)
    		.call(d3.axisBottom(x).ticks(width / 80).tickSizeOuter(0))
    		.call(g => g.select(".domain").remove())

		//set colour
		let color = d3.scaleOrdinal(d3.schemeCategory10).domain(data.map(d => d.name))

		let area = d3.area()
    		.curve(d3.curveStep)
    		.x(d => x(d.date))
    		.y0(d => y(d.values[0]))
    		.y1(d => y(d.values[1]))

		console.log(impacts);
		console.log(geodata);
		console.log(devices);

		function multimap(entries, reducer = (p, v) => (p.push(v), p), initializer = () => []) {
  			const map = new Map();
			for (const [key, value] of entries) {
    			map.set(key, reducer(map.has(key) ? map.get(key) : initializer(key), value));
  			}
  			return map;
		}

		const stack = d3.stack()
      		.keys(top)
      		.value((d, key) => d.get(key).value)
      		.offset(d3.stackOffsetSilhouette)
    		(Array.from(
      			multimap(
        		data.map(d => [+d.date, d]),
        		(p, v) => p.set(v.name, v),
        		() => new Map
      			).values()
    		));

		let stack = d3.stack()
    		.offset("silhouette")
    		.values(function(d) { return d.values; })
    		.x(function(d) { return d.date; })
    		.y(function(d) { return d.value; });
		
		//plot graph
		svg.append("g")
    		.selectAll("path")
    		//.data([...multimap(data.map(d => [d.name, d]))])
    		.data([...data.map(d => [d.name, d.value])])
    		.join("path")
      			.attr("fill", ([name]) => color(name))
      			.attr("d", ([, values]) => area(values))
    		.append("title")
      			.text(([name]) => name);
  		
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
