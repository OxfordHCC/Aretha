import { Component, OnInit, Input } from '@angular/core';

@Component({
  selector: 'app-content-b2',
  templateUrl: './content-b2.component.html',
  styleUrls: ['./content-b2.component.css']
})
export class ContentB2Component implements OnInit {

	@Input() stage: number;

  constructor() { }

  ngOnInit() {
  }

}
