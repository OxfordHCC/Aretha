import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { LoaderService } from './loader.service';
import { HttpModule } from '@angular/http';
import { AppComponent } from './app.component';
import { RefinebarComponent } from './refinebar/refinebar.component';
// import { UsageListenerComponent } from './usage-listener/usage-listener.component';
// import { UsagetableComponent } from './usagetable/usagetable.component';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';
// import { FoobarComponent } from './foobar/foobar.component';
import { ErrorComponent } from './error/error.component';
import { UsageConnectorService } from './usage-connector.service';
import { Ng2CompleterModule } from 'ng2-completer';

// no longer used with IoTRefine => 
// import { SingleDisplayComponent } from './single-display/single-display.component';
// import { TiledDisplayComponent } from './tiled-display/tiled-display.component';
// import { CompareComponent } from './compare/compare.component';
// import { CompareContainerComponent } from './compare-container/compare-container.component';
// 
import { CompanyListComponent } from './company-list/company-list.component';
// import { AutocompleteComponent } from './autocomplete/autocomplete.component';
import { HostUtilsService } from "app/host-utils.service";
import { AppinfoComponent } from './appinfo/appinfo.component';
import { CompanyinfoComponent } from './companyinfo/companyinfo.component';
import { RefinecatComponent } from './refinecat/refinecat.component';

import { FocusService } from "app/focus.service";
import { HoverService } from "app/hover.service";
import { ActivityLogService } from "app/activity-log.service";
import { GeomapComponent } from './geomap/geomap.component';
import { GeobarComponent } from './geobar/geobar.component';
import { TiledAllComponent } from './tiled-all/tiled-all.component';
import { FocusInfoboxComponent } from './focus-infobox/focus-infobox.component';
import { UserStudySetupComponent } from './user-study-setup/user-study-setup.component';
import { LayoutTimeseriesComponent } from './layout-timeseries/layout-timeseries.component';
import { TimeseriesComponent } from './timeseries/timeseries.component';
import { LayoutEduComponent } from './layout-edu/layout-edu.component';
import { ContentEncryptionComponent } from './content-encryption/content-encryption.component';
import { ExampleComponent } from './example/example.component';



const appRoutes: Routes = [ 
	{path: '', 			component: LayoutTimeseriesComponent},
	{path: 'refine',	component: TiledAllComponent},
	{path: 'edu',		component: LayoutEduComponent}
];


@NgModule({
  declarations: [
    AppComponent,
    RefinebarComponent,
    ErrorComponent,
    CompanyListComponent,
    // not used with IoT Refine >>
    // UsagetableComponent,
    // CompareComponent,    
    // UsageListenerComponent,
    // CompareContainerComponent,
    // AutocompleteComponent,
    // not ever used:
    // FoobarComponent,    
    AppinfoComponent,
    CompanyinfoComponent,
    RefinecatComponent,
    GeomapComponent,
    GeobarComponent,
    TiledAllComponent,
    FocusInfoboxComponent,
    UserStudySetupComponent,
    LayoutTimeseriesComponent,
    TimeseriesComponent,
    LayoutEduComponent,
    ContentEncryptionComponent,
    ExampleComponent    
  ],
  imports: [
    HttpModule,
    BrowserModule,
    FormsModule,
    RouterModule.forRoot(
      appRoutes,
      { enableTracing: true } // <-- debugging purposes only
    ),
    Ng2CompleterModule
  ],
  providers: [LoaderService, UsageConnectorService, HostUtilsService, FocusService, HoverService, ActivityLogService],
  bootstrap: [AppComponent]
})
export class AppModule { }
