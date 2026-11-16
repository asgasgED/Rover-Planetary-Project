/* TerraRover: local Webots mission workspace. All measurements originate from the API. */
import {escapeHTML as esc} from './ui.js';
const BASE='/api/simulation';
const model={terrains:[],terrainId:'',terrain:null,points:[],center:null,environment:'earth',
    parcelWidth:20,parcelHeight:20,seconds:450,run:null,enabled:false,loading:false,mapMode:'center'};
let polling=null, alive=false;
// Show only runs launched by this browser tab, not the globally latest Webots job.
const SESSION_RUN_KEY='terrarover-current-mission';
let ownRunId='';
try{ownRunId=sessionStorage.getItem(SESSION_RUN_KEY)||''}catch{}
function rememberOwnRun(id){
 ownRunId=typeof id==='string'&&/^[0-9a-f]{12}$/.test(id)?id:'';
 try{if(ownRunId)sessionStorage.setItem(SESSION_RUN_KEY,ownRunId);else sessionStorage.removeItem(SESSION_RUN_KEY)}catch{}
}

const f=(v,n=1)=>Number.isFinite(Number(v))?Number(v).toFixed(n):'—';
const safe=x=>esc(String(x??''));
const template=()=>`<section class="page-heading"><div><span class="overline">KILLA CODERS / ROBOTICS LAB</span><h1>Rover Simulation</h1><p>Explore published RGB maps, select a terrain parcel, run a real Webots rover and inspect actual telemetry.</p></div><span class="sim-status" id="simServerStatus">Checking engine…</span></section>
<div class="sim-workflow"><span>01 · CHOOSE TERRAIN</span><span>02 · SELECT PARCEL</span><span>03 · DRAW ROUTE</span><span>04 · SIMULATE</span><span>05 · ANALYZE</span></div>
<div class="sim-layout"><aside class="sim-sidebar"><section class="sim-card"><span class="overline">GEOSPATIAL CATALOG</span><h2>Choose your terrain</h2>
<label for="simTerrain">Published regions and Webots scenes</label><select id="simTerrain" class="select" aria-label="Terrain selection"><option value="">Loading terrains…</option></select>
<div class="sim-terrain-info" id="simTerrainInfo"></div></section>
<section class="sim-card"><span class="overline">REGION OF INTEREST</span><h2>Mission parcel</h2><p class="sim-help">Select a center on the RGB map. The Webots mesh uses measured elevation values (original DEM or data embedded in the published 3D visualization), never colors as heights.</p>
<div class="sim-two"><label>Width (m)<input id="simWidth" type="number" min="5" max="5000" step="5" value="20"></label><label>Height (m)<input id="simHeight" type="number" min="5" max="5000" step="5" value="20"></label></div>
<div class="sim-readout" id="simCenter">No parcel selected</div><div class="sim-readout" id="simParcelAdvice">Select a region to see its resolution.</div><button class="btn btn-outline sim-full" id="simCreateParcel" type="button">Generate Webots parcel</button><div class="sim-generation" id="simGenerated" role="status"></div></section>
<section class="sim-card"><span class="overline">WAYPOINT PLANNER</span><h2>Draw a mission route</h2><p class="sim-help">Switch to “Draw waypoints”, then click to set start, intermediate points and destination (minimum two points).</p>
<div class="sim-map-actions"><button class="btn btn-outline" id="simPickCenter" type="button">◎ Select center</button><button class="btn btn-outline" id="simPickRoute" type="button">↗ Draw waypoints</button></div><div class="sim-two-actions"><button class="btn btn-outline" id="simUndo" type="button">↶ Undo point</button><button class="btn btn-outline" id="simClear" type="button">Clear route</button></div>
<div class="sim-readout" id="simRouteReadout">0 points · 0.0 m</div><label for="simEnvironment">Gravity scenario (planetary environment)</label><select id="simEnvironment" class="select"><option value="earth">Earth · 9.81 m/s²</option><option value="mars">Mars · 3.71 m/s²</option><option value="moon">Moon · 1.62 m/s²</option></select><label for="simDuration">Maximum simulation time (s)</label><input id="simDuration" type="number" min="30" max="3600" step="30" value="450"><p class="sim-help">Sojourner: nominal maximum speed ≈ 0.039 m/s. Longer routes may time out.</p>
<button class="btn btn-primary sim-full" id="simStart" type="button">▶ Launch simulation</button><button class="btn btn-outline sim-full" id="simStop" type="button">■ Stop simulation</button></section></aside>
<section class="sim-main"><div class="sim-card sim-map-card"><div class="sim-header"><div><span class="overline">TOPOGRAPHIC VIEW / WORLD COORDINATES</span><h2 id="simMapTitle">Select a terrain</h2></div><span id="simMapScale">—</span></div>
<div class="sim-map" id="simMap" role="img" aria-label="Terrain preview: click to select parcel center or draw mission waypoints"><div class="sim-map-image" id="simMapImage"></div>
<svg id="simOverlay" aria-hidden="true" viewBox="0 0 1000 1000" preserveAspectRatio="none"></svg><span class="sim-map-empty" id="simMapEmpty">Select terrain to display topographic data</span></div>
<div class="sim-map-footer"><span id="simMapHint">No terrain selected</span><span>Coordinate convention: x → east · y → north · meters</span></div></div>
<div class="sim-card"><div class="sim-header"><div><span class="overline">WEBOTS / REAL SIMULATION</span><h2>Live rover view</h2></div><a id="simViewerLink" href="#/simulacion" target="_blank" rel="noopener noreferrer" class="btn btn-outline">Open Webots viewer ↗</a></div>
<div class="sim-stream" id="simStream"><div class="sim-stream-placeholder"><strong>Physics engine not started</strong><span>A genuine Webots stream will appear when a mission is launched in Docker. No video is simulated.</span></div></div>
<div class="sim-camera-bar" aria-label="Webots camera controls">
<button type="button" class="btn btn-outline" data-sim-camera="focus" disabled>🎯 Auto Focus</button>
<button type="button" class="btn btn-outline" data-sim-camera="follow" disabled>🚙 Follow Rover</button>
<button type="button" class="btn btn-outline" data-sim-camera="overview" disabled>🌐 Terrain Overview</button>
</div><div id="simCameraStatus" class="sim-camera-status" role="status">La cámara seguirá al rover cuando inicies una misión.</div>
<div id="simViewerHealth" class="sim-viewer-health" role="status">El visor se conectará automáticamente al iniciar la misión.</div><div id="simRunStatus" class="sim-run-status">No running mission.</div></div>
<div class="sim-card"><div class="sim-header"><div><span class="overline">WEBOTS / SIMULATED ROVER MEASUREMENTS</span><h2>Telemetry & results</h2></div><span id="simOutcome" class="sim-status">Awaiting run</span></div>
<div class="sim-metrics" id="simMetrics"><div>—<small>Distance · m</small></div><div>—<small>Velocity · m/s</small></div><div>—<small>Roll · °</small></div><div>—<small>Pitch · °</small></div></div>
<div id="simReport" class="sim-results-note">Metrics become available only after a real simulation publishes telemetry. No fabricated data.</div><div class="sim-downloads" id="simDownloads"></div><div class="sim-plot-container" id="simPlot"></div>
<div class="sim-alert" id="simError" role="status" hidden></div></div></section></div>
<div class="sim-footnote"><b>Scientific limitation:</b> A coarse DEM may be useful for regional morphology but cannot resolve centimeter-scale obstacles, wheel sinking, granular regolith, or actual mission safety. For meaningful rover-scale tests, use higher-resolution measured elevations.</div>`;
export function renderSimulationPage(){return template()}
export function destroySimulation(){if(typeof window.removeEventListener==='function')window.removeEventListener('message',onViewerMessage);alive=false;if(polling){clearInterval(polling);polling=null}}
const el=id=>document.getElementById(id);
async function api(path, init){const response=await fetch(BASE+path,{cache:'no-store',...init});const result=await response.json().catch(()=>({}));if(!response.ok)throw Error(result.detail||`HTTP ${response.status}`);return result}
const post=(path,payload)=>api(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
function showError(msg){let target=el('simError');if(target){target.hidden=!msg;target.textContent=msg||''}}
function setBusy(value){model.loading=value;['simStart','simCreateParcel','simUndo','simClear'].forEach(id=>{let btn=el(id);if(btn)btn.disabled=value})}
function current(){return model.terrain}
function allPointsLength(){return model.points.reduce((n,p,i)=>i?n+Math.hypot(p[0]-model.points[i-1][0],p[1]-model.points[i-1][1]):n,0)}
function updateSummary(){
 const t=current(); if(!t)return;
 el('simMapTitle').textContent=t.name;
 el('simMapScale').textContent=`${f(t.extent_x,0)} × ${f(t.extent_y,0)} m`;
 const source=t.synthetic?'Synthetic test terrain / not planetary field data':
   t.has_dem?'Original numeric DEM available':t.has_embedded_heights?'Numerical heights recovered from published 3D visualization':
   t.has_rgb_map?'RGB map available, missing elevation grid':'Catalog metadata only';
 const res=t.native_resolution_m?`${f(t.native_resolution_m,2)} m native spacing`:'Native resolution unavailable';
 el('simTerrainInfo').innerHTML=`<b>${safe(t.body)} · ${safe(t.source)}</b><small>${safe(source)} · ${safe(res)}</small><small>${t.has_world?'✓ Existing Webots world':t.can_create_parcel?'✓ Parcel extraction available':'⚠ RGB preview only: missing numeric geometry'}</small>${t.lfs_missing?'<small>Original DEM.tif in the ZIP is a Git LFS pointer.</small>':''}${t.warning?`<div class="sim-warning">${safe(t.warning)}</div>`:''}`;
 el('simMapImage').style.backgroundImage=t.preview_url?`url("${encodeURI(t.preview_url)}")`:'';
 el('simMapEmpty').hidden=Boolean(t.preview_url);
 el('simMapHint').textContent=model.mapMode==='center'?'Click the RGB map to select the center; use the size fields to draw the rectangle':'Click to add route waypoints (start → finish)';
 const rec=t.native_resolution_m ? Math.min(5000, Math.ceil(t.native_resolution_m*4/10)*10) : 20;
 el('simParcelAdvice').textContent=t.can_create_parcel ?
  `Native grid ≈ ${f(t.native_resolution_m,1)} m/pixel · recommended initial parcel ≥ ${rec} × ${rec} m. The selected physical area may be smaller because coordinates lie at pixel centers.`:
  'You can select a center on the RGB map, but physical parcel generation requires numeric elevations.';
 el('simPickCenter').classList.toggle('sim-tool-active',model.mapMode==='center');
 el('simPickRoute').classList.toggle('sim-tool-active',model.mapMode==='route');
 el('simCreateParcel').disabled=!t.can_create_parcel;
 el('simStart').disabled=!t.can_simulate;
 paintOverlay();
}
function paintOverlay(){
 const t=current();if(!t)return;
 const x=p=>1000*p[0]/t.extent_x, y=p=>1000*(1-p[1]/t.extent_y);
 let svg='';
 if(model.center){
  const w=1000*model.parcelWidth/t.extent_x,h=1000*model.parcelHeight/t.extent_y;
  svg+=`<rect x="${x(model.center)-w/2}" y="${y(model.center)-h/2}" width="${w}" height="${h}" class="sim-roi"/>`;
  svg+=`<circle cx="${x(model.center)}" cy="${y(model.center)}" r="7" class="sim-center"/>`;
 }
 if(model.points.length){
  svg+=`<polyline class="sim-route" points="${model.points.map(p=>`${x(p)},${y(p)}`).join(' ')}"/>`;
  model.points.forEach((p,i)=>{svg+=`<circle class="sim-point ${i===0?'sim-first':''}" cx="${x(p)}" cy="${y(p)}" r="9"/><text x="${x(p)+12}" y="${y(p)-10}" class="sim-point-label">${i===0?'S':i}</text>`});
 }
 if(model.run?.latest && Number.isFinite(Number(model.run.latest.x))){
  const p=[Number(model.run.latest.x),Number(model.run.latest.y)];svg+=`<circle class="sim-rover-dot" cx="${x(p)}" cy="${y(p)}" r="12"/>`;
 }
 el('simOverlay').innerHTML=svg;
 el('simCenter').textContent=model.center?`Center (${f(model.center[0],1)}, ${f(model.center[1],1)}) m`:'No parcel selected';
 const length=allPointsLength();
 el('simRouteReadout').textContent=`${model.points.length} waypoints · ${f(length,2)} m · ideal ≥ ${f(length/.039,0)} s`;
}
function choose(id){model.terrainId=id;model.terrain=model.terrains.find(t=>t.id===id)||null;model.points=[];model.center=null;model.mapMode=model.terrain?.can_simulate?'route':'center';
if(model.terrain?.can_create_parcel && !model.terrain?.can_simulate){
 const recommended=Math.max(20,Math.min(5000,Math.ceil((Number(model.terrain.native_resolution_m)||5)*4/10)*10));
 model.parcelWidth=recommended;model.parcelHeight=recommended;
 el('simWidth').value=recommended;el('simHeight').value=recommended;
}
el('simGenerated').textContent='';const parent=model.terrain?.parent_terrain;const origin=model.terrains.find(t=>t.id===parent)||model.terrain;model.environment=origin?.body==='Marte'?'mars':origin?.body==='Luna'?'moon':'earth';const select=el('simEnvironment');if(select)select.value=model.environment;updateSummary();}
function selectTerrains(){const sel=el('simTerrain'); if(!sel)return;
 sel.innerHTML='<option value="">Select a terrain…</option>'+model.terrains.map(t=>`<option value="${safe(t.id)}" ${t.id===model.terrainId?'selected':''}>${t.can_simulate?'● ':t.can_create_parcel?'◯ ':t.has_rgb_map?'◈ ':'× '}${safe(t.name)} · ${safe(t.body)}${t.synthetic?' (example)':''}</option>`).join('');}
function outputRun(data){
 model.run=data;
 const latest=data.latest||{},results=data.result||{};
 const val=(a,b)=>Number.isFinite(Number(results[a]))?Number(results[a]):Number.isFinite(Number(latest[b]))?Number(latest[b]):null;
 const number=(v,p=2)=>v==null?'—':f(v,p);
 const roll=val('max_roll_deg','roll_deg'),pitch=val('max_pitch_deg','pitch_deg');
 const metrics=[['Distance · m',number(val('distance_travelled','uninterrupted_dist_m'))],['Speed · m/s',number(val('average_speed','speed_ms'),3)],['Roll · °',number(roll)],['Pitch · °',number(pitch)]];
 el('simMetrics').innerHTML=metrics.map(([label,value])=>`<div>${safe(value)}<small>${safe(label)}</small></div>`).join('');
 el('simOutcome').textContent=data.status||'idle';
 el('simRunStatus').textContent=`Run ${data.id||'—'} · ${data.status||'idle'}${latest.time_sec!=null?' · '+f(latest.time_sec,1)+' simulated s':''}${latest.progress_pct!=null?' · '+f(latest.progress_pct,1)+'% route progress':''} · ${safe((data.environment||'earth').toUpperCase())} gravity · ${data.stream_ready?'puerto 3D disponible (escena pendiente)':'puerto 3D no disponible'}`;
 if(data.error)showError('Webots failed:\n'+data.error);
 
 if(data.result){
  el('simReport').textContent=`${data.result.simulation_status||'Finished'} · ${f(data.result.route_completion,1)}% of planned route · ${data.result.stall_events??'—'} stalls · ${data.result.stability_loss_events??'—'} instability alerts · ${f(data.result.elapsed_time_sec,1)} simulated seconds.`;
  const a=data.result.scientific_audit;
  if(a){ el('simReport').textContent += ` | Planned: ${f(a.planned_route_m,2)} m; nominal minimum: ${f(a.ideal_minimum_time_at_nominal_speed_s,0)} s. ` + (a.flags.includes('TIME_LIMIT_BELOW_NOMINAL_MINIMUM')?'⚠ Partial run expected with current time limit. ':'') + '⚠ Exploratory physics, not a validated field prediction. ' + (a.flags.includes('TERRAIN_COARSER_THAN_WHEEL_DIAMETER')?'Terrain resolution insufficient for wheel-scale obstacles.':''); }
 }else{el('simReport').textContent=data.status==='running'?'Simulation in progress: live telemetry will populate once the supervisor publishes its first observations.':'No measured run summary available.'}
 el('simDownloads').innerHTML=['json','csv','plot','manifest'].filter(ext=>data[ext+'_url']).map(ext=>`<a class="btn btn-outline" href="${safe(data[ext+'_url'])}" target="_blank" rel="noopener">${ext.toUpperCase()} ↗</a>`).join('')+(data.log_url?`<a class="btn btn-outline" href="${safe(data.log_url)}" target="_blank" rel="noopener">WEBOTS LOG ↗</a>`:'');
 el('simPlot').innerHTML=data.plot_url?`<img src="${safe(data.plot_url)}" alt="Actual simulation telemetry and route analysis, generated by Webots postprocessing" loading="lazy"/>`:'';
 const stream=el('simStream');
 if(data.camera_live && data.id && data.stream_ready){
  // Local auto-connecting Webots web component. Native /index.html requires clicking Connect.
  const url=data.viewer_url||`/src/rover-stream.html?mode=${encodeURIComponent(data.stream_mode||'mjpeg')}&run=${encodeURIComponent(data.id)}`;
  const link=el('simViewerLink');link.href=url;
  if(!stream.querySelector('iframe')||stream.dataset.runId!==data.id){
    stream.dataset.runId=data.id;
    stream.innerHTML=`<iframe title="Live Webots rover simulation" src="${safe(url)}" loading="eager" allow="fullscreen"></iframe>`;
    el('simViewerHealth').textContent='Conectando automáticamente a Webots en modo '+(data.stream_mode||'mjpeg').toUpperCase()+'…';
  }
 }else if(data.status==='running' && !data.stream_ready){stream.innerHTML='<div class="sim-stream-placeholder"><strong>Starting Webots 3D streaming…</strong><span>If this continues, open WEBOTS LOG below to see the actual engine error.</span></div>';stream.dataset.runId='';el('simViewerHealth').textContent='Esperando a que arranque el servidor de streaming.'}else if(!data.id){stream.innerHTML='<div class="sim-stream-placeholder"><strong>Physics engine not started</strong><span>Choose terrain, draw a route and launch.</span></div>';stream.dataset.runId=''}
 const cameraStatus=el('simCameraStatus');
 document.querySelectorAll('[data-sim-camera]').forEach(btn=>{
   btn.disabled=!data.camera_live;
   btn.classList.toggle('sim-camera-active',data.camera_requested===btn.dataset.simCamera);
 });
 if(cameraStatus){
   const ack=data.camera_ack;
   cameraStatus.textContent=ack?.status==='error'?'Cámara: '+(ack.message||'error del Supervisor'):
      ack?.status==='applied'?'Cámara aplicada: '+ack.mode+' ✓':
      data.camera_live?'Cámara solicitada: '+(data.camera_requested||'follow')+' (verificando…)':
      'Inicia una misión para activar la cámara.';
 }
 paintOverlay();
}
function onViewerMessage(event){
 if(event.origin!==location.origin || event.data?.source!=='terrarover-webots-viewer')return;
 const h=el('simViewerHealth');if(!h)return;
 h.textContent=event.data.message||'Sin mensaje del visor';
 h.classList.toggle('sim-viewer-health-error',event.data.state==='error');
}
export async function setupSimulation(){
 destroySimulation(); alive=true;
 // Never carry results over from a previous page visit or another run.
 model.run=null;
 if(typeof window.addEventListener==='function')window.addEventListener('message',onViewerMessage);
 const map=el('simMap');if(!map)return;
 document.querySelectorAll('[data-sim-camera]').forEach(btn=>btn.addEventListener('click',async()=>{
   const id=model.run?.id;
   if(!id || !model.run?.camera_live){showError('Primero inicia una misión en Webots.');return}
   const mode=btn.dataset.simCamera;
   const status=el('simCameraStatus');
   if(status)status.textContent='Enviando orden de cámara: '+mode+'…';
   try{
     await post('/runs/camera',{run_id:id,mode});
     const refreshed=await api('/runs/current');
     if(alive)outputRun(refreshed);
   }catch(err){showError('No se pudo cambiar la cámara: '+err.message)}
 }));
 map.addEventListener('click',ev=>{
   if(!current())return;
   const bounds=map.getBoundingClientRect();
   const u=Math.max(0,Math.min(1,(ev.clientX-bounds.left)/bounds.width));
   const v=Math.max(0,Math.min(1,(ev.clientY-bounds.top)/bounds.height));
   const point=[Number((u*model.terrain.extent_x).toFixed(3)),Number(((1-v)*model.terrain.extent_y).toFixed(3))];
   if(model.mapMode==='center'){model.center=point;el('simGenerated').textContent='Center selected. Click Generate Webots parcel to create a real .wbt world.'}
   else if(model.terrain.can_simulate){model.points.push(point);if(model.points.length>50)model.points.shift()}
   else showError('First generate a Webots parcel from the selected center; numeric elevations must be available.');
   paintOverlay();
 });
 el('simTerrain').addEventListener('change',ev=>{choose(ev.target.value);showError('')});
 el('simPickCenter').addEventListener('click',()=>{model.mapMode='center';updateSummary()});
 el('simPickRoute').addEventListener('click',()=>{model.mapMode='route';updateSummary()});
 el('simWidth').addEventListener('input',ev=>{model.parcelWidth=Number(ev.target.value)||20;paintOverlay()});
 el('simHeight').addEventListener('input',ev=>{model.parcelHeight=Number(ev.target.value)||20;paintOverlay()});
 el('simUndo').addEventListener('click',()=>{model.points.pop();paintOverlay()});
 el('simClear').addEventListener('click',()=>{model.points=[];paintOverlay()});
 el('simCreateParcel').addEventListener('click',async()=>{
  if(!current()||!model.center){showError('Choose the parcel center by clicking the large map first.');return}
  setBusy(true);showError('');el('simGenerated').textContent='Generating a physical parcel from numeric elevation…';
  try{
   const parcel=await post('/parcels',{terrain_id:model.terrainId,center_x:model.center[0],center_y:model.center[1],width_m:model.parcelWidth,height_m:model.parcelHeight,max_nodes:120});
   model.terrains.unshift(parcel);choose(parcel.id);selectTerrains();
   const gen=parcel.generation||{};
   el('simGenerated').textContent=`✓ Parcel created: ${gen.world||parcel.id}. ${gen.grid?gen.grid.xDimension+' × '+gen.grid.yDimension+' vertices. ':''}${gen.physical_extent_m?gen.physical_extent_m.width_x+' × '+gen.physical_extent_m.height_y+' m. ':''}Now click two waypoints and Launch simulation.`;
  }catch(err){showError(err.message);el('simGenerated').textContent='Parcel creation failed; no valid Webots world generated.'}finally{setBusy(false)}
 });
 el('simStart').addEventListener('click',async()=>{
  if(!current()?.can_simulate){showError('First choose a prepared Webots terrain or generate a parcel.');return}
  if(model.points.length<2){showError('Place at least two waypoints on the terrain map.');return}
  setBusy(true);showError('');
  try{
   model.seconds=Math.max(30,Math.min(3600,Number(el('simDuration').value)||450));
   model.environment=el('simEnvironment').value;
   const result=await post('/runs',{terrain_id:model.terrainId,points:model.points,max_duration_sec:model.seconds,environment:model.environment});
   if(!result?.id)throw Error('Webots did not return a valid run ID.');
   rememberOwnRun(result.id);
   outputRun(result);
  }catch(err){showError(err.message)}finally{setBusy(false)}
 });
 el('simStop').addEventListener('click',async()=>{try{outputRun(await post('/runs/stop',{}))}catch(err){showError(err.message)}});
 try{
   const [state,terrains,run]=await Promise.all([api('/status'),api('/terrains'),api('/runs/current')]);
   if(!alive)return;
   el('simServerStatus').textContent=state.webots_installed?'WEBOTS ENGINE READY':'WEB API ACTIVE · WEBOTS REQUIRES DOCKER';
   model.terrains=terrains;
   const currentID=model.terrainId;
   const ready=terrains.find(t=>t.id===currentID)||terrains.find(t=>t.id==='sample_analog_dem')||terrains.find(t=>t.can_create_parcel)||terrains[0];
   if(ready)choose(ready.id);
   selectTerrains();if(run.id && run.id===ownRunId)outputRun(run);
  }catch(err){if(alive){el('simServerStatus').textContent='SIMULATION API OFFLINE';showError('Simulation backend unavailable: '+err.message);}}
 polling=setInterval(async()=>{
  if(!alive||!el('simMap'))return;
  try{const run=await api('/runs/current');if(run.id && run.id===ownRunId)outputRun(run)}catch{};
 },1600);
}
