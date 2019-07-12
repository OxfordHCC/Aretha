import { Component, OnInit } from '@angular/core';
import { LoaderService, Device } from 'app/loader.service'
import {ActivityLogService} from "../activity-log.service";

@Component({
	selector: 'app-name-device',
	templateUrl: './name-device.component.html',
	styleUrls: ['./name-device.component.css']
})
export class NameDeviceComponent implements OnInit {

 	devices: Device[] = [];
	chosen: string;
	newName: string;

	constructor(
	  private loader: LoaderService,
    private actlog: ActivityLogService
  ) {
		this.getData();
	}

	ngOnInit() {
	}

	rename() {
		this.loader.setDevice(this.chosen, this.newName)
      .then(() => this.actlog.log("rename-device", this.chosen + " to " + this.newName))
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
