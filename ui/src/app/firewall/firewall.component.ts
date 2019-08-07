import { Component, OnInit } from '@angular/core';
import {Device, LoaderService} from "../loader.service";
import {ActivityLogService} from "../activity-log.service";

@Component({
	selector: 'app-firewall',
	templateUrl: './firewall.component.html',
	styleUrls: ['./firewall.component.css']
})
export class FirewallComponent implements OnInit {

  chosen_d: string;
  chosen_c: string;
  records: any;

  devices: Device[];
  companies: string[];

  constructor(
    private loader: LoaderService,
    private actlog: ActivityLogService
  ) {
    this.getData();
  }

  ngOnInit() {
  }

  addRule() {
    this.loader.setRule(this.chosen_d, this.chosen_c)
      .then(() => this.actlog.log("add-rule", this.chosen_d + " : " + this.chosen_c))
      .then(() => this.getData());
  }

  removeRule(company, mac, device) {
    this.loader.removeRule(mac, company)
      .then(() => this.actlog.log("remove-rule", device + " : " + company))
      .then(() => this.getData());
  }

  getData() {
    this.devices = [];
    this.companies = [];
    this.records = [];

    this.loader.getDevices().then((x) => {
      for (const key of Object.keys(x.devices)) {
        this.devices.push({
          "mac": key,
          "manufacturer": x.devices[key].manufacturer,
          "name": x.devices[key].name
        });
      }
    });

    this.loader.getGeodata().then((x) => {
      for (const key of Object.keys(x.geodata)) {
        if (this.companies.indexOf(x.geodata[key].company_name) === -1) {
          this.companies.push(x.geodata[key].company_name);
        }
      }
      this.companies.sort();
    });

    this.loader.getRules().then((x) => {
      x.rules.forEach((rule) => {
        this.records.push({
          "id": rule[0],
          "mac": rule[1],
          "device": rule[2],
          "company": rule[3]
        })
      });
    });
  }
}
