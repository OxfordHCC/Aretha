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
import { ContentEncryptionComponent } from './content-encryption/content-encryption.component';
import { ExampleComponent } from './example/example.component';
import { MatRadioModule, MatInputModule, MatButtonModule, MatBadgeModule, MatFormFieldModule, MatSelectModule} from '@angular/material';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { ContentTrackingComponent } from './content-tracking/content-tracking.component';
import { ContentInferenceComponent } from './content-inference/content-inference.component';
import { ContentBreachComponent } from './content-breach/content-breach.component';
import { ContentFrequencyComponent } from './content-frequency/content-frequency.component';
import { NameDeviceComponent } from './name-device/name-device.component';
import { CompanyInfoComponent } from './company-info/company-info.component';
import { RedactionComponent } from './redaction/redaction.component';

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
    ContentEncryptionComponent,
    ExampleComponent,
    ContentTrackingComponent,
    ContentInferenceComponent,
    ContentBreachComponent,
    ContentFrequencyComponent,
    NameDeviceComponent,
    CompanyInfoComponent,
    RedactionComponent    
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
