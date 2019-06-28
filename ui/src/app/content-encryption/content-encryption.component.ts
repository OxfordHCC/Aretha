import { Component, OnInit, Input } from '@angular/core';
import { FormControl } from "@angular/forms";
import { LoaderService } from '../loader.service';
import {Router} from '@angular/router';

@Component({
  selector: 'app-content-encryption',
  templateUrl: './content-encryption.component.html',
  styleUrls: ['./content-encryption.component.css']
})
export class ContentEncryptionComponent implements OnInit {

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
			this.loader.setContent('encryption')
				.then((x) => this.router.navigate(['/timeseries']));
		}
	}

	answer(question:number) {
		if (question === 2) {
			this.tipText = "Correct! Encryption only stops other people from reading data you sent to/from a website.";
			this.done = true;
		}
		else { 
			this.done = false;
			if (question === 1) { this.tipText = "Not quite. Encrypted data still needs to be labelled with where it's going, which will give away what websites you're visiting."; } 
			else { this.tipText = "Not quite. Check the content on the previous screens again."; }
		}
	}

}
