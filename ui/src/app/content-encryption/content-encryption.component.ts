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
	max: number = 3 + 2; // +2 for the intial and final text fields
	preResponse: string;
	postResponse: string;

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
			this.loader.setContent('encryption', this.preResponse, this.postResponse)
				.then((x) => this.router.navigate(['/timeseries']));
		}
	}
}
