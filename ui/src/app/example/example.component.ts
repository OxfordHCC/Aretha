import { Component, OnInit, Input } from '@angular/core';
import { LoaderService, Example } from '../loader.service';


@Component({
  selector: 'app-example',
  templateUrl: './example.component.html',
  styleUrls: ['./example.component.css']
})
export class ExampleComponent implements OnInit {

	@Input() text: string;

  	constructor() { }; 

	ngOnInit() {
	}

}
