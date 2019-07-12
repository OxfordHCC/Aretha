import { Component, OnInit } from '@angular/core';
import { LoaderService } from '../loader.service';
import * as _ from 'lodash';
import {ActivityLogService} from "../activity-log.service";

@Component({
	selector: 'app-company-info',
	templateUrl: './company-info.component.html',
	styleUrls: ['./company-info.component.css']
})
export class CompanyInfoComponent implements OnInit {

	chosen: string;
	companies: string[];
	description: string;

	constructor(
	  private loader: LoaderService,
    private actlog: ActivityLogService
  ) { }

	ngOnInit() {
		this.loader.getGeodata().then((gd) => {
			this.companies = _.uniq(gd.geodata.map((x) => x.company_name)).sort();
		});
	}

	getDesc() {
		this.loader.getDescription(this.chosen).then((desc) => {
			for (let key in desc.query.pages) {
        let raw = desc.query.pages[key].extract
        raw = raw.split('.');
        this.description = raw[0] + '.' + raw[1] + '.' + raw[2] + '.' + raw[3] + '.' + raw[4] + '.';
        break;
      }
		})
		.catch((e) => {
			// TODO try again after culling the last word (+ commas)
			this.description = "Sorry, we can't find any information on " + this.chosen + ".";
		});
		this.actlog.log("company-info", this.chosen)
	}
}
