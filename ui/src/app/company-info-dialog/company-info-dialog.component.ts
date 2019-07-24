import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { CompanyInfo } from '../loader.service';

@Component({
  selector: 'app-company-info-dialog',
  templateUrl: './company-info-dialog.component.html',
  styleUrls: ['./company-info-dialog.component.scss']
})
export class CompanyInfoDialogComponent implements OnInit {

  @Input() company : CompanyInfo;
  @Output() close = new EventEmitter<any>();

  constructor() {}

  ngOnInit() {}

  emitClose() { this.close.emit(); }

}
