import { Component, OnInit, Input } from '@angular/core';
import { LoaderService } from '../loader.service';
import {Router} from '@angular/router';
import {ActivityLogService} from "../activity-log.service";

@Component({
  selector: 'app-content-b2',
  templateUrl: './content-b2.component.html',
  styleUrls: ['./content-b2.component.css']
})
export class ContentB2Component implements OnInit {

	@Input() stage: number;
	max: number = 4;
	keyword = "B2";
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
