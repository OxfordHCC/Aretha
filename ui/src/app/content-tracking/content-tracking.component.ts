import { Component, OnInit, Input } from '@angular/core';
import { FormControl } from "@angular/forms";
import { LoaderService } from '../loader.service';
import {Router} from '@angular/router';

@Component({
  selector: 'app-content-tracking',
  templateUrl: './content-tracking.component.html',
  styleUrls: ['./content-tracking.component.css']
})
export class ContentTrackingComponent implements OnInit {

	@Input() stage: number;
	max: number = 4 + 1; //+1 for the attention check at the end
	done: boolean = false;
	answerText: string;
	tipText: string;

	constructor(
		private loader: LoaderService,
		private router: Router
	) { }

	ngOnInit() {
	}

	prev() { if (this.stage > 1) { this.stage--; } }

	next() {
		if (this.stage < this.max) { this.stage++; }
		else {
			this.loader.setContent('tracking')
				.then((x) => this.router.navigate(['/timeseries']));
		}
	}

	answer(question:number) {
		if (question === 1) {
			this.tipText = "Correct! Trackers build complex models about you that can infer personality and behavioural traits.";
			this.done = true;
		}
		else { 
			this.done = false;
			if (question === 2) { this.tipText = "Not quite. The models that are built by modern trackers and advertisers are more complex than the simple rules in this question."; } 
			else { this.tipText = "Not quite. Check the content on the previous screens again."; }
		}
	}

}
