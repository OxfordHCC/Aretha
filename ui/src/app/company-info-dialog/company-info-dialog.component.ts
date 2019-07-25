import { Component, OnInit, Input, Output, EventEmitter, OnChanges } from '@angular/core';
import { CompanyInfo } from '../loader.service';
import { HttpModule, Http } from '../../../node_modules/@angular/http';
import { DomSanitizer } from '../../../node_modules/@angular/platform-browser';

const CB_SERVICE_URL = 'http://localhost:3333/cbase?q=';

@Component({
  selector: 'app-company-info-dialog',
  templateUrl: './company-info-dialog.component.html',
  styleUrls: ['./company-info-dialog.component.scss']
})
export class CompanyInfoDialogComponent implements OnInit, OnChanges {

  @Input() company : CompanyInfo;
  @Output() close = new EventEmitter<any>();

  loaded_company : string;
  company_cb_url : any;


  constructor(private httpM: HttpModule, private http: Http, private sanitiser: DomSanitizer) { 
  }

  ngOnInit() {}

  emitClose() { this.close.emit(); }

  ngOnChanges(changes) {
    if (this.company !== undefined && this.loaded_company !== this.company.company) { 
      const url = `${CB_SERVICE_URL}${encodeURIComponent(this.company.company)}`;
      console.info('encoded url ', url);
      return this.http.get(`${CB_SERVICE_URL}${encodeURIComponent(this.company.company)}`).toPromise().then(response => {
        let results = response.json() as string[];
        if (results.length > 0) { 
          this.company_cb_url = this.sanitiser.bypassSecurityTrustResourceUrl(results[0]);
        }
      });
    }
  }

}
