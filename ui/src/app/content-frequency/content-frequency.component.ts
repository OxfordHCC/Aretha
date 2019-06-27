import { Component, OnInit, Input } from '@angular/core';
import { FormControl } from "@angular/forms";
import { LoaderService } from '../loader.service';
import {Router} from '@angular/router';

@Component({
  selector: 'app-content-frequency',
  templateUrl: './content-frequency.component.html',
  styleUrls: ['./content-frequency.component.css']
})
export class ContentFrequencyComponent implements OnInit {

	@Input() stage: number;
	max: number = 1 + 1; //+1 for the attention check at the end
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
			this.loader.setContent('frequency')
				.then((x) => this.router.navigate(['/timeseries']));
		}
	}

	answer(question:number) {
		if (question === 1) {
			this.tipText = "Correct! Smart devices send data back to their manufacturers and other companies for analytics, advertising, or just to say that they're still plugged in - this happens 24 hours a day.";
			this.done = true;
		}
		else { 
			this.done = false;
			if (question === 2) { this.tipText = "Not quite. Devices only need to get your permission once in order to collect and process data about you. This normally occurs when you install the accompanying app on your phone."; } 
			else { this.tipText = "Not quite. Devices often want to send other kinds of data for tracking and analytics purposes - this can happen at any time, not just when you're using them."; }
		}
	}

}
