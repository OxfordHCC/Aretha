 import { Input, Component, OnChanges, HostListener, ElementRef, SimpleChanges, AfterViewInit, NgZone, ViewEncapsulation, Output, EventEmitter, ViewChild } from '@angular/core';
 import { LoaderService, GeoData, Device, CompanyInfo, CompanyDB } from '../loader.service';
 import { Http, HttpModule} from '@angular/http';
 import { Observable } from 'rxjs';
 import { FocusService } from 'app/focus.service';
 import { HoverService} from "app/hover.service";
 import { Subscription } from 'rxjs';
 import * as d3 from 'd3';
 import * as _ from 'lodash';
 import { TimeSelection } from '../layout-timeseries/layout-timeseries.component';
import { persistentColor, dateMin, matchCompanies } from '../utils';
 
 @Component({
	encapsulation: ViewEncapsulation.None, 
	selector: 'app-timeseries',
	templateUrl: './timeseries.component.html',
	styleUrls: ['./timeseries.component.scss']
})
export class TimeseriesComponent implements AfterViewInit, OnChanges {
	@Input() impacts;
	
	@Input() impactChanges : Observable<any>;
	@Input() devices :Device[];
	@Input() timeSelectorWidth = 40;				
	@Input() detailedTicks = false;

	@Input() geodata: GeoData[];
	@Input() companydb;
	@Input() adsdb;

	@Output() selectedTimeChanged = new EventEmitter<TimeSelection>();
	@Output() legendClicked = new EventEmitter<any>();
	
	_hoveringApp: string;
	_ignoredApps: string[];
	_impact_listener : Subscription;
	vbox = { width: 700, height: 1024 };
	scale = false;
	
	margin = { top: 20, right: 280, bottom: 10, left: 20 };
	svgel: any; // actually an HTMLElement	
	
	@Input() showtimeselector: boolean;
	@Input() byDestination: boolean;

	@Input() showLegend = false;
	
	@ViewChild('graphel')
	graphEl: ElementRef;
	
	selectedTime = -1;

	company_to_info: {[c:string]:CompanyInfo};
	
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
	hovering: any;
	hover_timeout: any;

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
			// console.log('GRAPHEL OFFSETWIDTH', this.graphEl, this.graphEl.nativeElement.parentElement.offsetWidth, this.graphEl.nativeElement.parentElement.offsetHeight);
			// (<any>window)._gel = this.graphEl;
			this._recomputeSizes();
			this.render(); 
		}

		_recomputeSizes(): void {
			try { 
				this.elWidth = this.graphEl.nativeElement.parentElement.offsetWidth;
				this.elHeight = this.graphEl.nativeElement.parentElement.offsetHeight-10;
			} catch(E) { console.log(E); }
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
			
			if (this.company_to_info === undefined && this.companydb && this.geodata && this.adsdb) { 
				/// we just need to do this once >> 
				this.company_to_info = matchCompanies(this.geodata, this.companydb, this.adsdb);
				console.info('initialised companyinfo ', this.company_to_info);
			}

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
				// company_to_info: {[c:string]: CompanyInfo} = {};			

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
				.style("pointer-events","auto")				
				.data(series)
				.join("path") // join is only defined in d3@5 and newer
				.attr("fill", ({key}) => persistentColor(key)) // // stackscale(key))
				.attr('opacity', ({key}) => this.hovering ? (this.hovering === key ? 1.0 : 0.2) : 1.0 )
				.attr("d", area)
				.on('mouseenter', (d) => { 
					if (this.hover_timeout) { clearTimeout(this.hover_timeout); }
					this.hovering = d.key; 
					this.render();
					this.hover_timeout = setTimeout(() => { this.hover_timeout = undefined; this.hovering = undefined; this.render(); }, 250);
				}).on('mouseleave', (d) => { 
					// console.info('mouseout', d, this); 
					this.hovering = undefined;					
					this.render();
				}); // .on('mousedown', d => { console.log('path click ', d); });

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
				.call(d3.axisTop(xscale)
					.ticks(d3.timeMinute.every(60))
					.tickPadding(10)
					.tickFormat(d3.timeFormat(this.detailedTicks ? "%a %B %d %H:%M": ""))
					.tickSizeInner(-height_svgel)
					.tickSizeOuter(-10)					
				).selectAll('text')
				.style('text-anchor', 'end')
				.attr('y', 1)
				.attr('dx', '-0.4em')
				.attr('dy', '-.4em')
				.attr('transform', 'rotate(-90)');
				// .call(this.wrap, margin.bottom - 10);

			if (this.detailedTicks) { 
				svg.append('g')
					.attr('class', 'axis xlight')
					.call(d3.axisTop(xscale)
						.ticks(d3.timeMinute.every(5))
						// .tickPadding(20)
						.tickFormat("")
						.tickSizeInner(-height_svgel)
						.tickSizeOuter(-height_svgel)					
					).selectAll('text')
					.style('text-anchor', 'end')
					.attr('y', 1)
					.attr('dx', '-.8em')
					.attr('dy', '.15em')
					.attr('transform', 'rotate(-90)');
					// .call(this.wrap, margin.bottom - 10);
			}				
			
			if (this.showtimeselector) { 
				this.drawTimeSelector(svg, xscale, height, width_svgel, height_svgel); 
			}
			if (this.showLegend) { 
				this.drawLegend(svg, width_svgel, height_svgel, stack_keys); 
			}
		}

		// renders the time window dragger box
		drawTimeSelector(svg, xscale, height, width_svgel, height_svgel) { 
			if (svg.selectAll('g.dragwindow').size() === 0) {
				// attach only once	
				let updateMouse = (xx:number) => {
					// this makes it impossible to drag the time selector into
					// the future
					const timeXX = xscale.invert(xx + this.timeSelectorWidth/2), // we want to test the max extent
						now = d3.timeMinute.floor(new Date()),
						maxtime = dateMin(timeXX, now);

					this.mouseX = xscale(maxtime)-this.timeSelectorWidth/2;
					this.selectedTimeChanged.emit({
						centre: d3.timeMinute.floor(xscale.invert(this.mouseX)),
						start: d3.timeMinute.floor(xscale.invert(this.mouseX-this.timeSelectorWidth/2)),
						end:d3.timeMinute.ceil(xscale.invert(this.mouseX+this.timeSelectorWidth/2))
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

				svg.on('wheel.zoom', dd => {
					console.info('mouse wheel - X:', d3.event.wheelDeltaX, ' Y:', d3.event.wheelDeltaY);
					this.timeSelectorWidth = Math.min(320, Math.max(10, this.timeSelectorWidth + d3.event.wheelDeltaY));
					updateMouse(this.mouseX);
				});
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
		
		drawLegend(svg, width, height, stackkeys) {
			// legend
			
			const leading = 26,
				colwidth = 230,
				max_rows = Math.floor((height-40)/(leading)),
				get_company_type = d => this.company_to_info && this.company_to_info[d] && this.company_to_info[d].typetag || undefined,
				company_types = _.uniq(stackkeys.map(get_company_type).filter(x => x));

			// stackkeys = _.range(50).map(x => `Hello {x}!`);

			const legtype = svg.selectAll('g.legtype').data([0]).enter().append('g')
				.attr('class', 'legtype')
				.selectAll('g.legtypebox')
				.data(company_types)
				.enter()
				.append('g')
				.attr('class', 'legtypebox')
				.attr('transform', function (d, i) { 
					const coln = Math.floor(i / max_rows);
					return `translate(${width-(coln+1)*colwidth-40},${(i%max_rows)*leading + 50 })`; 
				});

			legtype.append('rect')
				.attr('class', 'typerect')
				.attr('x',0)
				.attr('y', d => {
					// index 
					let idx = company_types.indexOf(d),
						yoff = company_types.slice(0, company_types.indexOf(d)).reduce((sum, xx) => {
							return stackkeys.filter(x => get_company_type(x) === xx).length*leading;
						}, 0);
					return yoff;
				}).attr('width',colwidth)
				// .style("pointer-events","auto")	
				.attr('height', d => {
					const count = stackkeys.filter(x => get_company_type(x) === d).length;
					return count*leading;
				}).attr('opacity', 1)
				.attr('stroke', d => d === 'advertising' ? "rgba(255,180,180,0.4)" : "#000")
				.attr('fill', 'none');

			legtype.append('text')
				.attr('class', 'typename')
				.attr('x',0)
				.attr('y', d => {
					// index 
					let idx = company_types.indexOf(d),
						yoff = company_types.slice(0, company_types.indexOf(d)).reduce((sum, xx) => {
							return stackkeys.filter(x => get_company_type(x) === xx).length*leading;
						}, 0);
					return yoff;
				})
				.text(d => d);

			// const legel = svg.selectAll('g.legend').data([0]).enter().append('g')
			// 	.attr('class', 'legend')
			// 	.selectAll('g.legel')
			// 	.data(stackkeys)
			// 	.enter()
			// 	.append('g')
			// 	.attr('class','legel')
			// 	.attr('transform', function (d, i) { 
			// 		const coln = Math.floor(i / max_rows);
			// 		return `translate(${width-(coln+1)*colwidth-40},${(i%max_rows)*leading + 50 })`; 
			// 	}).on('mousedown', (d) => { console.info('click ', d); this.legendClicked.emit(d); })
			// 	.on('mouseenter', (d) => { 
			// 		if (this.hover_timeout) { clearTimeout(this.hover_timeout); }
			// 		this.hovering = d; 
			// 		this.render();
			// 		this.hover_timeout = setTimeout(() => { this.hover_timeout = undefined; this.hovering = undefined; this.render(); }, 250);
			// 	}).on('mouseout', (d) => { 
			// 		this.hovering = undefined;
			// 		this.render();
			// 	});	// .style("pointer-events","auto")

			// legel.append('rect')
			// 	.attr('class','main')
			// 	.attr('x',0)
			// 	.attr('y',-2)
			// 	.attr('width',colwidth)
			// 	// .style("pointer-events","auto")	
			// 	.attr('height', leading-4)
			// 	.attr('opacity', 1)
			// 	.attr('stroke', d => {
			// 		return this.company_to_info && this.company_to_info[d] && this.company_to_info[d].typetag === 'advertising' ? "rgba(255,180,180,0.4)" : "#fff";
			// 	 }).attr('fill', d => {
			// 		return this.company_to_info && this.company_to_info[d] && this.company_to_info[d].typetag === 'advertising' ? "rgba(255,180,180,0.4)" : "#fff";
			// 	 }).on('mousedown', (d) => { console.info('click ', d); this.legendClicked.emit(d)});
			
			// legel.append('rect')
			// 	.attr('class', 'legsq')
			// 	.attr('x', 3) // width - 140 - 19)
			// 	.attr('y', 3)
			// 	.attr('width', 12)
			// 	.attr('height', 12)
			// 	.style("pointer-events","auto")				
			// 	.attr('fill', d => persistentColor(d))
			// 	.attr('opacity', d => this.hovering ? ( this.hovering === d ? 1.0 : 0.2 ) : 1.0)
			// 	.on('mousedown', (d) => { console.info('click ', d); this.legendClicked.emit(d)});

				
			// legel.append('text')
			// 	.attr('x', 20) // width - 140 - 24)
			// 	.attr('y', 9.5)
			// 	.attr('dy', '0.32em')
			// 	// .style("pointer-events","auto")				
			// 	.text(d => this.byDestination ? d : this.devices[d].name)
			// 	.attr('opacity', d => this.hovering ? ( this.hovering === d ? 1.0 : 0.2 ) : 1.0)
			// 	.on('mousedown', (d) => { console.log('click text ', d); this.legendClicked.emit(d)});
			
			(<any>window)._dd = d3;
		}
		
		@HostListener('window:resize')
		onResize() {
			this._recomputeSizes();
			this.render();
		}
		
	}
