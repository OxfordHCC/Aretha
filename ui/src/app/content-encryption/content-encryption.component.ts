import { Component, OnInit, Input } from '@angular/core';

@Component({
  selector: 'app-content-encryption',
  templateUrl: './content-encryption.component.html',
  styleUrls: ['./content-encryption.component.css']
})
export class ContentEncryptionComponent implements OnInit {

	@Input() stage: number;
	max: number = 2;

	constructor() { }

	ngOnInit() {
	}

	prev() {
		console.log("stage down");
		this.stage--;
	}

	next() {
		console.log("stage up");
		this.stage++;
	}

}
