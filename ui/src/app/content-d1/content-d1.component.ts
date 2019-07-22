import { Component, OnInit, Input } from '@angular/core';

@Component({
  selector: 'app-content-d1',
  templateUrl: './content-d1.component.html',
  styleUrls: ['./content-d1.component.css']
})
export class ContentD1Component implements OnInit {

	@Input() stage: number;

  constructor() { }

  ngOnInit() {
  }

}
