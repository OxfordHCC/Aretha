import { Component, Input, OnInit, OnChanges, SimpleChanges, ViewChild, ElementRef, AfterViewInit, ViewEncapsulation, EventEmitter, Output, HostListener, NgZone } from '@angular/core';
import { LoaderService, CompanyInfo, CompanyDB, APIAppInfo } from '../loader.service';
import { AppUsage } from '../usagetable/usagetable.component';
import * as d3 from 'd3';
import * as _ from 'lodash';
import { HostUtilsService } from 'app/host-utils.service';
import { FocusService } from 'app/focus.service';
import { HoverService, HoverTarget } from "app/hover.service";
import { Http, HttpModule, Headers, URLSearchParams } from '@angular/http';
import { Observable } from '../../../node_modules/rxjs/Observable';
import { Observer } from '../../../node_modules/rxjs/Observer';
import { Subscription } from '../../../node_modules/rxjs/Subscription';
import { DeviceImpact, GeoData, Device } from '../loader.service';

@Component({
  selector: 'app-refinebar',
  templateUrl: './refinebar.component.html',
  styleUrls: ['./refinebar.component.scss'],
  encapsulation: ViewEncapsulation.None,
})

export class RefinebarComponent implements AfterViewInit, OnChanges {
  	// still in use!
  	companyid2info: CompanyDB;

	@Input() impacts: DeviceImpact[];
	@Input() geodata: GeoData[];
	@Input() impactChanges : Observable<any>;
  	@Input('devices') devices_in :Device[];
  	_devices: Device[];
  
  	private init: Promise<any>;
  	lastMax = 0;
  	// _timeSpan = 'd';
	normaliseImpacts = false;

  	// incoming attribute
  	@Input() showModes = true;
  	@Input() highlightApp: APIAppInfo;
  	@Input() showLegend = true;
  	@Input() showTypesLegend = false;
  	@Input() showXAxis = true;
  	@Input() scale = false;
	@Input() maxCompanies = 20;
  	linear = false;
  	vbox = { width: 700, height: 1024 };
  	highlightColour = '#FF066A';

  	_hoveringType: string;
  	_companyHovering: CompanyInfo;
  	_hoveringApp: string;
  	_ignoredApps: string[];
  	_impact_listener : Subscription;

	constructor(private httpM: HttpModule, 
    	private http: Http, 
    	private el: ElementRef,
    	private loader: LoaderService,
    	private hostutils: HostUtilsService,
    	private focus: FocusService,
    	private hover: HoverService,
    	private zone:NgZone) {
  
    	this.init = Promise.all([
      		this.loader.getCompanyInfo().then((ci) => this.companyid2info = ci),
    	]);

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
          		this._devices[d.mac] = d.name; 
        	});
        	this.render();
    	});  
  	}
	
	getSVGElement() {
    	const nE: HTMLElement = this.el.nativeElement;
    	return Array.from(nE.getElementsByTagName('svg'))[0];
  	}

  	addOrRemove(newClick: string): string[] {
    	// console.log(this._ignoredApps);
    	if (this._ignoredApps.indexOf(newClick) > -1) {
      		this._ignoredApps = this._ignoredApps.filter(obj => obj !== newClick);
    	} else {
      		this._ignoredApps.push(newClick);
    	}
    	this.render()
    	return this._ignoredApps
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
    	if (this.devices_in) { this._devices = Object.assign({}, this.devices_in);}	
		this.init.then(() => { this.render(); });
  	}

  	ngAfterViewInit(): void { this.init.then(() => this.render()); }

	private _getApp(appid: string): Promise<APIAppInfo> {
    	return this.loader.getCachedAppInfo(appid) && Promise.resolve(this.loader.getCachedAppInfo(appid))
      	|| this.loader.getFullAppInfo(appid);
  	}

  	nonLinearity(v):number { return this.linear ? v : Math.max(0, 5000*Math.log(v) + 10); }

	setHoveringTypeHighlight(ctype: string) {
    	let svg = this.getSVGElement();
    	this._hoveringType = ctype;
    	d3.select(svg).selectAll('rect.back').classed('reveal', false);
    	d3.select(svg).selectAll('.ctypelegend g').classed('selected', false)
    	if (ctype) {
      		d3.select(svg).selectAll('rect.back.' + ctype).classed('reveal', true);
      		d3.select(svg).selectAll('.ctypelegend g.' + ctype).classed('selected', true)
    	};
  	}
	
	// this is for displaying what company you're hovering on based 
  	// on back rects
  	_companyHover(company: CompanyInfo, hovering: boolean) {
    	this._companyHovering = hovering ? company : undefined;
  	}

  	@HostListener('mouseenter')
  	mouseEnter() { /*this.actlog.log('mouseenter', 'refinebar'); */ }

	@HostListener('mouseleave')
	mouseLv() { /*this.actlog.log('mouseleave', 'refinebar');*/ }  

	setHoveringApp(s: string) {
    	if (this._hoveringApp !== s) {
      		this._hoveringApp = s;
      		this.render();
    	}
  	}
	
  	render() {

		const svgel = this.getSVGElement();
    	if (!svgel || this.impacts === undefined ) { 
      		console.info('refinebar: impacts undefined, chilling');
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

		let compiledImpacts = []
      	let devices = _.uniq(this.impacts.map((x) => x.device));
		let companies = _.uniq(this.geodata.map((x) => x.company_name));
		
		//compile impacts for device/ip pairs into device/company pairs
		companies.forEach((comp) => {
			//geodata records for each ip belonging to company "comp"
			let addresses = this.geodata.filter((c) => comp === c.company_name);

			//impacts that are associated with an address in "addresses"
			let impacts = this.impacts.filter((i) => addresses.map((a) => a.ip).indexOf(i.company) != -1);

			//compile per device
			devices.forEach((dev) => {
				let total = impacts.filter((i) => i.device === dev).reduce(function(i, j){return i + j.impact}, 0);
				if (total > 0) {
					compiledImpacts.push({
						"company": comp,
						"device": dev,
						"impact": total
					});
				}
			});
		});

		let companySorted = compiledImpacts.sort((c1, c2) => c2.impact - c1.impact); 
		
		//fold smaller companies into an "other" category
		if (companySorted.length > this.maxCompanies) {
			let cutoff = companySorted[this.maxCompanies-1].impact;
			let companyFolded = [];
			let otherImpact = 0;
			companySorted.forEach((impact) => {
				if (impact.impact >= cutoff) { companyFolded.push(impact); }
				else { otherImpact += impact.impact; console.log("OPUSG"); }
			});
			companyFolded.push({"company": "Other", "device": "*", "impact": otherImpact});
			companySorted = companyFolded;
		}

		let by_company = companySorted; 
		companies = by_company.map((x) => x.company);

    	const stack = d3.stack(),
      	out = stack.keys(devices)(by_company),
      	margin = { top: 20, right: 20, bottom: this.showXAxis ? 160 : 0, left: 50 },
      	width = width_svgel - margin.left - margin.right, 
      	height = height_svgel - margin.top - margin.bottom; 

    	if (height < 0 || width < 0) {
      		console.error('height ', height, 'width ', width, 'exiting ');
      		// return
    	}
    
    	let g = svg.append('g').attr('transform', 'translate(' + margin.left + ',' + margin.top + ')'),
			x = d3.scaleBand()
        		.rangeRound([0, width]).paddingInner(0.05).align(0.1)
        		.domain(companies),
      		d3maxx = d3.max(by_company, function (d) { return d.impact; }) || 0,
      		ymaxx = this.lastMax = Math.max(this.lastMax, d3maxx),
      		this_ = this;

    	if (d3maxx < 0.7 * ymaxx) {
      		ymaxx = 1.1 * d3maxx;
    	}

		let y = d3.scaleLog()
     		.rangeRound([height, 0])
      		.domain([1, ymaxx]).nice(),
      	z = d3.scaleOrdinal(d3.schemeCategory20)
        	.domain(devices);

    	var self = this;

    g.selectAll('rect.back')
      .data(companies)
      .enter().append('rect')
      .attr('class', (company) => 'back ' + company) 
      .attr('x', (company) => x(company))
      .attr('y', 0)
      .attr('height', height)
	  .attr('width', x.bandwidth())
      .on('click', (d) => this.focus.focusChanged(d)) 
      .on('mouseenter', (d) => self.setHoveringApp(undefined)) 
      .on("mouseleave", (d) => {return}); 

    // main rects
    var self = this;
   
    const f = (selection, first, last) => {
      return selection.selectAll('rect')
        .data((d) => d)
        .enter().append('rect')
        .attr('class', 'bar')
		.attr('x', (d) => x(d.data.company))
		.attr('y', (d) => d.data.impact > 0 ? y(d.data.impact) : y(1))
		.attr('height', (d) => height - y(d.data.impact)) 
        .attr('width', x.bandwidth())
        .on('click', function (d) {
			self.focus.focusChanged(self.addOrRemove(this.parentElement.__data__.key))
        })
        .on('mouseleave', function (d) {
          this_.hover.hoverChanged(undefined);
        })
        .on('mouseenter', function (d) {
          if (this.parentElement && this.parentElement.__data__) {
            this_.hover.hoverChanged(this.parentElement.__data__.key);
          } 
        });
    };

    g.append('g')
      .selectAll('g')
      .data(d3.stack().keys(devices)(by_company))
      .enter().append('g')
      .attr('fill', (d) => {
        // highlightApp comes in from @Input() attribute, set using compare
        // _apphover comes in from hovering service, namely usagetable hover
        let highApp = this.highlightApp || this._hoveringApp;
        if (highApp) {
          return d.key === highApp ? z(d.key) : 'rgba(200,200,200,0.2)';
        }
        return z(d.key);
      })
      .call(f);

    // x axis
    g.append('g')
      .attr('class', 'axis x')
      .attr('transform', 'translate(0,' + height + ')')
	  .call(d3.axisBottom(x))
      .selectAll('text')
      .style('text-anchor', 'end')
      .attr('y', 1)
      .attr('dx', '-.8em')
      .attr('dy', '.15em')
      .attr('transform', 'rotate(-90)')
      .call(this.wrap, margin.bottom - 10);

    if (!this.showXAxis) {
      svg.selectAll('g.axis.x text').text('');
      svg.selectAll('g.axis.x g.tick').remove();
    } else {
      svg.selectAll('g.axis.x g.tick')
        .filter(function (d) { return d; })
        .attr('class', (d) => d.typetag)
        .on('click', (d) => this.focus.focusChanged(d));
    }

    g.append('g')
      .attr('class', 'axis y')
      .call(d3.axisLeft(y).ticks(null, '.0s'))
      .append('text')
			.attr('x', 20)
      .attr('y', y(y.ticks().pop()) - 12)
      .attr('dy', '0.22em')
      .text('Traffic (bytes)');

    // legend
    const leading = 26;
    if (this.showLegend) {
      const legend = g.append('g')
        .attr('class', 'legend')
        .attr('transform', 'translate(0,10)')
        .selectAll('g')
        .data(devices.slice().reverse())
        .enter()
        .append('g')
        .attr('transform', function (d, i) { return 'translate(0,' + i * leading + ')'; })
        .on('mouseenter', (d) => {
          this.hover.hoverChanged(d)
        })
        .on('mouseout', (d) => this.hover.hoverChanged(undefined))
        .on('click', (d) => this.focus.focusChanged(this.addOrRemove(d)));

      legend.append('rect')
        .attr('x', this.showTypesLegend ? width - 140 - 19 : width - 19)
        .attr('width', 19)
        .attr('height', 19)
        .attr('fill', z)
        .attr('opacity', (d) => {
          let highApp = this.highlightApp || this._hoveringApp;
          if (highApp) {
            return d === highApp ? 1.0: 0.2; 
          }
          return 1.0;
        });

      legend.append('text')
        .attr('x', this.showTypesLegend ? width - 140 - 24 : width - 24)
        .attr('y', 9.5)
        .attr('dy', '0.32em')
		.text((d) => this._ignoredApps.indexOf(d) === -1 ? this._devices[d].name || d : "Removed: " + d)
        .style("fill", d => this._ignoredApps.indexOf(d) === -1 ? 'rgba(0,0,0,1)' : 'rgba(200,0,0,1)')
        .attr('opacity', (d) => {
          let highApp = this.highlightApp || this._hoveringApp;
          if (highApp) {
            return d === highApp ? 1.0: 0.2; 
          }
          return 1.0;
        });

    }

    if (this._hoveringType) {
      this.setHoveringTypeHighlight(this._hoveringType)
    }
  }

	@HostListener('window:resize')
  	onResize() {
    	this.render();
  	}
}

