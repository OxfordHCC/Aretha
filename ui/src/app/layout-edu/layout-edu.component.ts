import { Component, OnInit } from '@angular/core';
import { LoaderService, Example } from '../loader.service';

@Component({
  selector: 'app-layout-edu',
  templateUrl: './layout-edu.component.html',
  styleUrls: ['./layout-edu.component.scss']
})
export class LayoutEduComponent implements OnInit {

	content: string = "encryption";
	stage: number = 1;
	impacts: any;
	devices: any;
	geodata: any;
	text: string;

	constructor(private loader: LoaderService) { }

	ngOnInit() {
		this.loader.getContent()
			.then((ct) => {
				if (ct.length > 0) {
					let content = ct.sort((c1, c2) => Date.parse(c1[1]) - Date.parse(c2[1]));
					this.content = content[0][0]
			 		this.getExample();
				}
			});
	}
		
	//fetch data to use in examples and graphs
	getExample() {
		this.loader.getExample(this.content)
			.then((ex) => {
				this.devices = ex.devices;
				this.geodata = ex.geodata;
				this.impacts = ex.impacts;
				this.text = ex.text;
			});
	}

}
