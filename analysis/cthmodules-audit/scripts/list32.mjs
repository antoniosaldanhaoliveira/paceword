import fs from 'fs';
const src = fs.readFileSync('CTHmodules/cth-corpus.js','utf8');
const rows=[...src.matchAll(/\['([A-Z0-9\-]+)',\s*(-?\d+),\s*'(\w+)',\s*([\d.]+),\s*([\d.]+),\s*([\d.]+),\s*([\d.]+),\s*([+-][\d.]+),\s*([\d.]+),\s*([\d.]+),[\s\S]*?historical_role:\s*'(\w+)'/g)]
 .map(m=>({id:m[1],year:+m[2],cat:m[3],obs:+m[4],pol:+m[5],eco:+m[6],soc:+m[7],d:+m[8],swan:+m[9],loop:+m[10],role:m[11]}));
const yr=y=>y<0?`${-y} BCE`:`${y} CE`;
console.log('#  '+'EVENT'.padEnd(31)+'YEAR'.padStart(9)+'  '+'CATEGORY'.padEnd(15)+'ROLE'.padEnd(11)+' dCTH   OUTCOME');
console.log('─'.repeat(96));
rows.forEach((r,i)=>console.log(
  String(i+1).padStart(2)+' '+r.id.replace(/-\d+BCE$|-\d+$/,'').replace(/-/g,' ').toLowerCase().replace(/\b\w/g,c=>c.toUpperCase()).padEnd(31)
  +yr(r.year).padStart(9)+'  '+r.cat.padEnd(15)+r.role.padEnd(11)
  +(r.d>0?'+':'')+r.d.toFixed(2)+'   '+r.obs.toFixed(2)+' '+(r.obs>=0.5?'RMD adapt':'CMN decline')));
console.log('─'.repeat(96));
console.log(`${rows.length} events | ${rows.filter(r=>r.obs>=.5).length} adaptive / ${rows.filter(r=>r.obs<.5).length} decline | span ${yr(rows[0].year)} → ${yr(rows.at(-1).year)}`);
