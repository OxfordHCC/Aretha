
import * as d3 from 'd3';
import * as _ from 'lodash';
import { CompanyInfo, CompanyDB } from './loader.service';

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

export function matchCompanies(cdomains:{[c:string]: Set<string>}, companies : CompanyDB): {[c:string]:CompanyInfo} {
    let clist = Object.keys(cdomains),
        info_by_domain = companies.values().reduce( (obj, info) => {
            info.domains.map(domain => obj[domain] = info);
            return obj;
        }, {});

    return clist.reduce((obj,cname) => { 
        // already done
        if (obj[cname]) { return obj; } 

        // attempt domain match
        const company_domains = new Array(...cdomains[cname]),
            domain_matches = company_domains.map(x => info_by_domain[x]).filter(x => x);
        if (domain_matches.length) { 
            obj[cname] = domain_matches[0];
            return obj;
        } 

        // name match
        
        
        return obj;        
    }, {});

    

}
