import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { LoaderService } from './loader.service';
import { HttpModule } from '@angular/http';
import { AppComponent } from './app.component';
import { RefinebarComponent } from './refinebar/refinebar.component';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';
import { ErrorComponent } from './error/error.component';
import { Ng2CompleterModule } from 'ng2-completer';
import { AppinfoComponent } from './appinfo/appinfo.component';
import { RefinecatComponent } from './refinecat/refinecat.component';
import { FocusService } from "app/focus.service";
import { HoverService } from "app/hover.service";
import { ActivityLogService } from "app/activity-log.service";
import { GeomapComponent } from './geomap/geomap.component';
import { GeobarComponent } from './geobar/geobar.component';
import { TiledAllComponent } from './tiled-all/tiled-all.component';
import { FocusInfoboxComponent } from './focus-infobox/focus-infobox.component';
import { LayoutTimeseriesComponent } from './layout-timeseries/layout-timeseries.component';
import { TimeseriesComponent } from './timeseries/timeseries.component';
import { LayoutEduComponent } from './layout-edu/layout-edu.component';
import { ExampleComponent } from './example/example.component';
import { MatRadioModule, MatInputModule, MatButtonModule, MatBadgeModule, MatFormFieldModule, MatSelectModule} from '@angular/material';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { NameDeviceComponent } from './name-device/name-device.component';
import { CompanyInfoComponent } from './company-info/company-info.component';
import { RedactionComponent } from './redaction/redaction.component';
import { ContentBreachComponent } from './content-breach/content-breach.component';
import { ContentS1Component } from './content-s1/content-s1.component';
import { ContentS2Component } from './content-s2/content-s2.component';
import { ContentS3Component } from './content-s3/content-s3.component';
import { ContentB1Component } from './content-b1/content-b1.component';
import { ContentB2Component } from './content-b2/content-b2.component';
import { ContentB3Component } from './content-b3/content-b3.component';
import { ContentB4Component } from './content-b4/content-b4.component';
import { ContentD1Component } from './content-d1/content-d1.component';
import { ContentD2Component } from './content-d2/content-d2.component';
import { ContentD3Component } from './content-d3/content-d3.component';
import { ContentD4Component } from './content-d4/content-d4.component';
import { ContentSd1Component } from './content-sd1/content-sd1.component';

const appRoutes: Routes = [
	{path: '', redirectTo: '/timeseries', pathMatch: 'full'},
	{path: 'timeseries', 	component: LayoutTimeseriesComponent},
	{path: 'refine',		component: TiledAllComponent},
	{path: 'edu',			component: LayoutEduComponent},
	{path: 'review',		component: RedactionComponent}
];

@NgModule({
  declarations: [
    AppComponent,
    RefinebarComponent,
    ErrorComponent,
    AppinfoComponent,
    RefinecatComponent,
    GeomapComponent,
    GeobarComponent,
    TiledAllComponent,
    FocusInfoboxComponent,
    LayoutTimeseriesComponent,
    TimeseriesComponent,
    LayoutEduComponent,
    ExampleComponent,
    NameDeviceComponent,
    CompanyInfoComponent,
    RedactionComponent,
    ContentBreachComponent,
    ContentS1Component,
    ContentS2Component,
    ContentS3Component,
    ContentB1Component,
    ContentB2Component,
    ContentB3Component,
    ContentB4Component,
    ContentD1Component,
    ContentD2Component,
    ContentD3Component,
    ContentD4Component,
    ContentSd1Component    
  ],
  imports: [
    HttpModule,
    BrowserModule,
    FormsModule,
	MatRadioModule,
	MatButtonModule,
	MatBadgeModule,
	MatFormFieldModule,
	MatInputModule,
	MatSelectModule,
	BrowserAnimationsModule,
    RouterModule.forRoot(
      appRoutes,
      { enableTracing: true } // <-- debugging purposes only
    ),
    Ng2CompleterModule
  ],
  providers: [LoaderService, FocusService, HoverService, ActivityLogService],
  bootstrap: [AppComponent]
})
export class AppModule { }
