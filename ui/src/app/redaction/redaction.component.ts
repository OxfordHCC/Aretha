import { Component, OnInit } from '@angular/core';
import { LoaderService } from '../loader.service';

@Component({
	selector: 'app-redaction',
	templateUrl: './redaction.component.html',
	styleUrls: ['./redaction.component.css']
})
export class RedactionComponent implements OnInit {

	records = [];
	fw_on = false;

	constructor(private loader: LoaderService) { }

	ngOnInit() {
		this.loader.getRedact().then((data) => {
			data.map((x) => {
				this.records.push(x[0]);
			});
			this.records.sort();
		});

		this.loader.getRules().then((x) => {
      this.fw_on = x.enabled;
    })

	}

	redact(company: string) {
		if(confirm("Are you sure to delete all records of" + company + "?")) {
			this.records = this.records.filter((x) => x !== company);
			this.loader.setRedact(company);
		}
	}

}
