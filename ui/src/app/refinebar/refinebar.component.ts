import { Component, Input, OnInit, OnChanges, SimpleChanges, ViewChild, ElementRef, AfterViewInit, ViewEncapsulation, EventEmitter, Output, HostListener } from '@angular/core';
import { LoaderService, App2Hosts, String2String, CompanyInfo, CompanyDB, APIAppInfo } from '../loader.service';
import { AppUsage } from '../usagetable/usagetable.component';
import * as d3 from 'd3';
import * as _ from 'lodash';
import { HostUtilsService } from 'app/host-utils.service';
import { FocusService } from 'app/focus.service';
import { HoverService, HoverTarget } from "app/hover.service";
import { Http, HttpModule, Headers, URLSearchParams } from '@angular/http';

const LOCAL_IP_MASK_16 = "192.168.";
const LOCAL_IP_MASK_24 = "10.";

export interface AppImpact {
  appid: string;
  companyid: string;
  impact: number;
  companyName: string;
};
export interface AppDevice {
  mac : string;
  manufacturer: string;
  name: string;
}

@Component({
  selector: 'app-refinebar',
  templateUrl: './refinebar.component.html',
  styleUrls: ['./refinebar.component.scss'],
  encapsulation: ViewEncapsulation.None,
})
export class RefinebarComponent implements AfterViewInit, OnChanges {
  // refactor to get rid of -- 
  // app2hosts: App2Hosts;
  // host2companyid: String2String;
  // host2short: String2String;

  // still in use!
  companyid2info: CompanyDB;

  private usage: AppUsage[];
  private impacts: AppImpact[];
  private init: Promise<any>;
  lastMax = 0;
  // _timeSpan = 'd';
  // _byTime = 'yes';
  normaliseImpacts = false;

  apps: string[]; // keeps app ordering between renders

  // @ViewChild('thing') svg: ElementRef; // this gets a direct el reference to the svg element

  // incoming attribute
  // @Input('appusage') usage_in: AppUsage[];
  @Input() showModes = true;
  @Input() highlightApp: APIAppInfo;
  @Input() showLegend = true;
  @Input() showTypesLegend = false;
  @Input() showXAxis = true;

  @Input() scale = false;
  linear = false;
  vbox = { width: 700, height: 1024 };
  highlightColour = '#FF066A';

  _hoveringType: string;
  _companyHovering: CompanyInfo;
  _hoveringApp: string;
  _ignoredApps: string[];

  constructor(private httpM: HttpModule, 
    private http: Http, 
    private el: ElementRef,
    private loader: LoaderService,
    private hostutils: HostUtilsService,
    private focus: FocusService,
    private hover: HoverService) {
    this.init = Promise.all([
      this.loader.getCompanyInfo().then((ci) => this.companyid2info = ci),
    ]);

    this.getIoTData();
    
    hover.HoverChanged$.subscribe((target) => {
      // console.log('hover changed > ', target);
      if (target !== this._hoveringApp) {
        this._hoveringApp = target ? target as string : undefined;
        this.render();
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
    
    // (<any>window)._rb = this;
  }
  getSVGElement() {
    const nE: HTMLElement = this.el.nativeElement;
    return Array.from(nE.getElementsByTagName('svg'))[0];
  }

  // todo; move this out to loader
  getIoTData(): void {

    let this_ = this,
      refresh = () => {
        this_.loader.getIoTData().then( bundle => {
          // console.log('!@#ILJ!@#L@!J# got bundle ', bundle);
          this_.usage = bundle.usage;
          this_.impacts = bundle.impacts;
          this_.render();
        });
      },
      throttledRender = _.throttle(() => this.render(), 500),
      throttledRefresh = _.throttle(refresh, 1000);

    refresh();
    this.loader.asyncAppImpactChanges().subscribe({
      next(i: AppImpact[]) {  
        console.log('AppImpact CHANGE!', i.map(x => ''+[x.companyName, x.companyid, ''+x.impact].join('_')).join(' - '))
        if (this_.impacts) { 
          this_.impacts = this_.impacts.concat(i);
        }
        throttledRender();
      },
      error(err) { console.log("Listen error! ", err, err.message); },
      complete() { console.log("Listen complete"); }
    });

    this.loader.asyncGeoUpdateChanges().subscribe({
      next(a: any[]) {
        console.info("GOT GEO UPDATE, NOW FLUSHING AND STARTING OVER");        
        if (this_.impacts) { 
          throttledRefresh();
        }        
      }
    });

      //   this.http.get('http://localhost:4201/api/refine/15').toPromise().then(response2 => {
  //   this.usage = response2.json()["usage"]; // ah ha! 
  //   this.impacts = response2.json()["impacts"];
  //   var manDev = response2.json()["manDev"];
    
  //   this.impacts.forEach(function(impact){
  //     if (manDev[impact.appid] !== "unknown") {
  //       impact.appid = manDev[impact.appid];
  //     }
  //   });
  //   this.render()
  // });
}

  addOrRemove(newClick: string): string[] {
    // console.log(this._ignoredApps);
    if (this._ignoredApps.indexOf(newClick) > -1) {
      this._ignoredApps = this._ignoredApps.filter(obj => obj !== newClick);
    } else {
      this._ignoredApps.push(newClick);
    }
    // console.log(this._ignoredApps);
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


  // TODO 
  // this gets called when this.usage_in changes
  ngOnChanges(changes: SimpleChanges): void {
    if (!this.usage) { return; }
    this.init.then(() => {
      // if (!this.usage_in || !this.usage || !this.apps || this.apps.length !== this.usage_in.length) {
      //   delete this.apps;
      // }
      this.render();
    });
  }

  ngAfterViewInit(): void { this.init.then(() => this.render()); }

  private _getApp(appid: string): Promise<APIAppInfo> {
    return this.loader.getCachedAppInfo(appid) && Promise.resolve(this.loader.getCachedAppInfo(appid))
      || this.loader.getFullAppInfo(appid);
  }

  nonLinearity(v):number {
    return this.linear ? v : Math.max(0, 5000*Math.log(v) + 10);
  }

  // compileImpacts(usage: AppUsage[]): Promise<AppImpact[]> {
  //   // folds privacy impact in simply by doing a weighted sum over hosts
  //   // usage has to be in a standard unit: days, minutes
  //   // first, normalise usage

  //   const timebased = this.byTime === 'yes',
  //     total = _.reduce(usage, (tot, appusage): number => tot + (timebased ? appusage.mins : 1.0), 0),
  //     impacts = usage.map((u) => ({ ...u, impact: 
	// 	  this.nonLinearity((timebased ? u.mins : 1.0) / (1.0 * (this.normaliseImpacts ? total / 1000000 : 1.0)))
  //     }));

  //   return Promise.all(impacts.map((usg): Promise<AppImpact[]> => {

  //     return this._getApp(usg.appid).then(app => {
  //       const hosts = app && app.hosts;
	// 	  if (!hosts) { console.warn('No hosts found for app ', usg.appid); return Promise.resolve([]); }

  //       return Promise.all(hosts.map(host => this.hostutils.findCompany(host, app)))
  //         .then((companies: CompanyInfo[]) => _.uniq(companies.filter((company) => company !== undefined && company.typetag !== 'ignore')))
  //         .then((companies: CompanyInfo[]) => companies.map((company) => ({ appid: usg.appid, companyid: company.id, impact: usg.impact })));
  //     });
  //   })).then((nested_impacts: AppImpact[][]): AppImpact[] => _.flatten(nested_impacts));
  // }


  // // accessors for .byTime 
  // set byTime(val) {
  //   this.lastMax = 0;
  //   this._byTime = val;
  //   this.init.then(x => this.compileImpacts(this.usage).then(impacts => {
  //     this.render();
  //   }));
  // }

  // get byTime() { return this._byTime; }

  // // accessors for timeSpan
  // set timeSpan(val) {
  //   this._timeSpan = val;
  //   this.render();
  // }

  // get timeSpan() {return this._timeSpan; }

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
  mouseEnter() {
    // this.actlog.log('mouseenter', 'refinebar');
  }

  @HostListener('mouseleave')
  mouseLv() {
    // this.actlog.log('mouseleave', 'refinebar');
  }  

  setHoveringApp(s: string) {
    if (this._hoveringApp !== s) {
      this._hoveringApp = s;
      this.render();
    }
  }

  // 
  render() {
    // console.log(':: render usage:', this.usage && this.usage.length);
    const svgel = this.getSVGElement();

    if (!svgel || this.usage === undefined || this.impacts === undefined || this.usage.length === 0) { return; }

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

    let usage = this.usage.filter(obj => this._ignoredApps.indexOf(obj.appid) === -1 ),
      impacts = this.impacts.filter(obj => this._ignoredApps.indexOf(obj.appid) === -1 ),
      apps = _.uniq(impacts.map((x) => x.appid)),
      companies = _.uniq(impacts.map((x) => x.companyName)),
      get_impact = (cid, aid) => {
        const t = impacts.filter((imp) => imp.companyName === cid && imp.appid === aid);
        const reducer = (accumulator, currentValue) => accumulator + currentValue.impact;
        return t !== undefined ? t.reduce(reducer, 0) : 0;
      },
      by_company = companies.map((c) => ({
        company: c,
        total: apps.reduce((total, aid) => total += get_impact(c, aid), 0),
        ..._.fromPairs(apps.map((aid) => [aid, get_impact(c, aid)]))
      }));

    if (this.apps === undefined) {
      // sort apps
      apps.sort((a, b) => _.filter(usage, { appid: b })[0].mins - _.filter(usage, { appid: a })[0].mins);
      this.apps = apps;
    } else {
      apps = this.apps;
    }

    by_company.sort((c1, c2) => c2.total - c1.total); // apps.reduce((total, app) => total += c2[app], 0) - apps.reduce((total, app) => total += c1[app], 0));

    // re-order companies
    companies = by_company.map((bc) => bc.company);

    const stack = d3.stack(),
      out = stack.keys(apps)(by_company),
      margin = { top: 20, right: 20, bottom: this.showXAxis ? 160 : 0, left: 50 },
      width = width_svgel - margin.left - margin.right, // +svg.attr('width') - margin.left - margin.right,
      height = height_svgel - margin.top - margin.bottom; // +svg.attr('height') - margin.top - margin.bottom,

    if (height < 0 || width < 0) {
      console.error('height ', height, 'width ', width, 'exiting ');
      // return
    }
    
    let g = svg.append('g').attr('transform', 'translate(' + margin.left + ',' + margin.top + ')'),
      x = d3.scaleBand()
        .rangeRound([0, width]).paddingInner(0.05).align(0.1)
        .domain(companies),
      d3maxx = d3.max(by_company, function (d) { return d.total; }) || 0,
      ymaxx = this.lastMax = Math.max(this.lastMax, d3maxx),
      this_ = this;

    if (d3maxx < 0.7 * ymaxx) {
      ymaxx = 1.1 * d3maxx;
    }

    let y = d3.scaleLinear()
      .rangeRound([height, 0])
      .domain([0, ymaxx]).nice(),
      z = d3.scaleOrdinal(d3.schemeCategory20)
        .domain(apps);

    var self = this;

    g.selectAll('rect.back')
      .data(companies)
      .enter().append('rect')
      .attr('class', (company) => 'back ' + company) // + this.companyid2info.get(company).typetag)
      .attr('x', (company) => x(company))
      .attr('y', 0)
      .attr('height', height)
      .attr('width', x.bandwidth())
      .on('click', (d) => this.focus.focusChanged(d)) // this.focus.focusChanged(this.companyid2info.get(d)))
      .on('mouseenter', (d) => self.setHoveringApp(undefined)) // this._companyHover(this.companyid2info.get(d), true))
      .on("mouseleave", (d) => {return}); // this._companyHover(this.companyid2info.get(d), false));

    // main rects

    var self = this;
    
    const f = (selection, first, last) => {
      return selection.selectAll('rect')
        .data((d) => d)
        .enter().append('rect')
        .attr('class', 'bar')
        .attr('x', (d) => x(d.data.company))
        .attr('y', (d) => Number.isNaN(y(d[1])) ? 0 : y(d[1]))
        .attr('height', function (d) { return Number.isNaN(y(d[0]) - y(d[1])) ? 0 : y(d[0]) - y(d[1]); })
        .attr('width', x.bandwidth())
        // .on('click', (d) => this.focus.focusChanged(this.companyid2info.get(d.data.company)))
        .on('click', function (d) {
          self.focus.focusChanged(self.addOrRemove(this.parentElement.__data__.key))
        })
        .on('mouseleave', function (d) {
          // console.log("Leave" + d );
          // self.setHoveringApp(undefined)
          this_.hover.hoverChanged(undefined);
        })
        .on('mouseenter', function (d) {
          if (this.parentElement && this.parentElement.__data__) {
            // unsure why this is dying
            // console.log("Enter" + this.parentElement.__data__.key );
            // self.setHoveringApp(this.parentElement.__data__.key);
            this_.hover.hoverChanged(this.parentElement.__data__.key);
          } 
        });
    };

    g.append('g')
      .selectAll('g')
      .data(d3.stack().keys(apps)(by_company))
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
      .call(d3.axisLeft(y).ticks(null, 's'))
      .append('text')
      .attr('x', 20)
      .attr('y', y(y.ticks().pop()) - 12)
      .attr('dy', '0.22em')
      .text('Impact (mB)');

    // legend
    const leading = 26;
    /*
    if (this.showTypesLegend) {
      const ctypes = ['advertising', 'analytics', 'app', 'other'],
        ctypeslegend = g.append('g')
          .attr('class', 'ctypelegend')
          .attr('transform', 'translate(0,10)')
          .selectAll('g')
          .data(ctypes)
          .enter().append('g')
          .attr('class', (d) => d)
          .on('mouseenter', (d) => this.setHoveringTypeHighlight(d))
          .on("mouseleave", (d) => this.setHoveringTypeHighlight(undefined))
          .attr('transform', (d, i) => 'translate(0,' + i * leading + ')');

      ctypeslegend.append('rect')
        .attr('x', width - 19)
        .attr('width', 19)
        .attr('height', 19)
        .attr('class', (d) => 'legend ' + d);
      ctypeslegend.append('text')
        .attr('x', width - 24)
        .attr('y', 9.5)
        .attr('dy', '0.32em')
        .text((d) => d);
    } */
    if (this.showLegend) {
      const legend = g.append('g')
        .attr('class', 'legend')
        .attr('transform', 'translate(0,10)')
        .selectAll('g')
        .data(apps.slice().reverse())
        .enter()
        .append('g')
        .attr('transform', function (d, i) { return 'translate(0,' + i * leading + ')'; })
        .on('mouseenter', (d) => {
          // console.log(d);
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
        .text((d) => this._ignoredApps.indexOf(d) === -1 ? d : "Removed: " + d)
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
    // call our matchHeight function here
    this.render();
  }
}


/* 
dead ponies
    const satBand = (name, domain, h, l, slow, shigh) => {
      return (appkey) => {
        let ki = domain.indexOf(appkey),
          bandwidth = (shigh - slow) / domain.length,
          starget = slow + ki * bandwidth,
          targetc = d3.hsl(h, starget, starget);
        // console.log(`satBand [${name}]:${appkey} - ki:${ki}, bw:${bandwidth}, slow:${slow}, shigh:${shigh}, ${starget}`, targetc);
        return targetc;
      };
    },
      catcolours = { // .interpolate(d3.interpolateHsl).
        'advertising': satBand('adv', apps, 0.2, 0.6, 0.2, 1),
        'app': satBand('app', apps, 80, 0.6, 0.2, 1),
        'analytics': satBand('analytics', apps, 30, 0.4, 0.2, 1),
        'usage': satBand('usage', apps, 30, 0.6, 0.2, 1),
        'other': satBand('other', apps, 0.5, 0.6, 0.2, 1)
      },
      getColor = (app: string, company: string): string => {
        if (app === undefined) {
          app = apps[0]; // apps.length - 1];
        }
        let companyInfo = this.companyid2info.get(company);
        if (companyInfo && companyInfo.typetag && catcolours[companyInfo.typetag]) {
          return catcolours[companyInfo.typetag](app);
        }
        return catcolours.other(app);
      };
      */
