import { Component, OnInit, Input } from '@angular/core';

@Component({
  selector: 'app-content-b3',
  templateUrl: './content-b3.component.html',
  styleUrls: ['./content-b3.component.css']
})
export class ContentB3Component implements OnInit {

	@Input() stage: number;

  constructor() { }

  ngOnInit() {
  }

}
