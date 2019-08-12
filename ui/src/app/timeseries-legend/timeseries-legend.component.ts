import { Component, OnInit, Input, OnChanges, Output, EventEmitter } from '@angular/core';

@Component({
  selector: 'app-timeseries-legend',
  templateUrl: './timeseries-legend.component.html',
  styleUrls: ['./timeseries-legend.component.scss']
})
export class TimeseriesLegendComponent implements OnInit, OnChanges {

  @Input() els: string[];
  @Input() categories: { [el:string]: string };
  @Input() info: { [el:string]: any };  
  @Input() title: string;
  @Input() colours: { [el:string]: string }
  @Input() hovering: string;
  @Input() namemap: { [el:string]: string }

  by_cat : { [el:string]: string };
  allcats: string[];

  @Output() hovered = new EventEmitter<string>();
  @Output() clicked = new EventEmitter<string>();
  catstyles: {};

  constructor() { }

  ngOnInit() {
  }

  mouseEnter(el) {
    console.info("mouse enter ", el);
    this.hovered.emit(el);
  }
  mouseLeave(el) {
    console.info("mouse leave ", el);
    this.hovered.emit(undefined);
  }
  mouseClicked(el) { 
    console.info('clicked');
    this.clicked.emit(el);
  }

  ngOnChanges() { 
    if (this.els) { 
      // update by_cat
      this.by_cat = this.els.reduce((obj, x) => { 
        let cat = this.categories && this.categories[x];
        if (!cat) { 
          cat = "";
          if (this.categories) { cat = "Other"; } 
      }
        obj[cat] = (obj[cat] || []).concat([x])
        return obj;
      }, {});
      this.allcats = Object.keys(this.by_cat);
      this.allcats.sort( (x,y) => this.by_cat[x].length - this.by_cat[y].length );
      // this.stylecats = this.els.reduce((obj, el) => {
      //   // const key = this.categories && this.categories[el] || "Other";
      //   obj[el] = {
      //     el: true,
      //     hovering: this.hovering && el === this.hovering,
      //     hoveringnot: this.hovering && el !== this.hovering,
      //     [this.categories && this.categories[el] || "Other"]: true
      //   };
      //   return obj;
      // }, {});

      this.catstyles = this.allcats.reduce((obj, cat) => {
        obj[cat] = { category: true, foo: true, [cat]: true } ; 
        return obj;
      }, {});
    }
  }
}
