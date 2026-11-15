import {escapeHTML as esc, nice} from './ui.js';

async function send(endpoint, pair) {
  const controller=new AbortController();
  const timeout=setTimeout(()=>controller.abort(),110000);
  let response;
  try {response=await fetch('/api/'+endpoint, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(pair),signal:controller.signal});}
  catch(error){if(error.name==='AbortError')throw Error('The terrain analysis took too long. Please retry or choose smaller valid DEMs.');throw error}
  finally {clearTimeout(timeout);}
  let value;
  try {value=await response.json()} catch {throw Error('The terrain analysis service is temporarily unavailable. Please try again later.')} 
  if (!response.ok)throw Error(value?.detail||`HTTP ${response.status}`);
  return value;
}
export const analyzeLive=(a,b)=>send('analyze',{a,b});
export async function serverStatus() {
  try {const r=await fetch('/api/health');if(!r.ok)return null;return await r.json()} catch {return null}
}
const detail=(text)=>esc(text??'');
function metricRows(report) {
  return report.feature_comparison.map(m=>{
   const hi=Math.min(100,Math.max(2,Math.abs(m.relative_change_pct)));
   const title=esc(m.label);
   return `<div class="scientific-row"><div class="scientific-row-header"><strong>${title}</strong><small>A: ${nice(m.a,5)} · B: ${nice(m.b,5)} · Δ ${nice(m.delta,5)}</small></div><div class="metric-track"><span style="width:${hi}%"></span></div></div>`;
  }).join('');
}
export function drawNumericalReport(report) {
 const c=report.legacy_cosine;
 const w=report.warnings||[];
 const pix=report.pixelwise_difference;
 const findings=report.key_findings||[];
 return `<div class="science-results">
 <div class="science-scoregrid">
 <div class="science-kpi"><small>COSINE ALIGNMENT · EXPLORATORY</small><strong>${c==null?'—':nice(c,5)}</strong><span>Mathematical alignment, not a % of geological similarity</span></div>
 <div class="science-kpi"><small>RELATIVE HEIGHT · WASSERSTEIN</small><strong>${nice(report.normalized_elevation_wasserstein,4)}</strong><span>Lower = more similar normalized height distribution</span></div>
 <div class="science-kpi"><small>K–S · RELATIVE HEIGHT</small><strong>${nice(report.normalized_elevation_KS_statistic,4)}</strong><span>Distributional distance (0 to 1)</span></div>
 </div>
 <div class="analysis-readout"><h3>What the numbers suggest</h3>${findings.map(t=>`<p>${detail(t)}</p>`).join('')}<p class="analysis-conclusion">${detail(report.interpretation_note)}</p></div>
 <div class="science-plot"><img loading="lazy" src="/api/chart?a=${encodeURIComponent(report.regions.a_id||report.regions.a)}&b=${encodeURIComponent(report.regions.b_id||report.regions.b)}" alt="Scientific DEM comparison chart generated from numerical source GeoTIFFs" /></div><div class="analysis-readout"><h3>Physical interpretation and alternative explanations</h3>${(report.interpretive_notes||[]).map(n=>`<p><strong>${detail(n.metric)}</strong> — ${detail(n.interpretation)}. ${detail(n.scientific_meaning)}<br/><small>Alternative: ${detail(n.alternative_explanation)}</small></p>`).join('')}</div><div class="report-columns"><div class="analysis-readout"><h3>Seven calculated terrain features</h3>${metricRows(report)}</div><div class="analysis-readout"><h3>Scientific suitability</h3><p><b>Fine-scale comparison:</b> ${report.fine_scale_comparison_permitted?'Eligible for exploratory analysis (not validated)':'NOT supported at current native resolution'}</p><p><b>Native ground spacing:</b> ${nice(report.native_resolution_m.a,2)} m vs ${nice(report.native_resolution_m.b,2)} m</p><p><b>Valid elevation coverage:</b> ${nice(report.coverage_pct.a,1)}% vs ${nice(report.coverage_pct.b,1)}%</p>${pix?`<p><b>Aligned same-world raster RMSE:</b> ${nice(pix.raw_rmse_m,2)} m</p><p><b>RMSE after vertical-offset removal:</b> ${nice(pix.shape_rmse_after_median_offset_m,2)} m</p>`:'<p>No pixelwise elevation difference map was produced because the terrains are not physically co-located.</p>'}</div></div>
 <div class="analysis-warnings"><h3>Quality and interpretation boundaries</h3><ul>${w.map(t=>`<li>${detail(t)}</li>`).join('')}</ul></div></div>`;
}
