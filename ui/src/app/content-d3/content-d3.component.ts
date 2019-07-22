import { Component, OnInit, Input } from '@angular/core';

@Component({
  selector: 'app-content-d3',
  templateUrl: './content-d3.component.html',
  styleUrls: ['./content-d3.component.css']
})
export class ContentD3Component implements OnInit {

	@Input() stage: number;

  constructor() { }

  ngOnInit() {
  }

}
