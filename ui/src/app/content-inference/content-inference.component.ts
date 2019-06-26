import { Component, OnInit, Input } from '@angular/core';
import { FormControl } from "@angular/forms";
import { LoaderService } from '../loader.service';
import {Router} from '@angular/router';

@Component({
  selector: 'app-content-inference',
  templateUrl: './content-inference.component.html',
  styleUrls: ['./content-inference.component.css']
})
export class ContentInferenceComponent implements OnInit {

	@Input() stage: number;
	max: number = 3 + 1; //+1 for the attention check at the end
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
			this.loader.setContent('inference')
				.then((x) => this.router.navigate(['/timeseries']));
		}
	}

	answer(question:number) {
		if (question === 3) {
			this.tipText = "Correct! The business models of many major companies depend on being able to collate data about users from multiple sources.";
			this.done = true;
		}
		else { 
			this.done = false;
			if (question === 2) { this.tipText = "Not quite. European data protection laws only prevent companies from inferring certain types of sensitve information without your consent."; } 
			else { this.tipText = "Not quite. Check the content on the previous screens again."; }
		}
	}

}
