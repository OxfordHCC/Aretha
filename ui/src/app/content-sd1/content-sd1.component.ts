import { Component, OnInit, Input } from '@angular/core';

@Component({
  selector: 'app-content-sd1',
  templateUrl: './content-sd1.component.html',
  styleUrls: ['./content-sd1.component.css']
})
export class ContentSd1Component implements OnInit {

	@Input() stage: number;

  constructor() { }

  ngOnInit() {
  }

}
