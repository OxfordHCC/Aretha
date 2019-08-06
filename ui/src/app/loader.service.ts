
import { Injectable, NgZone } from '@angular/core';
import { Http, HttpModule} from '@angular/http';
import 'rxjs/add/operator/toPromise';
import { mapValues} from 'lodash';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import * as _ from 'lodash';
import { Observable } from 'rxjs';
import { Subject } from 'rxjs';

export const IOTR_ENDPOINT='http://localhost:4201/api';
let zone = new NgZone({ enableLongStackTrace: false });

export interface DeviceImpact {
	minute: number;
	device: string;
	company: string;
  	impact: number;
}

export interface AdHostMap {[host: string]: boolean};
export interface AdIPHostMap {[ip: string]: string[]};

export type ImpactSet = ({[mac:string] : {[dst:string]:number}});
export type BucketedImpacts = ({ [min_t:string]: ImpactSet});

export interface Device {
	[mac : string]: string;
	manufacturer: string;
	name: string;
}

export interface GeoData {
  ip: string;
  company_name: string;
  // country_name: string;
  country_code: string;
  latitude: string;
  longitude: string;
  domain: string;
}

export class DBUpdate {
  type: string;
  data: any;
}

export interface Example {
	impacts: any;
	geodata: any;
	devices: any;
	text: string;
}

export let cache = (target: Object, propertyKey: string, descriptor: TypedPropertyDescriptor<any>) => {
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
};

export class AdsDB { 
  constructor(private _data: {[ip:string]:string}) {
  }
  get(ip):CompanyInfo | undefined { 
    if (this._data[ip]) { 
      const domain = this._data[ip], 
        newinfo = new CompanyInfo(domain, domain, [domain], "advertising"); 
      newinfo.type = ['advertising'];
      return newinfo;
    }
    return;
  }
}

export class CompanyInfo {
  domains: string[];
  type: string[];
  jurisdiction_code ?: string;
  parent ?: string;
  parentInfo ?: CompanyInfo;
  crunchbase_url ?: string | SafeResourceUrl;
  equity ?: string;
  size ?: string;
  description ?: string;
  constructor(readonly id: string, readonly company: string, domains: string[], readonly typetag: string) {
    this.domains = domains;
  }
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

  token_to_id:{ [token:string]: string } = {};

  constructor(private _data: { [id: string]: CompanyInfo }, private sanitiser: DomSanitizer) {

    this._data = _.mapKeys(_data, (value,key) => key.toLowerCase());
    
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
      
      // cache token to id
      s.company.toLowerCase().trim().split(' ').map(t => { this.token_to_id[t] = s.id; });
    });
  }
  get(companyid: string): CompanyInfo | undefined {
    return this._data[companyid.toLowerCase()];
  }
  add(info: CompanyInfo) {
    this._data[info.id.toLowerCase().trim()] = info;
  }
  values():CompanyInfo[] {
    return _.values(this._data);
  }

  @memoize(x => 'match-'+x)
  matchNames(name:string):CompanyInfo | undefined {
    // @TODO
    let tgt_tokens = name.toLowerCase().trim().split(' ').filter(x => x && ['ltd.', 'co.'].indexOf(x) < 0);
    const matches = tgt_tokens.filter(x => this.token_to_id[x]);
    matches.sort((x,y) => y.length - x.length);
    // console.info('best match is ', matches[0]);
    if (matches.length) {
      return this.get(this.token_to_id[matches[0]]);
    }
    return;
  }

  @memoize(x => 'match-'+x)
  matchId(name:string):CompanyInfo | undefined {
    // @TODO
    const tgt_tokens = name.toLowerCase().trim().split(' ').filter(x => x).map(x => x.replace(/[^\w\.\s]|_/g, "")),
      matches = tgt_tokens.filter(x => x && this.get(x));

    matches.sort((x,y) => y.length - x.length);
    if (matches.length) { return this.get(matches[0]); }
    return;
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
  description: string;
  free: boolean;
  installs: { min: number, max: number};
    video: string;
    string: string; // what's this?
    hosts?: string[];
    storeinfo: {
      title: string;
      summary: string;
      androidVer: string;
      numReviews: number;
      installs: { min: number, max: number };
      rating: number;
      updated: string;
    };
    name: string;
    site: string;
}

const host_blacklist = ['127.0.0.1','::1','localhost'];

@Injectable()
export class LoaderService {

  _host_blacklist : {[key:string]:boolean};
  apps: { [id: string]: APIAppInfo } = {};
  updateObservable: Observable<DBUpdate>;
  private readyContentSource = new Subject<string>();
  contentChanged = this.readyContentSource.asObservable();
  
  constructor(private httpM: HttpModule, private http: Http, private sanitiser: DomSanitizer) { 
    this._host_blacklist = host_blacklist.reduce((obj, a) => obj[a]=true && obj, {});
  }

  @cache
  getCompanyInfo(): Promise<CompanyDB> {
    return this.http.get('assets/data/company_details.json').toPromise().then(response => {
      return new CompanyDB(response.json() as {[name: string]: CompanyInfo}, this.sanitiser);
    });
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
                zone.run(() => observers.map(obs => { 
                  try { obs.next(incoming); } catch(e) { console.error(e); }
                }));
            };
            eventSource.onerror = error => {
                console.error("eventSource onerror", error);
                zone.run(() => observers.map(obs => obs.error(error)));
            };              
          }
          return () => { 
            // unsubscribe this one, but do not close until all are dead
            if (observers.indexOf(observer) >= 0) { 
              observers.splice(observers.indexOf(observer), 1);
            }
            if (eventSource && observers.length === 0) { 
              console.info('closing event source');
              eventSource.close(); 
              eventSource = undefined;
            } 
          };
  		});        
	}

	asyncDeviceImpactChanges(): Observable<ImpactSet> {
    	return Observable.create(observer => {
      		this.updateObservable.subscribe({
        		next(x) {           
                if (x.type === 'impact') {
                  observer.next(<ImpactSet>x.data);
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

	getIoTData(start: Date, end: Date, delta: number): Promise<IoTDataBundle> {
    const st_sec = Math.floor(start.getTime()/1000), 
      end_sec = Math.round(end.getTime()/1000);
		return this.http.get(IOTR_ENDPOINT + '/impacts/' + st_sec + '/' + end_sec + '/' + delta).toPromise().then(response2 => {
      		return response2.json();
    	});
  	}
	
	getIoTDataAggregated(start: number, end: number): Promise<IoTDataBundle> {
		return this.http.get(IOTR_ENDPOINT + '/impacts/' + start + '/' + end).toPromise().then(response2 => {
      		return response2.json();
    	});
  	}

	getExample(question: string): Promise<Example> {
		return this.http.get(IOTR_ENDPOINT + '/example/' + question).toPromise().then(response2 => {
      		return response2.json();
		});
	}
	
	getContent(): Promise<any> {
		return this.http.get(IOTR_ENDPOINT + '/content').toPromise().then(response2 => {
      		return response2.json();
		});
	}
	
	setContent(name: string, pre: string, post: string): Promise<any> {
		this.changeContent();
		if (pre === "") {pre = "Blank";}
		if (post === "") {post = "Blank";}
		return this.http.get(IOTR_ENDPOINT + '/content/set/' + name + '/' + encodeURIComponent(pre) + '/' + encodeURIComponent(post)).toPromise().then(response2 => {
      		return response2.json();
		});
	}
	
	getDevices(): Promise<any> {
		return this.http.get(IOTR_ENDPOINT + '/devices').toPromise().then(response2 => {
      		return response2.json();
		});
	}
	
	setDevice(mac: string, name: string): Promise<any> {
		return this.http.get(IOTR_ENDPOINT + '/devices/set/' + mac + '/' + name).toPromise().then(response2 => {
      		return response2.json();
		});
	}

	getGeodata(): Promise<any> {
		return this.http.get(IOTR_ENDPOINT + '/geodata').toPromise().then(response2 => {
      		return response2.json();
		});
	}

	getDescription(desc: string): Promise<any> {
		return this.http.get('https://en.wikipedia.org/w/api.php?format=json&action=query&prop=extracts&exintro&explaintext&redirects=1&origin=*&titles=' + desc).toPromise().then(response2 => {
      		return response2.json();
		});
	}

	getRedact(): Promise<any> {
		return this.http.get(IOTR_ENDPOINT + '/redact').toPromise().then(response2 => {
      		return response2.json();
		});
	}

	setRedact(company: string): Promise<any> {
		return this.http.get(IOTR_ENDPOINT + '/redact/set/' + company).toPromise().then(response2 => {
      		return response2.json();
		});
	}

	getPid(): Promise<any> {
    return this.http.get(IOTR_ENDPOINT + '/pid').toPromise().then(response2 => {
      return response2.json();
    });
  }

  setAct(pid: string, type: string, action: string) {
    this.http.get(IOTR_ENDPOINT + '/activity/' + pid + '/' + type + '/' + action).toPromise().then(response2 => {
		console.log("sent activity");
	});
  }

  @memoize(() => 'world')
  getWorldMesh(): Promise<any> {
    return this.http.get('assets/110m-sans-antarctica.json').toPromise().then((result) => result.json());
  }

	changeContent(): void {
		this.readyContentSource.next("tick");
  }

  @cache
  getAdsInfo():Promise<AdsDB> { 
    // return this.http.get('assets/data/ads-to-ip.json').toPromise().then(hosts => {
    return this.http.get('assets/data/peter-ads.json').toPromise().then(hosts => {
      const h2ip = hosts.json();
      return new AdsDB(Object.keys(h2ip).reduce((obj, host) => {
        h2ip[host].map(ip => { obj[ip] = host; });
        return obj;
      }, {}));
    });
  }
  
}
