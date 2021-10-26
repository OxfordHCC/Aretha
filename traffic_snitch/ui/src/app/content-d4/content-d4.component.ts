import { Component, OnInit, Input } from '@angular/core';
import { LoaderService } from '../loader.service';
import {Router} from '@angular/router';
import {ActivityLogService} from "../activity-log.service";

@Component({
  selector: 'app-content-d4',
  templateUrl: './content-d4.component.html',
  styleUrls: ['./content-d4.component.css']
})
export class ContentD4Component implements OnInit {

	@Input() stage: number;
	max: number = 5;
	keyword = "D4";
	preResponse: string = "";
	postResponse: string = "";

	constructor(
		private loader: LoaderService,
		private router: Router,
    private actlog: ActivityLogService
	) { }

	ngOnInit() {
	}

	prev() { if (this.stage > 1) { this.stage--; } }

	next() {
		if (this.stage < this.max) {
			this.stage++;
     	 	this.actlog.log("edu-advance", this.keyword + " " + this.stage)
    	} else {
			this.loader.setContent(this.keyword, this.preResponse, this.postResponse)
				.then((x) => this.router.navigate(['/timeseries']));
      		this.actlog.log("edu-complete", this.keyword);
    	}
	}
}
