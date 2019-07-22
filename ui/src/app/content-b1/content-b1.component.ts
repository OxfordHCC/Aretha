import { Component, OnInit, Input } from '@angular/core';

@Component({
  selector: 'app-content-b1',
  templateUrl: './content-b1.component.html',
  styleUrls: ['./content-b1.component.css']
})
export class ContentB1Component implements OnInit {

	@Input() stage: number;
 
  constructor() { }

  ngOnInit() {
  }

}
