import { Component, OnInit } from '@angular/core';
import { LoaderService, Device } from 'app/loader.service'

@Component({
	selector: 'app-namedevice',
	templateUrl: './namedevice.component.html',
	styleUrls: ['./namedevice.component.css']
})
export class NamedeviceComponent implements OnInit {

 	devices: Device[] = [];
	chosen: string;
	newName: string;

	constructor(private loader: LoaderService) { 
		this.getData();
	}

	ngOnInit() {
	}

	rename() {
		this.loader.setDevice(this.chosen, this.newName)
			.then(() => this.getData());
	}

	getData() {
		this.devices = [];
		this.loader.getDevices().then((x) => {
			for (const key of Object.keys(x.devices)) {
				this.devices.push({
					"mac": key,
					"manufacturer": x.devices[key].manufacturer,
					"name": x.devices[key].name
				});
			}
		});
	}
}
