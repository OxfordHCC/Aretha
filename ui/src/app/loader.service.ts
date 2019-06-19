
import { Injectable, NgZone } from '@angular/core';
import { Http, HttpModule, Headers, URLSearchParams } from '@angular/http';
import 'rxjs/add/operator/toPromise';
import { mapValues, keys, mapKeys, values, trim, uniq, toPairs } from 'lodash';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import * as _ from 'lodash';
import { Observable } from '../../node_modules/rxjs/Observable';

enum PI_TYPES { DEVICE_SOFT, USER_LOCATION, USER_LOCATION_COARSE, DEVICE_ID, USER_PERSONAL_DETAILS }

export const API_ENDPOINT = 'https://negi.io/api';
export const CB_SERVICE_ENDPOINT = 'http://localhost:3333';
export const IOTR_ENDPOINT='http://localhost:4201/api';

export interface Host2PITypes { [host: string]: PI_TYPES[] }
export interface String2String { [host: string]: string }

export interface AppSubstitutions { [app: string]: string[] };

let zone = new NgZone({ enableLongStackTrace: false });


export interface DeviceImpact {
	minute: number;
	device: string;
	company: string;
  	impact: number;
};

export interface Device {
	[mac : string]: string;
	manufacturer: string;
	name: string;
};

export interface GeoData {
	[ip: string]: string;
  	country_name: string;
  	country_code: string;
  	latitude: string;
  	longitude: string;
};

export class DBUpdate {
  type: string;
  data: any;
  // timestamp: string;
  // operation: string;
  // schema: string;
  // table: string;
  // data: PacketUpdateInfo
};

export interface Example {
	impacts: any;
	geodata: any;
	devices: any;
	text: string;
};

export let cache = (target: Object, propertyKey: string, descriptor: TypedPropertyDescriptor<any>) => {
  // console.log('@cache:: ~~ ', target, propertyKey, descriptor);
  let retval: { [method: string]: any } = {},
    method = descriptor.value;

  descriptor.value = function (...args: any[]) {
    if (retval[propertyKey]) {
      return retval[propertyKey];
    }
    return retval[propertyKey] = method.apply(this, args);
  };
};

// can be customised to be sensitive to target.
// pass in function that will generate keys for the cache:
// e.g. if values varies on multiple parameters, then return 
// a concatenation of dependent values
export let memoize = (f: (...args: any[]) => string) => {
  return function (target: Object, propertyKey: string, descriptor: TypedPropertyDescriptor<any>) {
    let retval: { [method: string]: any } = {}, method = descriptor.value;
    descriptor.value = function (...args: any[]) {
      let cache_key = propertyKey + '_' + f.apply(null, args);
      if (retval[cache_key]) {
        return retval[cache_key];
      }
      return retval[cache_key] = method.apply(this, args);
    };
  };
}

export class CompanyDB {
  emoji_table = {
    US: '&#x1F1FA;&#x1F1F8;',
    UK: '&#x1F1EC;&#x1F1E7;',
    AT: '&#x1F1E6;&#x1F1F9;',
    CN: '&#x1F1E8;&#x1F1F3;',
    FR: '&#x1F1EB;&#x1F1F7;',
    CA: '&#x1F1E8;&#x1F1E6;',
    DE: '&#x1F1E9;&#x1F1EA;'
  };

  constructor(private _data: { [id: string]: CompanyInfo }, private sanitiser: DomSanitizer) {
    mapValues(this._data, (s) => {
      if (s && s.company && s.equity && s.equity.length) {
          let n = parseInt(s.equity, 10);
          if (n > 1e6) { s.equity = Math.round(n / 1.0e5) / 10.0 + 'm'; }
          if (n > 1e9) { s.equity = Math.round(n / 1.0e8) / 10.0 + 'bn'; }
      }
      if (s && s.company && s.jurisdiction_code && this.emoji_table[s.jurisdiction_code.toUpperCase()]) {
          s.jurisdiction_flag = this.emoji_table[s.jurisdiction_code.toUpperCase()];
      }
      if (s.parent) {
        s.parentInfo = this.get(s.parent);
      }
      if (s.crunchbase_url) {
        s.crunchbase_url = this.sanitiser.bypassSecurityTrustResourceUrl(s.crunchbase_url);
      }      
      // http://www.google.com/search?btnI=I%27m+Feeling+Lucky&ie=UTF-8&oe=UTF-8&q=
    });
  }
  get(companyid: string): CompanyInfo | undefined {
    return this._data[companyid];
  }
  add(info: CompanyInfo) {
    this._data[info.id] = info;
  }
  getCompanyInfos(): CompanyInfo[] {
    return values(this._data);
  }
  getIDs(): string[] {
    return keys(this._data);
  }
}

export class CompanyInfo {
    // readonly id: string;
    // readonly company: string;
    domains: string[];
    founded ?: string;
    acquired ?: string;
    type: string[];
    // readonly typetag ?: string;
    jurisdiction ?: string;
    jurisdiction_code ?: string;
    parent ?: string;
    parentInfo ?: CompanyInfo;
    crunchbase_url ?: string | SafeResourceUrl;
    lucky_url ?: string | SafeResourceUrl;
    capita ?: string;
    equity ?: string;
    size ?: string;
    data_source ?: string;
    description ?: string;
    constructor(readonly id: string, readonly company: string, domains: string[], readonly typetag: string) {
      this.domains = domains;
    }
}

export class IoTDataBundle {
  impacts: any;
  geodata: any;
  devices: any;
}

export class APIAppInfo {
    app: string;
    title: string;
    summary: string;
    description: string;
    storeURL: string;
    price: string;
    free: boolean;
    rating: string;
    numReviews: number;
    genre: string;
    installs: { min: number, max: number};
    developer: {
      email: string[];
      name: string;
      site: string;
      storeSite: string;
    };
    updated: string;
    androidVer: string;
    contentRating: string;
    screenshots: string[];
    video: string;
    recentChanges: string[];
    crawlDate: string; // date string    
    string: string; // what's this?
    region: string; // us
    ver: string; // date string 
    screenFlags: number;
    hosts?: string[];
    host_locations?: any;
    storeinfo: { 
      title: string;
      summary: string;
      androidVer: string;
      numReviews: number;
      installs: { min: number, max: number };
      rating: number;
      updated: string;
    }
    icon: string;
    emails: string[]; // author contact email
    name: string; 
    storeSite: string;
    site: string;
}

export interface APIAppStub {
  Title: string;
  appid: string;
}

const host_blacklist = ['127.0.0.1','::1','localhost'];

@Injectable()
export class LoaderService {

  _host_blacklist : {[key:string]:boolean};n

  apps: { [id: string]: APIAppInfo } = {};
  updateObservable: Observable<DBUpdate>;

  
  constructor(private httpM: HttpModule, private http: Http, private sanitiser: DomSanitizer) { 
    this._host_blacklist = host_blacklist.reduce((obj, a) => obj[a]=true && obj, {});
  }

  @cache  
  getHostToPITypes(): Promise<Host2PITypes> {
    return this.http.get('assets/data/pi_by_host.json').toPromise().then(response => {
      return response.json() as { [app: string]: string[] };
    }).then((data: { [app: string]: string[] }) => {
      return Promise.resolve(mapValues(data, 
        (s: string[]): PI_TYPES[] => s.map(pis => {
          if (PI_TYPES[pis] === undefined) { throw new Error(`undefined PI_TYPE ${pis}`);  }
          return PI_TYPES[pis]
        }))
      );
    });
  }
  getHostToCompany(): Promise<String2String> {
    return this.http.get('assets/data/h2c.json').toPromise().then(response => {
      return response.json() as String2String;
    });
  }
  getHostToShort(): Promise<String2String> {
    return this.http.get('assets/data/h2h_2ld.json').toPromise().then(response => {
      return response.json() as String2String;
    });
  }
  @cache
  getCompanyInfo(): Promise<CompanyDB> {
    return this.http.get('assets/data/company_details.json').toPromise().then(response => {
      return new CompanyDB(response.json() as {[name: string]: CompanyInfo}, this.sanitiser);
    });
  }
  getSubstitutions(): Promise<AppSubstitutions> {
    return this.http.get('assets/data/app_substitutions.json').toPromise().then(response => {
      return response.json() as AppSubstitutions;
    });
  }
  makeIconPath(url: string): string {
    if (url) {
      return [API_ENDPOINT, 'icons', url.slice(1)].join('/');
    }
  }
	
  @memoize((company) => company.id)
  getCrunchbaseURLs(company: CompanyInfo): Promise<SafeResourceUrl[]> {
    if (!company) { throw new Error('no company'); }
    console.log('getting crunchbase url for ', company);    
    const urlSP = new URLSearchParams(); 
    urlSP.set('q', company.company);
    return this.http.get(CB_SERVICE_ENDPOINT + `/cbase?${urlSP.toString()}`).toPromise()
      .then(response => response.json())
      .then((results: string[]) => results.map(result => this.sanitiser.bypassSecurityTrustResourceUrl(result)));
  }

  /**
   * Parses JSON Object into a URL param options object and then Turns that to a
   * string. 
   * @param options JSON of param options that can be used to query the xray API.
   */
  private parseFetchAppParams(options: {
      title?: string,
      startsWith?: string, 
      appID?: string, 
      fullInfo?: boolean, 
      onlyAnalyzed?: boolean, 
      limit?: number
    }): string {
      // Initialising URL Parameters from passed in options.
    let urlParams = new URLSearchParams();

    if (options.title) {
      urlParams.append('title', options.title);
    }
    if (options.startsWith) {
      urlParams.append('startsWith', options.startsWith);
    }
    if (options.appID) {
      urlParams.append('appID', options.appID);
    }
    if (options.fullInfo) {
      urlParams.append('isFull',  options.fullInfo ? 'true' : 'false');
    }
    if (options.onlyAnalyzed) {
      urlParams.append('onlyAnalyzed', options.onlyAnalyzed ? 'true' : 'false');
    }
    if (options.limit) {
      urlParams.append('limit', options.limit.toString());
    }
    return urlParams.toString();
  }

  @memoize((appid: string): string => appid)
  getAlternatives(appid: string): Promise<APIAppInfo[]> {
    return this.http.get(API_ENDPOINT + `/alt/${appid}?nocache=true`).toPromise()
      .then(response => {
        if (response && response.text().toString().trim() === 'null') {  console.error('ERROR - got a null coming from the endpoint ~ ' + appid);    }
        return response && response.text().toString().trim() !== 'null' ? response.json() as string[] : [];
      }).then(appids => Promise.all(appids.map(id => this.getFullAppInfo(id))))
      .then(appinfos => appinfos.filter(x => x));
  }

  getCachedAppInfo(appid: string): APIAppInfo | undefined {
    // returns a previously seen appid
    return this.apps[appid];
  }

	connectToAsyncDBUpdates() : void {
    	let observers = [], eventSource; 
    	this.updateObservable = Observable.create(observer => {
      		observers.push(observer);
      		if (observers.length === 1 && eventSource === undefined) {       
        		eventSource = new EventSource(IOTR_ENDPOINT + '/stream');
        		
				eventSource.onopen = thing => {
          			console.info('EventSource Open', thing);
        		};
        		eventSource.onmessage = function (score) {
          			let incoming = <DBUpdate>JSON.parse(score.data);
          			zone.run(() => observers.map(obs => obs.next(incoming)))
        		};
        		eventSource.onerror = error => {
          			console.error("eventSource onerror", error);
          			zone.run(() => observers.map(obs => obs.error(error)));
        		};              
      		}
      		return () => { if (eventSource) { eventSource.close(); } }
  		});        
	}


	asyncDeviceImpactChanges(): Observable<DeviceImpact[]> {
    	return Observable.create(observer => {
      		this.updateObservable.subscribe({
        		next(x) {           
					if (x.type === 'impact') {
            			observer.next(<DeviceImpact[]>x.data);
            			return true;
          			} 
          			return false;
        		},
        		error(e) { observer.error(e); }
      		});
    	});
  	}
  
	asyncGeoUpdateChanges(): Observable<any[]> {
    	return Observable.create(observer => {
    		this.updateObservable.subscribe({
        		next(x) {
          			if (x.type === 'geodata') {
            			observer.next(x.data);
            			return true;
          			} 
          			return false;
        		},
        		error(e) { observer.error(e); }
      		});
    	});
  	}
  
	asyncDeviceChanges(): Observable<Device[]> {
    	return Observable.create(observer => {
      		this.updateObservable.subscribe({
        		next(x) {           
          			if (x.type === 'device') {
            			observer.next(<Device[]>x.data);
            			return true;
          			} 
          			return false;
        		},
        		error(e) { observer.error(e); }
      		});
    	});
  	}

	getIoTData(start: number, end: number, delta: number): Promise<IoTDataBundle> {
		return this.http.get(IOTR_ENDPOINT + '/impacts/' + start + '/' + end + '/' + delta).toPromise().then(response2 => {
      		let resp = response2.json(),
        		impacts = resp.impacts,
        		geodata = resp.geodata,
				devices = resp.devices;
			return resp;
    	});
  	}
	
	getIoTDataAggregated(start: number, end: number): Promise<IoTDataBundle> {
		return this.http.get(IOTR_ENDPOINT + '/impacts/' + start + '/' + end).toPromise().then(response2 => {
      		let resp = response2.json(),
        		impacts = resp.impacts,
        		geodata = resp.geodata,
				devices = resp.devices;
			return resp;
    	});
  	}

	getExample(question: string): Promise<Example> {
		return this.http.get(IOTR_ENDPOINT + '/example/' + question).toPromise().then(response2 => {
      		let resp = response2.json(),
        		impacts = resp.impacts,
        		geodata = resp.geodata,
				devices = resp.devices,
				text = resp.text;
			return resp
		});
	}
  
  @memoize((appid: string): string => appid)
  getFullAppInfo(appid: string): Promise<APIAppInfo|undefined> {
    return this.http.get(API_ENDPOINT + `/apps?isFull=true&limit=10000&appId=${appid}`).toPromise()
    .then(response => (response && response.json() as APIAppInfo[])[0] || undefined)
    .then(appinfo => {
      if (appinfo) { 
		  //return this._prepareAppInfo(appinfo);
		  return undefined;
      }
      return undefined;
    }).then(appinfo => {
      if (appinfo) {
        this.apps[appid] = appinfo;
      } else {
        console.warn('null appinfo');
      }
      // console.log(appinfo);
      return appinfo;
    });
  }

  @memoize(() => 'world')
  getWorldMesh(): Promise<any> {
    return this.http.get('assets/110m-sans-antarctica.json').toPromise().then((result) => result.json());
  }

}
