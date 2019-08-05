
import * as d3 from 'd3';
import * as _ from 'lodash';
import { CompanyInfo, CompanyDB, AdsDB, GeoData } from './loader.service';

// Adapted from http://martin.ankerl.com/2009/12/09/how-to-create-random-colors-programmatically/

export function dateMin(d1: Date, d2:Date):Date { 
    return d1.valueOf() < d2.valueOf() ? d1:d2;
}

var randomColor = (function(){
    var golden_ratio_conjugate = 0.618033988749895;
    var h = Math.random();
  
    var hslToRgb = function (h, s, l){
        var r, g, b;
  
        if(s == 0){
            r = g = b = l; // achromatic
        }else{
            function hue2rgb(p, q, t){
                if(t < 0) t += 1;
                if(t > 1) t -= 1;
                if(t < 1/6) return p + (q - p) * 6 * t;
                if(t < 1/2) return q;
                if(t < 2/3) return p + (q - p) * (2/3 - t) * 6;
                return p;
            }
  
            var q = l < 0.5 ? l * (1 + s) : l + s - l * s;
            var p = 2 * l - q;
            r = hue2rgb(p, q, h + 1/3);
            g = hue2rgb(p, q, h);
            b = hue2rgb(p, q, h - 1/3);
        }
  
        return '#'+Math.round(r * 255).toString(16)+Math.round(g * 255).toString(16)+Math.round(b * 255).toString(16);
    };
    
    return function(){
      h += golden_ratio_conjugate;
      h %= 1;
      return hslToRgb(h, 0.5, 0.60);
    };
  })();

export function persistentColor(s: string): string { 
    // console.log('foo');
    if (localStorage[s] === undefined) {
        localStorage[s] = randomColor();
    }
    return localStorage[s];
}

export function matchCompanies(geodata : GeoData[], cdb : CompanyDB, ads_db: AdsDB): {[c:string]:CompanyInfo} {

    const info_by_domain = cdb.values().reduce((obj, info) => {
        info.domains.map(domain => { obj[domain] = info; });
        return obj;
    }, {});

    return geodata.reduce((obj, geodata_entry) => {
        const domain = geodata_entry.domain;
        if (geodata_entry.domain && 
            geodata_entry.domain !== 'unknown' && 
            !obj[geodata_entry.company_name] && // we don't already have it
            info_by_domain[domain]) {              
            obj[geodata_entry.company_name] = info_by_domain[domain];
            return obj;
        }

        // next, if no domain then we try to match against ads
        if ((!geodata_entry.domain || geodata_entry.domain === 'unknown') && 
            ads_db.get(geodata_entry.ip)) {
            obj[geodata_entry.company_name] = ads_db.get(geodata_entry.ip);
            return obj;
        }        
        
        // next, try matching names
        // let mname1 = cdb.matchNames(geodata_entry.company_name);
        // if (mname1 !== undefined) { 
        //     obj[geodata_entry.company_name] = mname1;
        //     return obj;
        // }

        console.info("failure identifying information for > ", geodata_entry);
        return obj;
    },{});

}


        // clist = Object.keys(geodata_company_to_domains),

    // return clist.reduce((obj,cname) => { 
    //     // already done
    //     if (obj[cname]) { return obj; } 

    //     // attempt domain match
    //     const company_domains = new Array(...geodata_company_to_domains[cname]),
    //         domain_matches = company_domains.map(x => info_by_domain[x]).filter(x => x);
    //     if (domain_matches.length) { 
    //         obj[cname] = domain_matches[0];
    //         return obj;
    //     } 
    //     // name match        
    //     return obj;        
    // }, {});



    // const geodata_company_to_domains: {[c:string]: Set<string>} = geodata.reduce((obj, x) => {
    //         if (!obj[x.company_name]) { obj[x.company_name] = new Set<string>(); }
    //         obj[x.company_name].add(x.domain)
    //         return obj;
    //     },{}),
    //     clist = Object.keys(geodata_company_to_domains),

    // return clist.reduce((obj,cname) => { 
    //     // already done
    //     if (obj[cname]) { return obj; } 

    //     // attempt domain match
    //     const company_domains = new Array(...geodata_company_to_domains[cname]),
    //         domain_matches = company_domains.map(x => info_by_domain[x]).filter(x => x);
    //     if (domain_matches.length) { 
    //         obj[cname] = domain_matches[0];
    //         return obj;
    //     } 
    //     // name match        
    //     return obj;        
    // }, {});