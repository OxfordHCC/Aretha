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

	explanations = [
		["Akamai International B.V.", "Akamai Technologies, Inc. is an American content delivery network (CDN) and cloud service provider headquartered in Cambridge, Massachusetts, in the United States. Akamai's content delivery network is one of the world's largest distributed computing platforms, responsible for serving between 15% and 30% of all web traffic. The company operates a network of servers around the world and rents out capacity on these servers to customers who want their websites to work faster by distributing content from locations close to the user. When a user navigates to the URL of an Akamai customer, their browser is redirected to one of Akamai's copies of the website."],
		["Automattic, Inc", "Automattic Inc. is a web development corporation founded in August 2005. It is most notable for WordPress.com (a free blogging service), as well as its contributions to WordPress (open source blogging software). The company's name is a play on its founder's first name, Matt."],
		["Cloudflare, Inc.", "Cloudflare, Inc. is a U.S. company that provides content delivery network services, DDoS mitigation, Internet security and distributed domain name server services. Cloudflare's services sit between the visitor and the Cloudflare user's hosting provider, acting as a reverse proxy for websites. Cloudflare's headquarters are in San Francisco, California, with additional offices in Lisbon, London, Singapore, Munich, San Jose, Champaign, Austin, New York and Washington, D.C."],
		["DigitalOcean, LLC", "DigitalOcean, Inc. is an American cloud infrastructure provider headquartered in New York City with data centers worldwide. DigitalOcean provides developers cloud services that help to deploy and scale applications that run simultaneously on multiple computers. As of January 2018, DigitalOcean was the third-largest hosting company in the world in terms of web-facing computers."],
		["Incapsula Inc", "Imperva Incapsula is a cloud-based application delivery platform. It uses a global content delivery network to provide web application security, DDoS mitigation, content caching, application delivery, load balancing and failover services."],
		["Jisc Services Limited", "Jisc (formerly the Joint Information Systems Committee) is a United Kingdom not-for-profit company whose role is to support post-16 and higher education, and research, by providing relevant and useful advice, digital resources and network and technology services, while researching and developing new technologies and ways of working. It is funded by a combination of the UK further and higher education funding bodies, and individual higher education institutions."],
		["Linode, LLC", "Linode, LLC is an American privately-owned company (based in Philadelphia, Pennsylvania, United States) providing virtual private servers. Linode offers multiple products and services for its clients. Its flagship products are cloud-hosting services with multiple packages at different price points."],
		["MCI Communications Servic", "MCI Communications Corp. was an American telecommunications company that was instrumental in legal and regulatory changes that led to the breakup of the AT&T monopoly of American telephony and ushered in the competitive long-distance telephone industry. It was headquartered in Washington, D.C. Founded in 1963, it grew to be the second-largest long-distance provider in the U.S. It was purchased by WorldCom in 1998 and became MCI WorldCom, with the name afterwards being shortened to WorldCom in 2000. WorldCom's financial scandals and bankruptcy led that company to change its name in 2003 to MCI Inc."],
		["Yahoo! UK Services Limite", "Yahoo! is an American web services provider headquartered in Sunnyvale, California, and owned by Verizon Media. The original Yahoo! company was founded by Jerry Yang and David Filo in January 1994 and was incorporated on March 2, 1995. Yahoo was one of the pioneers of the early Internet era in the 1990s. It provides or provided a Web portal, search engine Yahoo! Search, and related services, including Yahoo! Directory, Yahoo! Mail, Yahoo! News, Yahoo! Finance, Yahoo! Groups, Yahoo! Answers, advertising, online mapping, video sharing, fantasy sports, and its social media website. At its height it was one of the most popular sites in the United States. According to third-party web analytics providers Alexa and SimilarWeb, Yahoo! was the most widely read news and media website – with over 7 billion views per month – ranking as the sixth-most-visited website globally in 2016"]
	];

	constructor(
	  private loader: LoaderService,
    private actlog: ActivityLogService
  ) { }

	ngOnInit() {
		this.loader.getGeodata().then((gd) => {
			this.companies = _.uniq(gd.geodata.map((x) => x.company_name)).filter((x) => x !== "unknown").sort();
		});
	}

	getDesc() {
		let matched = false;
		this.explanations.forEach((expl) => {
			console.log(this.chosen, expl);
			if (expl[0] === this.chosen) {
				this.description = expl[1];
				matched = true;
			}
		});

		if (matched === false) {
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
		}
		this.actlog.log("company-info", this.chosen);
	}
}
