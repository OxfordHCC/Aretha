import { Component, OnInit, Input } from '@angular/core';

@Component({
  selector: 'app-content-b4',
  templateUrl: './content-b4.component.html',
  styleUrls: ['./content-b4.component.css']
})
export class ContentB4Component implements OnInit {

	@Input() stage: number;

  constructor() { }

  ngOnInit() {
  }

}
