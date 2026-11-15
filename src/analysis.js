import {featureLabels} from './ui.js';
// Primera versión del algoritmo compartido por el equipo (coseno de 7 indicadores).
// El return original tenía un salto de línea que devolvía undefined. Aquí los perfiles
// llegan preprocesados desde DEM.tif reales por scripts/preparar_catalogo.py.
export const KEYS=Object.keys(featureLabels);
export function cosine(a,b){
 if(!a?.metrics||!b?.metrics)return null;
 const aa=KEYS.map(k=>a.metrics[k]);const bb=KEYS.map(k=>b.metrics[k]);
 if([...aa,...bb].some(x=>!Number.isFinite(x)))return null;
 const dot=aa.reduce((sum,x,i)=>sum+x*bb[i],0);
 const n1=Math.hypot(...aa),n2=Math.hypot(...bb);
 return n1>0&&n2>0?dot/(n1*n2):null;
}
export function comparisonStatus(a,b){
 if(!a||!b)return {ok:false,reason:'Select two terrains.'};
 if(a.id===b.id)return {ok:false,reason:'Select two different terrains.'};
 if(!a.metrics||!b.metrics)return {ok:false,reason:'Both numerical DEM datasets must be available to calculate terrain metrics. Missing values are never replaced by fabricated scores.'};
 if(Math.max(+a.native_resolution_m||0,+b.native_resolution_m||0)>250)return {ok:true,tier:'regional',reason:'REGIONAL EXPLORATORY ONLY · At least one DEM is coarse (MOLA ~463 m/cell). This uncalibrated cosine can be calculated, but 3/15-cell features are NOT scale-equivalent. It does not establish a reliable geological match, fine morphology or rover-scale obstacles.'};
 return {ok:true,reason:'Uncalibrated mathematical comparison only, not a scientifically validated planetary analog score.'};
}
