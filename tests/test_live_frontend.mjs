import assert from 'node:assert/strict';
import fs from 'node:fs';
const root={innerHTML:''},main={innerHTML:''},events={};
globalThis.document={documentElement:{dataset:{}},getElementById:id=>id==='app'?root:id==='main-content'?main:null,addEventListener:(event,fn)=>{events[event]=fn}};
globalThis.window={scrollTo:()=>{},addEventListener:()=>{},innerWidth:1400};
globalThis.location={hash:'#/comparador'};
const cat=JSON.parse(fs.readFileSync(new URL('../data/catalog.json',import.meta.url),'utf8'));
const chemistry=JSON.parse(fs.readFileSync(new URL('../data/chemistry.json',import.meta.url),'utf8'));
let lastRequest=null;
const fake={regions:{a:'Timanfaya',b:'Mare Tranquillitatis',a_id:'Timanfaya_ASTER',b_id:'Mare_Tranquillitatis_SLDEM'},feature_comparison:[{key:'pendiente_media_deg',label:'Mean slope',a:5,b:3,delta:-2,relative_change_pct:-40}],native_resolution_m:{a:30,b:59},coverage_pct:{a:100,b:100},legacy_cosine:.93,normalized_elevation_wasserstein:.123,normalized_elevation_KS_statistic:.2,pixelwise_difference:null,key_findings:['Slope is lower in reference B at the observed scale.'],interpretive_notes:[],warnings:['Native resolution mismatch.'],fine_scale_comparison_permitted:false,interpretation_note:'Not geological validation.'};
globalThis.fetch=async(url,opts={})=>{
 if(url.includes('catalog.json'))return {ok:true,json:async()=>cat};
 if(url.includes('chemistry.json'))return {ok:true,json:async()=>chemistry};
 if(url.includes('api/health'))return {ok:true,json:async()=>({status:'ok',ai_key_configured:false})};
 if(url.includes('api/analyze')){lastRequest=JSON.parse(opts.body);return {ok:true,json:async()=>fake}}
 throw Error('Unexpected URL: '+url);
};
await import('../src/app.js');
await new Promise(resolve=>setTimeout(resolve,50));
assert.match(root.innerHTML,/Analyze selected terrains/);
assert.match(root.innerHTML,/Planetary Comparator/);
events.change({target:{id:'cmpB',value:'Mare_Tranquillitatis_SLDEM'}});
assert.match(main.innerHTML,/Analyze selected terrains/);
await events.click({target:{closest:()=>({dataset:{action:'runAnalysis'}})}});
assert.deepEqual(lastRequest,{a:'Timanfaya_ASTER',b:'Mare_Tranquillitatis_SLDEM'});
assert.match(main.innerHTML,/Scientific suitability/);
assert.match(main.innerHTML,/0\.93/);
assert.match(main.innerHTML,/api\/chart/);
console.log('Live frontend analysis workflow passed (mocked local API).');
