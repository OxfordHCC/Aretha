import { Component, OnInit } from '@angular/core';
import { LoaderService } from '../loader.service';

@Component({
	selector: 'app-redaction',
	templateUrl: './redaction.component.html',
	styleUrls: ['./redaction.component.css']
})
export class RedactionComponent implements OnInit {

	records = [];

	constructor(private loader: LoaderService) { }

	ngOnInit() {
		this.loader.getRedact().then((data) => {
			data.map((x) => {
				this.records.push(x[0]);
			});
		});

	}

	redact(company: string) {
		console.log(company);
		this.records = this.records.filter((x) => x !== company);
		this.loader.setRedact(company);
	}

}
