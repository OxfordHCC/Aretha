import { Component, OnInit, Input } from '@angular/core';

@Component({
  selector: 'app-content-d4',
  templateUrl: './content-d4.component.html',
  styleUrls: ['./content-d4.component.css']
})
export class ContentD4Component implements OnInit {

	@Input() stage: number;

  constructor() { }

  ngOnInit() {
  }

}
