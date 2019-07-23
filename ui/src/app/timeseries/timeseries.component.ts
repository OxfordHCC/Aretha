 import { Input, Component, OnChanges, HostListener, ElementRef, SimpleChanges, AfterViewInit, NgZone, ViewEncapsulation, Output, EventEmitter, ViewChild } from '@angular/core';
 import { LoaderService, GeoData, Device } from '../loader.service';
 import { Http, HttpModule} from '@angular/http';
 import { Observable } from 'rxjs';
 import { FocusService } from 'app/focus.service';
 import { HoverService} from "app/hover.service";
 import { Subscription } from 'rxjs';
 import * as d3 from 'd3';
 import * as _ from 'lodash';
 import { TimeSelection } from '../layout-timeseries/layout-timeseries.component';
import { persistentColor } from '../utils';
 
 @Component({
	// encapsulation: ViewEncapsulation.None, 
	selector: 'app-timeseries',
	templateUrl: './timeseries.component.html',
	styleUrls: ['./timeseries.component.scss']
})
export class TimeseriesComponent implements AfterViewInit, OnChanges {
	 
	@Input() impacts;
	@Input() geodata: GeoData[];
	@Input() impactChanges : Observable<any>;
	@Input() devices :Device[];
	@Input() timeSelectorWidth = 200;				
	@Output() selectedTimeChanged = new EventEmitter<TimeSelection>();
	
	_hoveringApp: string;
	_ignoredApps: string[];
	_impact_listener : Subscription;
	vbox = { width: 700, height: 1024 };
	scale = false;
	
	margin = { top: 20, right: 20, bottom: 10, left: 20 };
	svgel: any; // actually an HTMLElement	
	
	@Input() showtimeselector: boolean;
	@Input() byDestination: boolean;
	
	@ViewChild('graphel')
	graphEl: ElementRef;
	
	selectedTime = -1;
	
	// for debug visualisation
	debug_impacts_arr : any;
	debug_series: any;
	debug_yscale: any;
	debug_series_scale: any;
	// debug_macs: string[] = [];
	// debug_
	
	mouseX = undefined;
	mouseDown = false;
	elHeight: any;
	elWidth: any;
	 impacts_arr: any;
	
	constructor(private httpM: HttpModule, 
		private http: Http, 
		private el: ElementRef,
		private loader: LoaderService,
		private focus: FocusService,
		private hover: HoverService,
		private zone:NgZone) {
			
			// hover.HoverChanged$.subscribe((target) => {
			// 	if (target !== this._hoveringApp) {
			// 		this._hoveringApp = target ? target as string : undefined;
			// 		this.render();
			// 	}
			// });
			
			// this._ignoredApps = [];
			
			// focus.focusChanged$.subscribe((target) => {
			// 	if (target !== this._ignoredApps) {
			// 		this._ignoredApps = target ? target as string[] : [];
			// 		this.render();
			// 	}
			// });
			
			this.loader.asyncDeviceChanges().subscribe(devices => {
				console.info(` ~ device name update ${devices.length} devices`);                
				devices.map( d => { 
					console.info(`time:: adding mac::name binding ${d.mac} -> ${d.nickname}`);
					this.devices[d.mac] = d.name; 
				});
				this.render();
			});  
		}
		
		ngAfterViewInit(): void { 
			console.log('GRAPHEL OFFSETWIDTH', this.graphEl, this.graphEl.nativeElement.parentElement.offsetWidth, this.graphEl.nativeElement.parentElement.offsetHeight);
			(<any>window)._gel = this.graphEl;
			try { 
				this.elWidth = this.graphEl.nativeElement.parentElement.offsetWidth;
				this.elHeight = this.graphEl.nativeElement.parentElement.offsetHeight;
			} catch(E) { console.log(E); }
			this.render(); 
		}
		
		getSVGElement() {
			const nE: HTMLElement = this.el.nativeElement;
			return Array.from(nE.getElementsByTagName('svg'))[0];
		}
		
		// this gets called when impacts changes
		ngOnChanges(changes: SimpleChanges): void {
			console.info('time:: ngOnChanges ', changes);
			// console.log('onchanges GRAPHEL OFFSETWIDTH', this.graphEl, this.graphEl.nativeElement.offsetWidth, this.graphEl.nativeElement.offsetHeight);
			var this_ = this;
			if (this.impactChanges && this._impact_listener === undefined) { 
				this._impact_listener = this.impactChanges.subscribe(target => {
					this.zone.run(() => this_.render());
				});	
			}
			if (this.devices) { this.devices = Object.assign({}, this.devices);}	
			if (this.impacts) { 
				this._process_impacts(this.impacts);
				this.render();
			}
		}
		
		wrap(text, width) {
			text.each(function() {
				var text = d3.select(this),
				words = text.text().split(/\s+/).reverse(),
				word,
				line = [],
				lineNumber = 0,
				lineHeight = 1.1, // ems
				y = text.attr("y"),
				dy = parseFloat(text.attr("dy")),
				tspan = text.text(null).append("tspan")
				.style('text-anchor', 'end').attr("x", 0).attr("y", y).attr("dy", dy + "em");
				while (word = words.pop()) {
					line.push(word);
					tspan.text(line.join(" "));
					if (tspan.node().getComputedTextLength() > width) {
						line.pop();
						tspan.text(line.join(" "));
						line = [word];
						tspan = text.append("tspan")
						.style('text-anchor', 'end').attr("x", -20).attr("y", y).attr("dy", ++lineNumber * lineHeight + dy + "em").text(word);
					}
				}
			});
		}

		_process_impacts(impacts): void {
			// 
			let minutes = Object.keys(impacts).map(x => +x);
			minutes.sort();
			const impacts_src = minutes.map(m => ({ date: new Date(+m*60*1000), impacts: impacts[m+""] }));
			this.impacts_arr = this.byDestination ? this.rectify_impacts_arr(impacts_src) : impacts_src;
		}   
		
		rectify_impacts_arr(iarr: any): any {

			// first step, invert 
			// input: [ { date: x, impacts: { mac : { ip0:xx ... ipN:yy } } ... ]
			// output: [ { date: x, impacts: { ip : { mac0:xx ... macN:yy } } ]

			let ip_to_company = _.fromPairs(this.geodata.map( x => [x.ip, x.company_name]));

			let impact_by_ip = iarr.map((el) => {
				const ii = _.flatten(_.toPairs(el.impacts).map(macimp => {
					const mac = macimp[0], imp = _.toPairs(macimp[1]),
						// condense to companies
						company_impact = imp.reduce((tot, ipimp) => {
							const [ip, impact] = ipimp,
								company = ip_to_company[ip];
							if (!ip) { console.info('warning couldnt find ip ', ip); return tot; }
							tot[company] = (tot[company] || 0) + impact;
							return tot;
						}, {}),
						company_impact_arr = _.toPairs(company_impact);	

					return company_impact_arr.map( compimp => [mac, ...compimp] );
				})),
				ips = ii.reduce((obj, xyz) => { 
					const [mac, ip, imp] = xyz;
					const impactpermac = obj[ip] || {};
					impactpermac[mac] = imp;
					obj[ip] = impactpermac;
					return obj;
				}, {});
				return { date: el.date, impacts: ips };
			});

			// [mac, [[ip0, xx], ... ] -> [mac ip0 xx] [mac ip1 yy] -> ip0
			// [ip0, [[mac, xx], ... ]
			return impact_by_ip;
		}	
		
		render() {
			// console.info('timeseries.render[',this.showtimeselector,'] ', this.impacts);
			const svgel = this.svgel || this.getSVGElement(),
				margin = this.margin;

			if (!svgel || this.impacts === undefined || !this.elHeight || !this.elWidth || this.impacts_arr === undefined) { 
				console.info('timeseries: impacts undefined, chilling');
				return; 
			}
			this.svgel = svgel;
			
			const svg = d3.select(svgel),
				width_svgel = this.elWidth,
				height_svgel = this.elHeight,
				height = height_svgel - this.margin.top - this.margin.bottom,
				impacts = this.impacts;
	
			// set width and height of svel
			svg.attr('width', width_svgel).attr('height', height_svgel); 			
			
			svg.selectAll('*').remove();			
		
			const impacts_arr = this.impacts_arr,			
				// this hellish line simply does a union over all impact keys : which is the total set of 
				// destination IP addresses.  We do this instead of taking the first one to be ultra careful
				// that the back end doesn't do anything sneaky like omit some hosts for certain time indexes
				stack_keys = new Array(...impacts_arr.map(v => Object.keys(v.impacts)).reduce((a,x) => new Set<string>([...a, ...x]), new Set<string>()));

			stack_keys.sort();
			if (this.byDestination) { 
				console.info('stack keys ', stack_keys.slice(0,10));
			}

			const series = d3.stack()
					.keys(stack_keys)
					.offset(d3.stackOffsetSilhouette)
					// .offset(d3.stackOffsetWiggle)
					// .order(d3.stackOrderInsideOut)
					.value((d,key) => _.values(d.impacts[key]||{}).reduce((x,y)=>x+y, 0))(impacts_arr),
				// now create scales
				stackscale = d3.scaleOrdinal().domain(stack_keys).range(d3.schemeCategory10),
				xscale = d3.scaleTime()
					.domain(d3.extent(impacts_arr, d=>d.date))
					.range([this.margin.left, width_svgel - this.margin.right]),
				yscale = d3.scaleLinear()
					.domain([d3.min(series, d => d3.min(d, dd => dd[0])), d3.max(series, d => d3.max(d, dd => dd[1]))])
					.range([height - this.margin.bottom, this.margin.top]);
			
			// -----
			// this.debug_impacts_arr = minutes.map(m => ({ date: new Date(+m*60*1000), m:m, impacts: impacts[m+""] }));
			// this.debug_series = series;
			// this.debug_series_scale = _.mapValues(series, (timeseries) => _.mapValues(timeseries, v => [yscale(v[0]), yscale(v[1])]));
			// ----
			
			// single area which operates directly on the stack structure inner values
			const area = d3.area()
				.x((d) => xscale(d.data.date)) 
				.y0(d => yscale(d[0])) // + 100*(Math.random()-0.5))
				.y1(d => yscale(d[1])) // + 100*(Math.random()-0.5));
			
			svg.append("g")
				.attr('class','plot')
				.selectAll("path")
				.attr("class", "stream")
				.data(series)
				.join("path") // join is only defined in d3@5 and newer
				.attr("fill", ({key}) => persistentColor(key)) // // stackscale(key))
				.attr("d", area);
			// .append("title")
			//   .text(({key}) => key);		
			
			svg.append('g')
				.attr('class', 'axis y')
				.call(d3.axisLeft(yscale).ticks(null, '.0s'))
				.append('text')
				.attr('x', 20)
				.attr('y', yscale(yscale.ticks().pop()) - 12)
				.attr('dy', '0.22em')
				.text('Traffic (bytes)');
			
			svg.append('g')
				.attr('class', 'axis x')
				.call(d3.axisBottom(xscale))
				.selectAll('text')
				.style('text-anchor', 'end')
				.attr('y', 1)
				.attr('dx', '-.8em')
				.attr('dy', '.15em')
				.attr('transform', 'rotate(-90)');
				// .call(this.wrap, margin.bottom - 10);
			
			if (this.showtimeselector) { 
				this.drawTimeSelector(svg, xscale, height, width_svgel, height_svgel); 
			}
		}

		// renders the time window dragger box
		drawTimeSelector(svg, xscale, height, width_svgel, height_svgel) { 
			if (svg.selectAll('g.dragwindow').size() === 0) {
				// attach only once	
				let updateMouse = (xx:number) => {
					this.mouseX = xx;
					// console.log('new time is ', xscale.invert(this.mouseX));
					this.selectedTimeChanged.emit({
						centre: xscale.invert(this.mouseX),
						start: xscale.invert(this.mouseX-this.timeSelectorWidth/2),
						end:xscale.invert(this.mouseX+this.timeSelectorWidth/2)
					});
					this.render();
				};
				if (this.mouseX === undefined) { 
					setTimeout(() => updateMouse(width_svgel - this.margin.right - this.margin.left), 0);
				}
				svg.on("mousedown", dd => {
					this.mouseDown = true;
					updateMouse(d3.event.clientX);
				});
				svg.on("mousemove", dd => {
					if (this.mouseDown) { updateMouse(d3.event.clientX); }
				});
				svg.on("mouseup", dd => { this.mouseDown = false; });
			}
			// enter selection
			const enters = svg.selectAll('g.dragwindow').data([0]).enter().append('g').attr('class', 'dragwindow');
			
			enters.append('rect').attr('class','timebox')
				.attr('x',() => this.mouseX-(this.timeSelectorWidth/2))
				.attr('y', this.margin.top)
				.attr('width', this.timeSelectorWidth)
				.attr('height', height);
				
			enters.append('line')
				.attr('class','timeline')
				.attr('x1', this.mouseX)
				.attr('y1', this.margin.top)
				.attr('x2', this.mouseX)
				.attr('y2', height+this.margin.top);		
				
			d3.select('svg').selectAll('rect.timebox')
				.attr('x',this.mouseX-(this.timeSelectorWidth/2))
				.attr('y', this.margin.top)
				.attr('width', this.timeSelectorWidth)
				.attr('height', height);        
				
			d3.select('svg').selectAll('line.timeline')            
				.attr('x1',() => this.mouseX)
				.attr('x2',() => this.mouseX);
		}			
		
		
		@HostListener('window:resize')
		onResize() {
			this.render();
		}
		
	}
	