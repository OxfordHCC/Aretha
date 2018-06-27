import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { LoaderService } from './loader.service';
import { HttpModule } from '@angular/http';
import { AppComponent } from './app.component';
import { RefinebarComponent } from './refinebar/refinebar.component';
import { UsageListenerComponent } from './usage-listener/usage-listener.component';
import { UsagetableComponent } from './usagetable/usagetable.component';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';
import { FoobarComponent } from './foobar/foobar.component';
import { ErrorComponent } from './error/error.component';
import { UsageConnectorService } from './usage-connector.service';
import { CompanybarComponent } from './companybar/companybar.component';
import { Ng2CompleterModule } from 'ng2-completer';

import { SingleDisplayComponent } from './single-display/single-display.component';
import { TiledDisplayComponent } from './tiled-display/tiled-display.component';
import { CompareComponent } from './compare/compare.component';
import { CompanyListComponent } from './company-list/company-list.component';
import { CompareContainerComponent } from './compare-container/compare-container.component';
import { AutocompleteComponent } from './autocomplete/autocomplete.component';
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



const appRoutes: Routes = [
  {
    path: 'alternatives/:app',
    component: CompareContainerComponent
  },  
  {
    path: 'grid',
    component: TiledAllComponent,
  },    
  {
    path: 'scroll',
    component: TiledDisplayComponent,
  },  
  {
    path: 'add',
    component: UsagetableComponent,
  },  
  { path: 'setup', component: UserStudySetupComponent },
  { path: '', redirectTo: '/add', pathMatch: 'full' },
  { path: '**', component: ErrorComponent, data: { message: 'page not found' } }
];


@NgModule({
  declarations: [
    AppComponent,
    RefinebarComponent,
    UsagetableComponent,
    SingleDisplayComponent,
    TiledDisplayComponent,    
    FoobarComponent,
    ErrorComponent,
    CompanybarComponent,
    CompareComponent,
    CompanyListComponent,
    UsageListenerComponent,
    CompareContainerComponent,
    AutocompleteComponent,
    AppinfoComponent,
    CompanyinfoComponent,
    RefinecatComponent,
    GeomapComponent,
    GeobarComponent,
    TiledAllComponent,
    FocusInfoboxComponent,
    UserStudySetupComponent    
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
