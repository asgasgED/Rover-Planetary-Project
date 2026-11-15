import assert from 'node:assert/strict';
import fs from 'node:fs';
const root={innerHTML:''};const events={};
globalThis.document={
 documentElement:{dataset:{}},
 getElementById:(id)=>id==='app'?root:null,
 addEventListener:(name,fn)=>{events['document_'+name]=fn},
};
globalThis.window={addEventListener:(name,fn)=>events['window_'+name]=fn,scrollTo:()=>{}};
globalThis.location={hash:'#/inicio'};
globalThis.fetch=async (url)=>({ok:true,json:async()=>JSON.parse(fs.readFileSync(new URL(url.includes('chemistry')?'../data/chemistry.json':'../data/catalog.json',import.meta.url),'utf8'))});
await import('../src/app.js');
await new Promise(resolve=>setTimeout(resolve,40));
for(const [hash,terms] of [
 ['#/inicio',['MARS','WORKFLOW','KILLA CODERS','planet-next']],
 ['#/explorador',['mapCanvas','Timanfaya','Natural Earth']],
 ['#/catalogo',['Terrain Catalog','region-card','Jezero']],
 ['#/analisis',['Terrain Analysis','Real terrain elevation profile','Elevation skewness']],
 ['#/comparador',['Planetary Comparator','cos(θ)','cmpA','cmpB']],
 ['#/descubrir',['Find Analog Sites','discoverSelect','EARTH CANDIDATE']],
 ['#/simulacion',['Rover Simulation','Simulation integration is coming']],
 ['#/region/Timanfaya_ASTER',['Geospatial data sheet','Timanfaya','Material composition']],
 ['#/region/Mare_Tranquillitatis_SLDEM',['Material composition','SiO₂','Apollo 11 lunar sample']],
]){
 location.hash=hash;
 events['window_hashchange']();
 for(const v of terms)assert.ok(root.innerHTML.includes(v),`Página ${hash}: falta ${v}`);
 console.log('Ruta correcta:',hash,'bytes',root.innerHTML.length);
}
for(const hash of ['#/resultados','#/metodologia']){
 location.hash=hash;events['window_hashchange']();
 assert.equal(location.hash,'#/inicio',`La ruta antigua ${hash} debe regresar al inicio`);
}
console.log('TerraRover v3 page routing tests passed.');
