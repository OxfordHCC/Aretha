import { Component, OnInit, Input } from '@angular/core';
import { FormControl } from "@angular/forms";
import { LoaderService } from '../loader.service';
import {Router} from '@angular/router';

@Component({
  selector: 'app-content-breach',
  templateUrl: './content-breach.component.html',
  styleUrls: ['./content-breach.component.css']
})
export class ContentBreachComponent implements OnInit {

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
			this.loader.setContent('breach')
				.then((x) => this.router.navigate(['/timeseries']));
		}
	}

	answer(question:number) {
		if (question === 2) {
			this.tipText = "Correct! As with burglaries, while good security can minimise the chance of a breach there is no way to prevent them completely. Employing good security practices, like choosing different passwords for each website, is the best way to protect yourself.";
			this.done = true;
		}
		else { 
			this.done = false;
			if (question === 1) { this.tipText = "Not quite. As with burglaries, while good security can minimise the chance of a breach there is no way to prevent them completely. Employing good security practices, like choosing different passwords for each website, is the best way to protect yourself.";}
			else { this.tipText = "Not quite. The quality of your password has no bearing on how likely a company is to be the victim of a data breach."; }
		}
	}

}
