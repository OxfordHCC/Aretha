import { Component, OnInit, Input } from '@angular/core';

@Component({
  selector: 'app-content-d2',
  templateUrl: './content-d2.component.html',
  styleUrls: ['./content-d2.component.css']
})
export class ContentD2Component implements OnInit {

	@Input() stage: number;

  constructor() { }

  ngOnInit() {
  }

}
