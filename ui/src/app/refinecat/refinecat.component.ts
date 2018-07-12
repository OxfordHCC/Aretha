import { Component, Input, OnInit, OnChanges, SimpleChanges, ViewChild, ElementRef, AfterViewInit, ViewEncapsulation, EventEmitter, Output, HostListener } from '@angular/core';
import { LoaderService, App2Hosts, String2String, CompanyInfo, CompanyDB, APIAppInfo } from '../loader.service';
import { AppUsage } from '../usagetable/usagetable.component';
import * as d3 from 'd3';
import * as _ from 'lodash';
import { HostUtilsService } from 'app/host-utils.service';
import { FocusService } from 'app/focus.service';
import { HoverService, HoverTarget } from "app/hover.service";
import * as moment from 'moment';

interface AppImpactCat {
  appid: string;
  companyid?: string;
  impact: number;
  category?: string;
};

@Component({
  selector: 'app-refinecat',
  templateUrl: './refinecat.component.html',
  styleUrls: ['./refinecat.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class RefinecatComponent {
  impacts: AppImpactCat[];

  // still in use!
  companyid2info: CompanyDB;

  private usage: AppUsage[];
  private init: Promise<any>;
  lastMax = 0;
  _byTime = 'yes';
  normaliseImpacts = false;

  apps: string[]; // keeps app ordering between renders

  // @ViewChild('thing') svg: ElementRef; // this gets a direct el reference to the svg element

  // incoming attribute
  @Input('appusage') usage_in: AppUsage[];
  @Input() showModes = true;
  @Input() highlightApp: APIAppInfo;
  @Input() showLegend = true;
  @Input() showTypesLegend = true;
  @Input() showXAxis = true;

  @Input() scale = false;
  vbox = { width: 700, height: 1024 };
  highlightColour = '#FF066A';

  _companyHovering: CompanyInfo;
  _hoveringApp: APIAppInfo;

  constructor(private el: ElementRef,
    private loader: LoaderService,
    private hostutils: HostUtilsService,
    private focus: FocusService,
    private hover: HoverService) {
    this.init = Promise.all([
      this.loader.getCompanyInfo().then((ci) => this.companyid2info = ci),
    ]);
    hover.HoverChanged$.subscribe((target) => {
        // console.log('hover changed > ', target);
        if (target !== this._hoveringApp) {
          this._hoveringApp = target ? target as APIAppInfo : undefined;
          this.getDataAndRender()
        }
    });
    (<any>window)._rb = this;
    
    this.getDataAndRender()
    
  }

getDataAndRender() {
    var data = [{'value': 1380854103662, 'col': true},{'value': 1363641921283, col: false}];
    var brushEnabled = false;
    this.render('', 'timeseries'.toString(), data, brushEnabled);
}

getSVGElement() {
    const nE: HTMLElement = this.el.nativeElement;
    return Array.from(nE.getElementsByTagName('svg'))[0];
}
  
lessThanDay(d) {
    return (d === "hours" || d === "minutes" || d === "seconds") ? true : false;
};

ngAfterViewInit(): void { this.init.then(() => {
    this.getDataAndRender()
}) ; }

ngOnChanges(changes: SimpleChanges): void {
    this.getDataAndRender()
}

getDate(d) {
    var date = moment(d);
    date.hour(1);
    date.minute(0);
    date.second(0);
    return date.valueOf();
};

getTime(d) {
    var date = moment(d);
    date.date(1);
    date.month(0);
    date.year(2012);
    return date.valueOf();
};

/* 
  Given a list of time stamps, compute the minimum and maxium dates. Return a padded
  version of the min and max dates based on the temporal distance between them.
*/
timeRangePad(dates) {
    var minDate, maxDate, pad;
    if (dates.length > 1) {
        minDate = moment(_.min(dates));
        maxDate = moment(_.max(dates));
        pad = this.getDatePadding(minDate, maxDate);
        minDate.subtract(1, pad);
        maxDate.add(1, pad);
    } else {
        minDate = moment(dates[0]).subtract(1, 'hour');
        maxDate = moment(dates[0]).add(1, 'hour');
    }
    return {
        'minDate': minDate,
        'maxDate': maxDate,
        'pad': pad
    };
};

getDatePadding(minDate, maxDate) {
    if (maxDate.diff(minDate, 'years') > 0)
        return 'months';
    else if (maxDate.diff(minDate, 'months') > 0)
        return 'days';
    else if (maxDate.diff(minDate, 'days') > 0)
        return 'days';
    else if (maxDate.diff(minDate, 'hours') > 0)
        return 'hours';
    else if (maxDate.diff(minDate, 'minutes') > 0)
        return 'minutes';
    else
        return 'seconds';
};

  render(classd, spaced, data, enableBrush) {
        
    var padding = this.timeRangePad(data.map(val => val.value));

    var margin = {
        top: 10,
        right: 25,
        bottom: 15,
        left: 30
    }
    var svgel = this.getSVGElement();
    console.log(svgel);
    if (!svgel) { return; }

    var rect = svgel.getBoundingClientRect(),
      width_svgel = Math.round(rect.width - 5),
      height_svgel = Math.round(rect.height - 5),
      svg = d3.select(svgel)

    svg.selectAll('*').remove();
    
    var width = width_svgel - 50;
    
    var height = (this.lessThanDay(padding.pad)) ? (height_svgel - margin.top - margin.bottom) : (height_svgel - margin.top - margin.bottom);

    console.log(width);
    console.log(height);

    var x = d3.scaleLinear().range([0 + margin.right, width - margin.left]),
        y = d3.scaleLinear().range([margin.top, height - margin.bottom - margin.top]);

    var ticks = width > 800 ? 8 : 4;

    x.domain(d3.extent([padding.minDate, padding.maxDate]));

    var xFormat, yFormat;
    if (this.lessThanDay(padding.pad)) {
        xFormat = "%H:%M";
        yFormat = "%m/%d/%y";
        y.domain(d3.extent([padding.minDate]));
    } else {
        xFormat = "%m/%d/%y";
        yFormat = "%H:%M";
        var start = new Date(2012, 0, 1, 0, 0, 0, 0).getTime();
        var stop = new Date(2012, 0, 1, 23, 59, 59, 59).getTime();
        y.domain(d3.extent([start, stop]));
    }

    var xAxis = d3.axisBottom().scale(x)
        .ticks(ticks)
        .tickSize(-height, 0)
        .tickFormat(d3.timeFormat(xFormat));

    var yAxis = d3.axisLeft().scale(y)
        .ticks(6)
        .tickSize(-width + margin.right, 0)
        .tickFormat(d3.timeFormat(yFormat));

    svg.attr("width", width + margin.left + margin.right)
       .attr("height", height + margin.top + margin.bottom);

    var context = svg.append("g")
        .attr("class", "context")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    context.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(" + margin.left + "," + (margin.top + (height - margin.bottom)) + ")")
        .call(xAxis);

    context.append("g")
        .attr("class", "y axis")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")")
        .call(yAxis);

    var circles = context.append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")")

    circles.selectAll(".circ")
        .data(data)
        .enter().append("circle")
        .attr("class", "circ")
        .style("fill", d => {
            return d.col ? "white" : "black"
        })
        .attr("cx", d => {
            var res = ((this.lessThanDay(padding.pad)) ? x(d.value) : x(this.getDate(d.value)));
            return res;
        })
        .attr("cy",(d, i) => {
            return (this.lessThanDay(padding.pad)) ? y(this.getDate(d.value)) : y(this.getTime(d.value));
        })
        .attr("r", 9)
        .on("click", function(d) {
            console.log(new Date(d.value));
        })
        .append("svg:title")
        .text(function(d) { return d.col; });

    
    // ----------------------------------------- Legend ---------------------------------------------
    /*
    const leading = 26;
    const legend = svg.append('g')
        .attr('class', 'legend')
        .attr('transform', 'translate(0,10)')
        .selectAll('g')
        .data(["White", "Black"])
        .enter()
        .append('g')
        .attr('transform', function (d, i) { return 'translate(0,' + i * leading + ')'; })
        .on('mouseenter', (d) => this.hover.hoverChanged(this.loader.getCachedAppInfo(d)))
        .on('mouseout', (d) => this.hover.hoverChanged(undefined))
        .on('click', (d) => this.focus.focusChanged(this.loader.getCachedAppInfo(d)));

      legend.append('rect')
        .attr('x', this.showTypesLegend ? width - 140 - 19 : width - 19)
        .attr('width', 19)
        .attr('height', 19)
        

      legend.append('text')
        .attr('x', this.showTypesLegend ? width - 140 - 24 : width - 24)
        .attr('y', 9.5)
        .attr('dy', '0.32em')
        .text((d) => {return d})

     */
    }
    @HostListener('window:resize')
    onResize() {
    // call our matchHeight function here
    this.getDataAndRender()
  }
}