import {analyzeLive,drawNumericalReport,serverStatus} from './live_analysis.js';
import {icon,escapeHTML as e,nice,bodyEnglish,bodyBadge,statusBadge,featureLabels,urlFor,lineChart,histogram,sectionHeading} from './ui.js';
import {cosine,comparisonStatus,KEYS} from './analysis.js';

const NAV=[
 {id:'inicio',label:'Mission Control',icon:'grid'},
 {id:'explorador',label:'Planet Explorer',icon:'globe'},
 {id:'catalogo',label:'Terrain Catalog',icon:'layers'},
 {id:'analisis',label:'Morphological Analysis',icon:'chart'},
 {id:'comparador',label:'Planetary Comparator',icon:'compare'},
 {id:'descubrir',label:'Find Analog Sites',icon:'compass'},
 {id:'simulacion',label:'Rover Simulation',icon:'rover'},
];
let catalog={items:[],methodology:{}};
let chemistry={};
const prefs=typeof localStorage!=='undefined'?localStorage:{getItem:()=>null,setItem:()=>{}};
const s={body:'Todos',q:'',mapBody:'Tierra',mapId:'Timanfaya_ASTER',mapZoom:1,mapX:0,mapY:0,
 regionTab:'2d',analysisId:'Timanfaya_ASTER',compareA:'Timanfaya_ASTER',compareB:'',discoverId:'Jezero_MOLA',modal:null,navOpen:false,
 liveReport:null,aiReport:null,liveError:null,aiError:null,liveBusy:false,aiBusy:false,apiInfo:null,aiCheck:null,aiUseVision:false,uploadBusy:false,uploadMessage:'',statusFilter:'Todos',resultQ:'',planetIndex:0,sideCollapsed:prefs.getItem('terrarover-sidebar')==='compact',theme:'light'};
// Recorded Webots results: isolated from scientific DEM analysis state.
const sim={runs:[],selected:'',record:null,health:null,loaded:false,loading:false,detailsLoading:false,error:'',detailsError:'',requestSeq:0};
const root=document.getElementById('app');
if(document.documentElement)document.documentElement.dataset.theme='light';
const items=()=>catalog.items||[];
const item=id=>items().find(v=>v.id===id);
const mapLon=lon=>(((Number(lon)+180)%360+360)%360)-180;
const available=()=>items().filter(r=>r.status==='disponible');
const route=()=>decodeURIComponent((location.hash.replace(/^#\/?/,'')||'inicio').split('/')[0]);
const routeId=()=>decodeURIComponent(location.hash.replace(/^#\/?/,'').split('/')[1]||'');
const goto=id=>{location.hash='#/'+id};
const getPageTitle=id=>id==='region'?'Terrain Details':NAV.find(p=>p.id===id)?.label||'Mission Control';
const kpi=(label,value,foot,ico)=>`<div class="metric-tile"><div class="cap">${label}${icon(ico)}</div><strong>${value}</strong><div class="foot">${foot}</div></div>`;
function shell(){
 const active=route();
 root.innerHTML=`<div class="app-shell ${s.navOpen?'nav-open':''} ${s.sideCollapsed?'sidebar-collapsed':''}">
 <aside class="sidebar"><a class="brand" href="#/inicio" aria-label="TerraRover home"><span class="brand-emblem"><img src="assets/brand/killa-coders-transparent.png" alt="Killa Coders emblem"/></span><span class="brand-text"><span class="brand-name">TerraRover</span><span class="brand-sub">PLANETARY SYSTEMS</span></span></a>
 <div class="side-label">PLATFORM / 2026</div><nav class="nav-list" aria-label="NavegaciÃ³n principal">${NAV.map((n,i)=>`<a href="#/${n.id}" class="nav-item ${active===n.id||(active==='region'&&n.id==='catalogo')?'active':''}" aria-current="${active===n.id?'page':'false'}" title="${n.label}">${icon(n.icon)}<span>${n.label}</span><span class="nav-index">0${i+1}</span></a>`).join('')}</nav>
 <div class="sidebar-bottom"><div class="side-project"><span class="overline" style="font-size:9px">MISSION / TERRESTRIAL ANALOGUES</span><strong>From Earth to other worlds.</strong><p>Real topography Â· 5 Ã— 5 km per site</p><div class="tiny-line"><span></span></div></div><div class="status-online"><span class="pulse"></span><span>Planetary exploration Â· 2026</span></div></div></aside>
 <div class="workspace"><header class="topbar"><div class="topbar-left"><button type="button" class="round-btn collapse-btn" data-action="collapse" aria-label="Collapse or expand menu" title="Collapse / expand menu">${icon('menu')}</button><span class="topbar-caption"><span class="overline">KILLA CODERS</span><span class="topbar-divider"></span><strong>${e(getPageTitle(active))}</strong></span></div><div class="topbar-right"><button class="search-btn" data-action="search" aria-label="Search regions">${icon('search')}<span>Search region</span><kbd class="keycap">/</kbd></button><button class="round-btn" data-action="upload-public" aria-label="Submit your own DEM" title="Submit your own DEM">${icon('upload')}</button><span class="avatar" title="TerraRover">TR</span></div></header><main class="content ${active==='explorador'?'no-pad':''}" id="main-content">${pageContent(active)}</main></div></div>${s.modal?modal():''}`;
 if(active==='simulacion'&&!sim.loaded&&!sim.loading)loadSimulationRuns();
 if(active==='explorador')setupMap();
}
function pageContent(id){
 if(id==='inicio')return dashboard();
 if(id==='explorador')return explorer();
 if(id==='catalogo')return catalogPage();
 if(id==='region')return detail(routeId());
 if(id==='analisis')return analysisPage();
 if(id==='comparador')return comparePage();
 if(id==='descubrir')return discoverPage();
 if(id==='simulacion')return simulationPage();
 return dashboard();
}
const WORLDS=[
 {body:'Marte',label:'MARS / 01',name:'MARS',intro:'Decode the Red Planetâ€™s terrain.',sub:'Craters, volcanic plains and exploration regions.',image:'assets/space/mars.webp',tone:'mars',target:'#/catalogo'},
 {body:'Tierra',label:'EARTH / 02',name:'EARTH',intro:'Discover potential analog sites on Earth.',sub:'Volcanoes, deserts, salt flats and lava fields.',image:'assets/space/earth.webp',tone:'earth',target:'#/explorador'},
 {body:'Luna',label:'MOON / 03',name:'MOON',intro:'Explore a world shaped by impacts and ancient lava.',sub:'Basaltic maria, impact craters and lunar relief.',image:'assets/space/moon.webp',tone:'moon',target:'#/catalogo'}
];
function methodRibbon(){return `<div class="workflow-ribbon"><div class="workflow-name"><span class="overline">WORKFLOW</span><strong>FROM OBSERVATION TO ANALYSIS</strong></div><div class="workflow-items">${[['01','Open data'],['02','DEM Â· 5 km'],['03','Morphometry'],['04','Comparison']].map(([n,t])=>`<div class="workflow-item"><em>${n}</em><span>${t}</span></div>`).join('')}</div><button class="workflow-more" data-action="workflow" aria-label="View scientific workflow">${icon('arrow')}</button></div>`}
function dashboard(){
 const w=WORLDS[s.planetIndex];const cnt=items().filter(r=>r.body===w.body).length;
 return `<div class="mission-lead"><div class="eyebrow-line"><span class="live-dot"></span> TERRA STATION / PLANETARY ANALOG OBSERVATORY <i>2026</i></div><span class="mission-counter">EARTH  /  MARS  /  MOON</span></div>
 ${methodRibbon()}
 <section class="cinema-hero hero-${w.tone}" aria-label="Planet explorer"><div class="cosmos-stars" aria-hidden="true"></div><div class="orbital-rings" aria-hidden="true"></div><div class="cinema-copy"><span class="cinema-index">${w.label} <span class="hairline"></span> KILLA CODERS</span><div class="cinema-overline">TERRA / PLANETARY TERRAIN EXPLORER</div><h1>${w.name}</h1><p class="cinema-intro">${w.intro}</p><p class="cinema-sub">${w.sub}</p><div class="cinema-actions"><a href="${w.target}" class="btn btn-primary">Explore sites ${icon('arrow')}</a><a href="#/comparador" class="cinema-textlink">Compare terrains <span>â†—</span></a></div></div><div class="planet-container"><img class="planet-image" src="${w.image}" alt="Contextual image of ${bodyEnglish(w.body)} supplied as contextual visual reference" loading="eager"/></div><div class="planet-selection"><span class="selection-tag">SELECTED BODY</span><strong>${bodyEnglish(w.body).toUpperCase()}</strong><span>${cnt} catalogued regions</span></div><div class="world-controls"><button data-action="planet-prev" aria-label="Previous planet">${icon('chevron')}</button><span>0${s.planetIndex+1} <small>/ 03</small></span><button data-action="planet-next" aria-label="Next planet">${icon('chevron')}</button></div><div class="hero-coordinate">5,000 Ã— 5,000 m <span>FOOTPRINT PER DEM</span></div></section>
 <div class="mission-statbar"><div><small>GEOSPATIAL COLLECTION</small><strong>${items().length}<span> REGIONS</span></strong></div><div><small>EARTH</small><strong>${items().filter(r=>r.body==='Tierra').length}<span> DEM</span></strong></div><div><small>MARS</small><strong>${items().filter(r=>r.body==='Marte').length}<span> DEM</span></strong></div><div><small>MOON</small><strong>${items().filter(r=>r.body==='Luna').length}<span> DEM</span></strong></div><div><small>DATASETS ON THIS WEBSITE</small><strong>${available().length}<span> AVAILABLE</span></strong></div></div>
 <section class="mission-section"><div class="section-bar"><div><span class="overline">EXPLORE / 01</span><h2>One planet. Countless landscapes.</h2><p>Browse by planet, native resolution and geomorphological context.</p></div><a class="btn btn-outline" href="#/catalogo">Open catalog ${icon('arrow')}</a></div><div class="world-grid">${WORLDS.map((p,i)=>`<a href="#/catalogo" class="world-card world-${p.tone}" data-action="world-filter" data-value="${p.body}"><img src="${p.image}" alt="${p.body}" loading="lazy"/><div class="world-card-copy"><span class="overline">EXPLORATION / 0${i+1}</span><h3>${p.body.toUpperCase()}</h3><p>${p.sub}</p><span class="world-link">${items().filter(r=>r.body===p.body).length} regions ${icon('arrow')}</span></div></a>`).join('')}</div></section>
 <section class="mission-section technical-highlight"><div><span class="overline">TERRAIN INTELLIGENCE / 02</span><h2>From pixels<br/>to terrain science.</h2><p>Go beyond imagery with real elevation grids, terrain profiles, slopes, roughness and interactive 3D models.</p><a class="btn btn-primary" href="#/analisis">Enter the lab ${icon('arrow')}</a></div><div class="technical-illustration"><img src="assets/timanfaya-relief.webp" alt="Real elevation visualization from Timanfaya" loading="lazy"/><div class="mesh-tag">ELEVATION / DIGITAL TERRAIN MODEL</div><div class="scanline" aria-hidden="true"></div></div></section>
 <div class="partner-signature"><img src="assets/brand/killa-coders-transparent.png" alt="Killa Coders logo"/><div><strong>Built by Killa Coders</strong><small>Planetary analog research Â· TerraRover</small></div><img class="nasa-event" src="assets/brand/space-apps-transparent.png" alt="NASA Space Apps Challenge event logo"/></div><div class="mission-footer"><span>TR / KILLA CODERS</span><span>SCIENTIFIC PLATFORM Â· GEOSPATIAL DATA</span><span>EST. 2026</span></div>`;
}
function filteredItems(){let q=s.q.trim().toLocaleLowerCase('es');return items().filter(r=>(s.body==='Todos'||r.body===s.body)&&(!q||`${r.title} ${r.id} ${r.source} ${r.body}`.toLocaleLowerCase('es').includes(q)))}
function card(r){const asset=r.assets?.['Mapa_2D.png'];return `<article class="region-card"><div class="region-art ${r.body==='Marte'?'mars':r.body==='Luna'?'moon':''}">${asset?`<img loading="lazy" src="${urlFor(asset)}" alt="Topographic map of ${e(r.title)}"/>`:''}<div class="region-art-top">${bodyBadge(r.body)}</div><div class="region-art-bottom">${asset?'DEM Â· 5 Ã— 5 KM':'DATA NOT YET AVAILABLE'}</div></div><div class="region-content"><h3>${e(r.title)}</h3><div class="region-meta">${icon('layers')} ${e(r.source)} Â· ${r.lat===null?'Center not specified':`${nice(r.lat,2)}Â°, ${nice(r.lon,2)}Â°`}</div><div class="region-stat-line"><div><b>${nice(r.native_resolution_m,1)} m</b><small>Approx. native spacing</small></div><div><b>${r.elevation_max_m!=null?nice(r.elevation_max_m-r.elevation_min_m,1)+' m':'â€”'}</b><small>Reported relief</small></div></div><div class="region-footer">${statusBadge(r.status)}<a href="#/region/${encodeURIComponent(r.id)}" aria-label="Open details of ${e(r.title)}">Details ${icon('arrow')}</a></div></div></article>`}
function catalogPage(){return `<div class="page-heading"><div><div class="overline">GEOSPATIAL DATA LIBRARY</div><h1>Terrain Catalog</h1><p>Explore published planetary terrain data, inspect their elevation models, and find potential analog sites.</p></div><button class="btn btn-outline" data-action="upload-public">${icon('upload')} Submit your DEM</button></div><div class="catalog-toolbar"><div class="catalog-filters">${['Todos','Tierra','Marte','Luna'].map(v=>`<button class="filter-btn ${s.body===v?'on':''}" data-action="filter" data-value="${v}">${({'Todos':'All','Tierra':'Earth','Marte':'Mars','Luna':'Moon'}[v]||v)}${v==='Todos'?` Â· ${items().length}`:''}</button>`).join('')}</div><label class="input-wrap">${icon('search')}<input type="search" id="catalogSearch" value="${e(s.q)}" placeholder="Search by name or sourceâ€¦" autocomplete="off" aria-label="Search catalog"/></label></div><div class="tagline" style="margin-bottom:16px"><span id="catalogCount">${filteredItems().length}</span> regions Â· Each preview uses available terrain data; unpublished datasets are clearly marked.</div><div class="catalog-cards" id="catalogItems">${filteredItems().map(card).join('')||`<div class="chart-empty">No matching regions.</div>`}</div>`}
function explorer(){let arr=items().filter(r=>r.body===s.mapBody),r=item(s.mapId);if(!r||r.body!==s.mapBody)r=arr[0];return `<div class="explorer-layout"><aside class="map-side"><div class="map-side-header"><div class="overline">GEOSPATIAL EXPLORER</div><h2>${bodyEnglish(s.mapBody)} Â· Regions</h2><p>${arr.length} reference locations. Select a site to inspect its data sheet.</p></div><div class="map-list">${arr.map((v,i)=>`<button class="map-list-btn ${v.id===r?.id?'selected':''}" data-action="mapselect" data-value="${e(v.id)}"><span class="map-list-num">${String(i+1).padStart(2,'0')}</span><span><b>${e(v.title)}</b><small>${e(v.source)} Â· ${r.status==='disponible'?'Elevation data available':'Dataset pending'}</small></span></button>`).join('')}</div></aside>
 <section class="map-panel" aria-label="Interactive regional map"><div class="map-toolbar"><div class="segment" aria-label="Select planet">${['Tierra','Marte','Luna'].map(b=>`<button data-action="mapbody" data-value="${b}" class="${s.mapBody===b?'current':''}">${({'Tierra':'Earth','Marte':'Mars','Luna':'Moon'}[b]||b)}</button>`).join('')}</div><span class="pill" class="map-roi-label">${icon('target')} ROI Â· 5 Ã— 5 km</span></div><div class="map-canvas" id="mapCanvas" aria-label="Interactive region locator"><div class="map-stage" id="mapStage" style="transform:translate(${s.mapX}px,${s.mapY}px) scale(${s.mapZoom})">${s.mapBody==='Tierra'?`<img src="./assets/earth-vector.svg" draggable="false" alt="Vector basemap of Earth"/>`:`<div class="planet-map-bg ${s.mapBody==='Luna'?'moon':''}"></div>`}${arr.filter(v=>v.lat!==null&&v.lon!==null&&Number.isFinite(Number(v.lat))&&Number.isFinite(Number(v.lon))).map(v=>`<button class="map-marker ${v.id===r?.id?'selected':''}" style="left:${(mapLon(v.lon)+180)/360*100}%;top:${(90-Number(v.lat))/180*100}%" data-action="mapselect" data-value="${e(v.id)}" aria-label="Explore ${e(v.title)}"><span class="marker-tooltip">${e(v.title)}</span></button>`).join('')}</div></div><div class="map-zoom"><button data-action="zoom" data-value="+" aria-label="Zoom in">${icon('zoom')}</button><button data-action="zoom" data-value="-" aria-label="Zoom out">${icon('minus')}</button><button data-action="zoom" data-value="0" aria-label="Reset zoom">${icon('target')}</button></div><div class="mobile-map-selection"><div><strong>${e(r?.title||'')}</strong><small>${e(r?.source||'')} Â· ${e(bodyEnglish(r?.body||''))}</small></div><a class="btn btn-primary btn-sm" href="#/region/${encodeURIComponent(r?.id||'')}">View details ${icon('arrow')}</a></div><div class="map-overlay-bottom"><div class="map-caption"><b>${s.mapBody==='Tierra'?'Natural Earth vector basemap':'Schematic coordinate map'}</b>${s.mapBody==='Tierra'?'Approximate site locations; no high-resolution satellite imagery is implied.':'Decorative planet background â€” not a scientific terrain map.'}</div><span class="map-coords">DRAG Â· SCROLL TO ZOOM</span></div></section><aside class="map-details">${r?mapDetails(r):''}</aside></div>`}
function provenanceEnglish(r){
 if(r.status==='disponible')return r.user_uploaded?'Community-submitted DEM. Elevation data available; no independent scientific verification.':'Numerical elevation data available for research exploration.';
 if(r.status==='auditoria_historica')return 'Site in the research catalog; elevation dataset currently unavailable.';
 if(r.status==='cli_reportada')return 'Site in the research catalog; elevation dataset currently unavailable.';
 return 'Site listed for future research; data currently unavailable.';
}
function warningEnglish(r){
 if(r.body==='Marte')return 'MOLA native resolution is regional (~463 m/cell); no rover-scale obstacle interpretation.';
 return 'Elevation data supports topographic context only, not verified soil chemistry or safe rover navigation.';
}
function mapDetails(r){const img=r.assets?.['Mapa_2D.png'];return `<div class="detail-cover ${img?'':'no-image'}">${img?`<img src="${urlFor(img)}" alt="2D map de ${e(r.title)}"/>`:''}<span class="chip">${bodyBadge(r.body)}</span></div><div class="map-detail-body"><div class="overline">SELECTED REGION</div><h3>${e(r.title)}</h3><p>${e(provenanceEnglish(r))}</p><div style="margin-top:14px">${statusBadge(r.status)}</div><div class="spec-list">${spec('Source',r.source)}${spec('Center',r.lat==null||r.lon==null?'Not specified':`${nice(r.lat,3)}Â°, ${nice(r.lon,3)}Â°`)}${spec('Area','25 kmÂ²')}${spec('Native spacing',`${nice(r.native_resolution_m,1)} m approx.`)}${spec('Elevation range',r.elevation_min_m!=null?`${nice(r.elevation_min_m,0)} / ${nice(r.elevation_max_m,0)} m`:'Not imported')}</div><div class="map-detail-actions"><a href="#/region/${encodeURIComponent(r.id)}" class="btn btn-primary">View terrain details ${icon('arrow')}</a><a href="#/comparador" class="btn btn-outline">Open comparator ${icon('compare')}</a></div></div>`}
function spec(k,v){return `<div class="spec-row"><span>${e(k)}</span><strong>${e(v)}</strong></div>`}
function detail(id){let r=item(id);if(!r)return `<div class="chart-empty">Region not found. <a href="#/catalogo">Back to catalog</a></div>`;let img=r.assets?.['Mapa_2D.png'];let fmt=r.status==='disponible';return `<div class="page-heading"><div><div class="overline"><a href="#/catalogo" class="secondary-link">Terrain Catalog</a> / ${e(r.source)}</div><h1>Geospatial data sheet</h1><p>Dataset metadata, deliverables, terrain characterization and provenance.</p></div><a class="btn btn-outline" href="#/explorador">${icon('globe')} View on map</a></div>
 <section class="detail-hero"><div class="detail-scene">${img?`<img src="${urlFor(img)}" alt="Actual topographic map of ${e(r.title)}"/>`:`<div class="viewer-placeholder" style="height:100%">${icon('layers')}<div>Terrain preview unavailable<br/><small>Data has not yet been published</small></div></div>`}<div class="scene-caption">${img?'REAL ELEVATION MAP':'NO SCIENTIFIC IMAGERY'} Â· 5,000 m Ã— 5,000 m</div></div><div class="detail-summary"><div>${bodyBadge(r.body)} ${statusBadge(r.status)}</div><h1>${e(r.title)}</h1><p>Source ${e(r.source)}. Terrain properties depend on measurement resolution, source coverage and verification. Numeric DEMs describe elevations, not soil composition.</p><div class="detail-actions">${fmt?`<a class="btn btn-primary" href="${urlFor(r.assets['DEM.tif'])}" download>${icon('download')} Download scientific DEM</a>`:`<span class="notice">Elevation dataset not yet available</span>`}<a class="btn btn-outline" href="#/analisis">${icon('chart')} Open analysis</a></div></div></section>
 <div class="detail-tabs"><button data-action="detailtab" data-value="2d" class="${s.regionTab==='2d'?'active':''}">2D map</button><button data-action="detailtab" data-value="3d" class="${s.regionTab==='3d'?'active':''}">3D relief</button><button data-action="detailtab" data-value="files" class="${s.regionTab==='files'?'active':''}">Files and downloads</button></div>
 <div class="detail-grid"><div class="card">${detailView(r)}</div><div class="card"><div class="card-header"><h3>Terrain technical sheet</h3>${icon('info')}</div><div class="card-pad"><div class="spec-list" style="margin:0">${spec('Body',bodyEnglish(r.body))}${spec('Source',r.source)}${spec('Center',r.lat==null||r.lon==null?'Not specified':`${nice(r.lat,4)}Â°, ${nice(r.lon,4)}Â°`)}${spec('Extent','5,000 Ã— 5,000 m')}${spec('Native spacing',`${nice(r.native_resolution_m,2)} m approx.`)}${spec('Min. elevation',r.elevation_min_m==null?'Not available':`${nice(r.elevation_min_m,2)} m`)}${spec('Max. elevation',r.elevation_max_m==null?'Not available':`${nice(r.elevation_max_m,2)} m`)}${spec('Coverage',r.coverage_pct==null?'Not reported':`${nice(r.coverage_pct,1)} %`)}${r.crs?spec('CRS',r.crs):''}</div><div class="notice" style="margin-top:20px">${icon('warning')}<span>${e(warningEnglish(r))}</span></div></div></div></div>
 ${r.profile?`<div class="card" style="margin-top:19px"><div class="card-header"><h3>Topographic profile Â· center transect</h3><span class="card-meta">Computed from DEM.tif</span></div><div class="analysis-chart">${lineChart(r.profile)}<div class="chart-axis"><span>Central row start</span><span>Central row end</span></div></div></div>`:''}${chemistryCard(r)}`}
function chemistryCard(r){
 const entry=chemistry[r.id];
 return `<section class="chemistry-block card" aria-label="Terrain chemistry"><div class="card-header"><div><div class="overline">MATERIAL / GEOCHEMICAL CONTEXT</div><h3>Material composition</h3></div><span class="status-tag muted">${entry?'Sample-based evidence':'Data pending'}</span></div><div class="card-pad">${entry?`<p class="chemistry-description"><b>${e(entry.site)}</b> Â· ${e(entry.sample)}. ${e(entry.note)}</p><div class="chemistry-grid">${entry.rows.map(x=>`<div class="chemistry-element"><span>${e(x[0])}</span><strong>${e(x[1])}</strong></div>`).join('')}</div><div class="notice" style="margin-top:15px">${icon('warning')}<span>Bibliographic sample values provided by the team, pending source verification. These are NOT DEM measurements and do not represent the entire 5 Ã— 5 km terrain. Composition can vary between samples.</span></div>`:`<div class="empty-chem"><div class="empty-chem-icon">â—‡</div><b>Composition data not yet available</b><p>No verified chemical sample is linked to this region. DEMs encode elevation, not mineralogy.</p></div>`}</div></section>`
}
function detailView(r){if(s.regionTab==='files'){return `<div class="card-header"><h3>Deliverable package</h3><span class="card-meta">Six files per site</span></div><div class="download-grid">${['DEM.tif','Mapa_2D.tiff','Mapa_2D.png','Terreno_3D.html','Terreno_3D.obj','metadatos.json'].map(f=>{let path=r.assets?.[f];return `<${path?'a':'div'} ${path?`href="${urlFor(path)}" download`:'aria-disabled="true"'} class="download-tile ${path?'':'disabled'}"><div><b>${f}</b><small>${f==='DEM.tif'?'Numeric elevation':f==='Mapa_2D.tiff'?'Georeferenced RGBA map':f==='Terreno_3D.html'?'Interactive 1:1 viewer':f.endsWith('.json')?'Metadata and source':'Supporting file'}</small></div>${icon(path?'download':'warning')}</${path?'a':'div'}>`}).join('')}</div>`}
 if(s.regionTab==='3d')return `<div class="card-header"><h3>Three-dimensional terrain viewer</h3><span class="card-meta">1:1 vertical scale Â· Plotly</span></div>${r.assets?.['Terreno_3D.html']?`<iframe class="viewer" title="Interactive 3D terrain for ${e(r.title)}" src="${urlFor(r.assets['Terreno_3D.html'])}" loading="lazy" sandbox="allow-scripts"></iframe>`:`<div class="viewer-placeholder">${icon('globe')}<p>A 3D viewer is not available for this dataset.<br/>No synthetic terrain is generated.</p></div>`}`;
 return `<div class="card-header"><h3>2D topographic map</h3><span class="card-meta">GeoTIFF Â· PNG preview</span></div>${r.assets?.['Mapa_2D.png']?`<img class="thumb-inline" src="${urlFor(r.assets['Mapa_2D.png'])}" alt="Actual 2D topographic map of ${e(r.title)}"/>`:`<div class="viewer-placeholder">${icon('layers')}<p>A topographic preview is not yet available for this site.</p></div>`}`;
}
function analysisPage(){let integrated=available();let r=item(s.analysisId);if(!r?.metrics)r=integrated[0]||r;return `<div class="page-heading"><div><div class="overline">TERRAIN INTELLIGENCE / MORPHOMETRY</div><h1>Terrain Analysis</h1><p>Seven computed numerical terrain features. Exploratory characterization, not a geological classification.</p></div><div class="analytic-selector"><label class="select-field"><span class="fine">Analyze a region</span><select class="select" id="analysisSelect" aria-label="Select a region"><option value="">Select terrain</option>${integrated.map(v=>`<option value="${e(v.id)}" ${r?.id===v.id?'selected':''}>${e(v.title)} Â· ${v.source}</option>`).join('')}</select></label></div></div>
 <div class="notice blue" style="margin-bottom:20px">${icon('info')}<span>These seven features are preliminary morphological descriptors. TRI/TPI depend on neighborhood window size; different ground sampling distances can make direct comparison misleading.</span></div>
 <div class="analyse-grid"><div class="card"><div class="card-header"><h3>Real terrain elevation profile</h3><span class="card-meta">${r?.metrics?e(r.title):'No published DEM'}</span></div><div class="analysis-chart"><p>Samples from DEM center row Â· vertical coordinate: meters</p>${lineChart(r?.profile)}<div class="chart-axis"><span>Start</span><span>End Â· 5 km footprint</span></div></div></div><div class="card"><div class="card-header"><h3>Elevation distribution</h3><span class="card-meta">Histogram Â· cells</span></div><div class="card-pad">${histogram(r?.histogram)}<div class="spec-list">${spec('Minimum elevation',r?.elevation_min_m!=null?`${nice(r.elevation_min_m,2)} m`:'â€”')}${spec('Maximum elevation',r?.elevation_max_m!=null?`${nice(r.elevation_max_m,2)} m`:'â€”')}${spec('Relief',r?.elevation_max_m!=null?`${nice(r.elevation_max_m-r.elevation_min_m,2)} m`:'â€”')}${spec('Coverage',r?.coverage_pct!=null?`${nice(r.coverage_pct,1)}%`:'â€”')}</div></div></div></div>
 ${sectionHeading('CHARACTERIZATION','Seven-feature morphology vector','Metrics from the teamâ€™s initial scientific algorithm.')}<div class="card"><div class="features-list">${Object.entries(featureLabels).map(([k,[label,unit]],i)=>`<div class="feature-row"><div><b><span style="font:11px monospace;color:var(--cyan);margin-right:10px">${String(i+1).padStart(2,'0')}</span> ${label}</b><small>${e(k)} Â· ${unit}</small></div><span class="metric-value">${r?.metrics?nice(r.metrics[k],5):'â€”'} ${unit==='Â°'?'Â°':''}</span></div>`).join('')}</div></div>
 <div class="notice" style="margin-top:17px">${icon('warning')}<span>DEM features depend on resolution, vertical datum, NoData and window size. They cannot establish small obstacles, soil composition or route safety. Timanfaya sea-level zero cells require particular caution.</span></div>`}
function comparePage(){const a=item(s.compareA),b=item(s.compareB),status=comparisonStatus(a,b),score=status.ok?cosine(a,b):null;let earth=items().filter(v=>v.body==='Tierra');let other=items().filter(v=>v.body!=='Tierra');return `<div class="page-heading"><div><div class="overline">PLANETARY ANALOG EXPLORER</div><h1>Planetary Comparator</h1><p>Compare terrain characteristics across Earth, Mars and the Moon without treating mathematical alignment as physical equivalence.</p></div><span class="pill">${icon('compare')} Exploratory comparison</span></div><div class="card card-pad"><div class="two-selects"><div class="select-field"><label for="cmpA">Candidate Earth terrain</label><select class="select" id="cmpA"><option value="">Choose an Earth region</option>${earth.map(v=>`<option value="${e(v.id)}" ${s.compareA===v.id?'selected':''}>${e(v.title)} (${v.source})${v.metrics?' âœ“':''}</option>`).join('')}</select></div><div class="compare-arrow">${icon('compare')}</div><div class="select-field"><label for="cmpB">Planetary reference</label><select class="select" id="cmpB"><option value="">Choose Mars or Moon site</option>${other.map(v=>`<option value="${e(v.id)}" ${s.compareB===v.id?'selected':''}>${e(v.title)} Â· ${v.body}${v.metrics?' âœ“':''}</option>`).join('')}</select></div></div></div>
 <div class="compare-result">${score!==null?`<div class="overline">${status.tier==='regional'?'REGIONAL Â· EXPLORATORY ONLY':'UNCALIBRATED COSINE INDEX'}</div><div class="number"><span class="score-value">${nice(score,4)}</span></div><span class="score-unit">cos(Î¸)</span>`:`<div class="overline">AWAITING COMPARISON</div><div class="score-empty">Awaiting numeric data</div>`}<p>${e(status.reason)}</p></div>
 <section class="cosine-explainer card"><div class="cosine-symbol">cos(Î¸)</div><div><h3>What does cosine similarity measure?</h3><p>It measures the <b>mathematical alignment</b> of two seven-dimensional feature vectors. General range: <b>âˆ’1 to +1</b>; aligned (+1), orthogonal (0), opposed (âˆ’1). Mostly positive features tend to yield 0â€“1. <b>0.90 is NOT 90% geological similarity.</b> The legacy index is not standardized or calibrated and must not be treated as a validated ranking.</p></div></section>
 <div class="compare-split"><div class="card card-pad"><div class="overline">CANDIDATE TERRAIN</div><h3 style="margin-bottom:15px">${e(a?.title||'Not selected')}</h3>${a?`${bodyBadge(a.body)} ${statusBadge(a.status)}<div class="spec-list">${spec('Source',a.source)}${spec('Resolution',nice(a.native_resolution_m,1)+' m')}${spec('Relief',a.elevation_min_m!=null?nice(a.elevation_max_m-a.elevation_min_m,1)+' m':'â€”')}</div>`:'Choose an Earth site.'}</div><div class="card card-pad"><div class="overline">PLANETARY REFERENCE</div><h3 style="margin-bottom:15px">${e(b?.title||'Not selected')}</h3>${b?`${bodyBadge(b.body)} ${statusBadge(b.status)}<div class="spec-list">${spec('Source',b.source)}${spec('Resolution',nice(b.native_resolution_m,1)+' m')}${spec('Relief',b.elevation_min_m!=null?nice(b.elevation_max_m-b.elevation_min_m,1)+' m':'â€”')}</div>`:'Choose a Mars or Moon reference.'}</div></div>
 ${a&&b?`<section class="card" style="margin-top:20px"><div class="card-header"><h3>Feature-by-feature differences</h3><span class="card-meta">Not standardized or calibrated across planets</span></div><div class="card-pad">${KEYS.map(k=>`<div class="compare-spec"><strong>${a.metrics?nice(a.metrics[k],4):'â€”'}</strong><span>${featureLabels[k][0]}</span><strong>${b.metrics?nice(b.metrics[k],4):'â€”'}</strong></div>`).join('')}</div></section>`:''}
 ${liveAnalysisPanel(a,b)}${sectionHeading('INTERPRETATION','How to interpret the result','Three requirements before claiming a validated planetary analog.')}<div class="explain-grid"><div class="card">${icon('layers')}<h3>Comparable physical scale</h3><p>Earth (~30 m), Moon (~59 m) and Mars MOLA (~463 m) cannot be compared directly for fine-scale structures.</p></div><div class="card">${icon('chart')}<h3>Cosine â‰  validation</h3><p>Seven-feature similarity is exploratory; calibration, sensitivity tests and independent geological evidence are still required.</p></div><div class="card">${icon('warning')}<h3>Know the limits</h3><p>Full GeoTIFF coverage does not guarantee terrain accuracy, obstacles or mineralogical composition.</p></div></div>`}
function liveAnalysisPanel(a,b){
 const enabled=a?.status==='disponible'&&b?.status==='disponible'&&a?.id!==b?.id;
 const current=s.liveReport?.regions?.a===a?.title&&s.liveReport?.regions?.b===b?.title;
 return `<section class="science-live card"><div class="card-header"><div><div class="overline">EVIDENCE / MORPHOLOGICAL COMPARISON</div><h3>Explore terrain differences</h3></div></div>
 <div class="card-pad"><p>Compare numeric elevation models using terrain morphology, height distributions and spatial-resolution checks. All similarity estimates are preliminary.</p>
 <div class="science-actions"><button class="btn btn-primary" data-action="runAnalysis" ${!enabled||s.liveBusy?'disabled':''}>${s.liveBusy?'Analyzing terrainâ€¦':'Analyze selected terrains'}</button></div>
 ${!enabled?'<p class="science-hint">Both regions need published numeric elevation models for this comparison.</p>':''}
 ${s.liveError?`<div class="notice science-error">${icon('warning')}<span>${e(s.liveError)}</span></div>`:''}
 ${current?drawNumericalReport(s.liveReport):''}
 <p class="science-hint">Numerical results indicate measurable terrain characteristics, not verified geology or rover-safe conditions.</p>
 </div></section>`;
}
function discoverPage(){
 const references=available().filter(r=>r.body!=='Tierra'&&r.metrics);
 const ref=item(s.discoverId)?.metrics?item(s.discoverId):references[0];
 const matches=ref?available().filter(r=>r.body==='Tierra'&&r.metrics).map(r=>({r,score:cosine(r,ref)})).filter(x=>Number.isFinite(x.score)).sort((a,b)=>b.score-a.score).slice(0,8):[];
 return `<div class="page-heading"><div><div class="overline">EARTH / MARS / MOON</div><h1>Find Analog Sites</h1><p>Select a planetary reference and explore terrestrial terrain candidates ranked by a preliminary seven-feature cosine index.</p></div><button class="btn btn-outline" data-action="upload-public">${icon('upload')} Submit a DEM</button></div>
 <section class="card card-pad"><label class="select-field" style="max-width:620px"><span>Planetary reference</span><select class="select" id="discoverSelect"><option value="">Choose a planetary region</option>${references.map(x=>`<option value="${e(x.id)}" ${ref?.id===x.id?'selected':''}>${e(x.title)} Â· ${e(bodyEnglish(x.body))}</option>`).join('')}</select></label>
 <div class="notice" style="margin-top:18px">${icon('info')}<span>These scores compare mathematical feature vectors only. They are not probabilities of geological analogy. Resolution differences, especially Mars MOLA, limit physical interpretation.</span></div></section>
 <div class="discover-results">${matches.length?matches.map((x,i)=>`<article class="card discover-card"><div><small>EARTH CANDIDATE / ${String(i+1).padStart(2,'0')}</small><h3>${e(x.r.title)}</h3><p>${e(x.r.source)} Â· ${nice(x.r.native_resolution_m,1)} m native spacing</p></div><div class="discover-score"><strong>${nice(x.score,4)}</strong><small>uncalibrated cos(Î¸)</small></div><div class="discover-actions"><a class="btn btn-outline" href="#/region/${encodeURIComponent(x.r.id)}">Terrain details ${icon('arrow')}</a><button class="btn btn-primary" data-action="compare-match" data-value="${e(x.r.id)}" data-reference="${e(ref?.id)}">Compare ${icon('compare')}</button></div></article>`).join(''):'<div class="chart-empty">Choose a published planetary reference to find potential analog sites.</div>'}</div>`;
}
/* ---------------------------------------------------------------------------
 * Webots recorded-run viewer. Uses existing /api/simulation/* GET endpoints.
 * These are historic runs, NOT real-time Webots sessions.
 * --------------------------------------------------------------------------- */
const simNumber=(value,digits=2)=>Number.isFinite(Number(value))&&value!==null&&value!==''?nice(value,digits):'â€”';
const simRunName=id=>String(id||'').replace(/_/g,' ').replace(/\bDEM\b/g,'DEM');
const simIsValidId=id=>typeof id==='string'&&/^[A-Za-z0-9_-]{1,160}$/.test(id);
const simStatusLabel=status=>({completed:'Completed',timeout_partial:'Partial Â· time limit',running:'Recorded as running',failed:'Failed',stopped:'Stopped'})[status]||String(status||'Not reported').replace(/_/g,' ');
const simMetric=(label,value,unit,foot='')=>`<div class="sim-metric"><span>${e(label)}</span><strong>${e(value)}${value==='â€”'?'':`<small> ${e(unit)}</small>`}</strong>${foot?`<p>${e(foot)}</p>`:''}</div>`;
function simBase(runId){return '/api/simulation/runs/'+encodeURIComponent(runId)}
function simRefresh(){if(route()==='simulacion')refreshOnlyPage()}
async function simJSON(url){
 const resp=await fetch(url,{headers:{Accept:'application/json'},cache:'no-store'});
 let payload;
 try{payload=await resp.json()}catch{throw new Error(`Simulation API returned a non-JSON response (HTTP ${resp.status}).`)}
 if(!resp.ok)throw new Error(payload?.detail||payload?.message||`Simulation API HTTP ${resp.status}`);
 return payload;
}
async function loadSimulationRuns(force=false){
 if(sim.loading)return;
 if(sim.loaded&&!force)return;
 sim.loading=true;sim.error='';simRefresh();
 try{
  const [list,health]=await Promise.all([
   simJSON('/api/simulation/runs'),
   simJSON('/api/simulation/health').catch(()=>null)
  ]);
  const records=Array.isArray(list?.runs)?list.runs.filter(x=>simIsValidId(x?.run_id)):[];
  sim.runs=records;sim.health=health;sim.loaded=true;
  const exists=records.some(x=>x.run_id===sim.selected);
  if(!exists){
   sim.selected=records.find(x=>x.run_id==='sample_analog_dem')?.run_id||records[0]?.run_id||'';
   sim.record=null;
  }
  sim.detailsError='';
 }catch(err){sim.error=String(err?.message||err);sim.loaded=false;sim.runs=[];sim.record=null;}
 finally{sim.loading=false;simRefresh()}
 if(sim.loaded&&sim.selected)await loadSimulationRecord(sim.selected);
}
async function loadSimulationRecord(id){
 if(!simIsValidId(id))return;
 const requestId=++sim.requestSeq;
 sim.selected=id;sim.record=null;sim.detailsError='';sim.detailsLoading=true;simRefresh();
 try{
  const data=await simJSON(simBase(id)+'/results');
  if(requestId!==sim.requestSeq)return;
  if(!data||data.run_id!==id||typeof data.result!=='object'||data.result===null||Array.isArray(data.result))throw new Error('The simulation result has an invalid format.');
  sim.record=data;
 }catch(err){if(requestId===sim.requestSeq)sim.detailsError=String(err?.message||err)}
 finally{if(requestId===sim.requestSeq){sim.detailsLoading=false;simRefresh()}}
}
function simRecordPanel(){
 if(sim.detailsLoading)return `<section class="sim-card sim-pending" role="status">${icon('refresh')} Loading recorded Webots telemetryâ€¦</section>`;
 if(sim.detailsError)return `<div class="notice science-error" role="alert">${icon('warning')} ${e(sim.detailsError)}</div>`;
 const wrapper=sim.record;
 if(!wrapper)return `<section class="sim-card sim-pending">Choose a recorded simulation to view its measured telemetry.</section>`;
 const r=wrapper.result, id=sim.selected;
 const linkCsv=wrapper.artifacts?.csv===simBase(id)+'/artifacts/csv';
 const linkPlot=wrapper.artifacts?.plot===simBase(id)+'/artifacts/plot';
 const status=String(r.simulation_status||'unknown');
 const finished=status==='completed';
 return `<section class="sim-card sim-record" aria-label="Webots telemetry">
  <div class="sim-section-heading"><div><span class="overline">WEBOTS / ARCHIVED EXPERIMENT</span><h2>${e(simRunName(r.terrain||id))}</h2><p>Rover: ${e(r.rover||'Not reported')} Â· Recorded simulation Â· ${e(simStatusLabel(status))}</p></div><span class="sim-state ${finished?'sim-done':'sim-partial'}">${icon(finished?'check':'info')} ${e(simStatusLabel(status))}</span></div>
  <div class="sim-metrics">
   ${simMetric('Distance travelled',simNumber(r.distance_travelled,3),'m','Recorded odometry')}
   ${simMetric('Mean speed',simNumber(r.average_speed,4),'m/s','From exported experiment')}
   ${simMetric('Elapsed time',simNumber(r.elapsed_time_sec,1),'s','Simulated duration')}
   ${simMetric('Route completion',simNumber(r.route_completion,2),'%','Reported by the controller')}
  </div>
  <div class="sim-section-heading sim-section-tight"><div><span class="overline">ROVER / TERRAIN DYNAMICS</span><h3>Mobility and stability</h3></div></div>
  <div class="sim-spec-grid">
   <div><span>Maximum slope</span><strong>${simNumber(r.maximum_slope,2)}Â°</strong></div>
   <div><span>Max. roll</span><strong>${simNumber(r.max_roll_deg,2)}Â°</strong></div>
   <div><span>Max. pitch</span><strong>${simNumber(r.max_pitch_deg,2)}Â°</strong></div>
   <div><span>Max. uninterrupted distance</span><strong>${simNumber(r.max_uninterrupted_distance,3)} m</strong></div>
   <div><span>Stall events</span><strong>${simNumber(r.stall_events,0)}</strong></div>
   <div><span>Stability loss events</span><strong>${simNumber(r.stability_loss_events,0)}</strong></div>
  </div>
  <div class="notice" style="margin-top:18px">${icon('info')}<span>These measurements come from a previously exported Webots run. A completed status is the controller's reported state, not an independently verified mission outcome.</span></div>
 </section>
 <section class="sim-card sim-plot-card"><div class="sim-section-heading"><div><span class="overline">EVIDENCE / SCIENTIFIC OUTPUT</span><h3>Recorded trajectory and telemetry plots</h3><p>Plots supplied by the original simulation; no generated or interpolated mission data.</p></div></div>
  ${linkPlot?`<a class="sim-plot-link" href="${simBase(id)+'/artifacts/plot'}" target="_blank" rel="noopener noreferrer" aria-label="Open full resolution Webots report"><img src="${simBase(id)+'/artifacts/plot'}" alt="Webots trajectory, velocity and stability plots for ${e(simRunName(id))}" loading="lazy"/><span>Open full-resolution plot ${icon('external')}</span></a>`:`<div class="sim-plot-missing">${icon('chart')} No validated PNG plot is available for this run.</div>`}
  <div class="sim-downloads">
    ${linkCsv?`<a class="btn btn-primary" href="${simBase(id)+'/artifacts/csv'}" download>${icon('download')} Download telemetry CSV</a>`:''}
    ${linkPlot?`<a class="btn btn-outline" href="${simBase(id)+'/artifacts/plot'}" target="_blank" rel="noopener noreferrer">${icon('external')} View PNG report</a>`:''}
    <button class="btn btn-outline" type="button" data-action="sim-json">${icon('download')} Export result JSON</button>
  </div>
 </section>`;
}
function simStyles(){return `<style>
.sim-page{display:grid;gap:18px;max-width:1480px;margin:0 auto;padding-bottom:30px}
.sim-head{display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:18px}
.sim-head .sim-label{display:inline-flex;align-items:center;gap:7px;color:#B80C09;font-size:11px;font-weight:800;letter-spacing:.12em;text-transform:uppercase}
.sim-head h1{margin:7px 0 9px}.sim-head p{max-width:750px;color:#555;font-size:14px;line-height:1.65}
.sim-runtime{display:inline-flex;align-items:center;gap:8px;border:1px solid #DEDEDE;border-radius:100px;padding:9px 13px;background:#fff;color:#303030;font-size:12px;font-weight:700}
.sim-runtime svg{width:16px;height:16px;color:#FC3C23}
.sim-card{background:#fff;border:1px solid #e2e2e2;border-radius:15px;padding:24px;min-width:0}
.sim-toolbar{display:flex;gap:16px;justify-content:space-between;align-items:flex-end;flex-wrap:wrap}
.sim-select-group{display:grid;gap:8px;flex:1 1 340px;max-width:660px}
.sim-select-group label{color:#555;font-size:12px;font-weight:700;letter-spacing:.04em}
.sim-select-group select{width:100%;min-height:44px;cursor:pointer}
.sim-toolbar-actions{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.sim-toolbar-actions .btn{min-height:44px}
.sim-section-heading{display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:16px;margin-bottom:19px}
.sim-section-heading h2{font-size:clamp(23px,2.5vw,30px);margin:5px 0 5px;overflow-wrap:anywhere}
.sim-section-heading h3{font-size:20px;margin:5px 0}
.sim-section-heading p{color:#606060;font-size:13px;line-height:1.6}
.sim-section-tight{margin-top:28px}
.sim-state{display:inline-flex;gap:6px;align-items:center;font-size:12px;font-weight:700;border-radius:100px;padding:8px 12px;white-space:normal}
.sim-state .i{height:14px;width:14px}
.sim-done{background:#eef8f1;color:#217a41}.sim-partial{background:#fff4e6;color:#94580b}
.sim-metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:11px}
.sim-metric{background:#101115;border-radius:12px;padding:18px 17px;min-height:122px;color:#fff;min-width:0}
.sim-metric>span{color:#d6d6d8;font-weight:700;font-size:12px}
.sim-metric strong{display:block;white-space:normal;overflow-wrap:anywhere;font-size:clamp(22px,2.3vw,31px);letter-spacing:-.04em;margin-top:11px}
.sim-metric small{font-size:12px;letter-spacing:normal;color:#cbcbcb}
.sim-metric p{margin-top:8px;font-size:11px;color:#b4b4b4}
.sim-spec-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}
.sim-spec-grid>div{border:1px solid #e6e6e6;background:#fafafa;border-radius:10px;padding:15px;min-width:0}
.sim-spec-grid span{display:block;font-size:12px;color:#626262;margin-bottom:7px}
.sim-spec-grid strong{font-size:21px;color:#101010;overflow-wrap:anywhere}
.sim-plot-card{margin-top:0}.sim-plot-link{display:block;border:1px solid #eee;border-radius:10px;overflow:hidden;background:#fafafa}
.sim-plot-link img{display:block;width:100%;height:auto;max-height:730px;object-fit:contain}
.sim-plot-link>span{display:flex;justify-content:center;gap:6px;padding:12px;background:#fff;color:#555;font-size:12px}
.sim-plot-link>span svg{height:15px;width:15px}
.sim-plot-missing,.sim-pending{min-height:170px;display:flex;align-items:center;justify-content:center;gap:10px;flex-direction:column;color:#6b6b6b;text-align:center}
.sim-plot-missing svg{width:35px;height:35px}.sim-downloads{display:flex;gap:10px;flex-wrap:wrap;margin-top:17px}
.sim-footnote{padding:17px 19px;border-radius:12px;border:1px solid #e6e6e6;background:#fff;color:#5b5b5b;font-size:12px;line-height:1.6}
.sim-footnote strong{color:#111}.sim-page .notice{display:flex;align-items:flex-start;gap:9px}
.sim-empty{border:1px dashed #ddd;border-radius:14px;padding:42px 18px;text-align:center;background:#fff;color:#555}
.sim-empty h3{margin-bottom:8px}.sim-empty .i{height:29px;width:29px;color:#fc3c23;margin-bottom:10px}
@media(max-width:1100px){.sim-metrics{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:650px){.sim-page{gap:13px}.sim-card{padding:16px}.sim-metrics,.sim-spec-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.sim-spec-grid strong{font-size:17px}.sim-metric{padding:15px 12px}.sim-toolbar-actions{width:100%}.sim-head h1{font-size:32px}}
@media(max-width:385px){.sim-metrics,.sim-spec-grid{grid-template-columns:1fr}}
</style>`}
function simulationPage(){return `${simStyles()}<div class="sim-page">
 <div class="sim-head"><div><span class="sim-label">${icon('rover')} WEBOTS / ROVER RESEARCH</span><h1>Rover Simulation</h1><p>Inspect authentic Sojourner rover experiments, measured mobility and terrain stability. All results below come from previously exported Webots simulations.</p></div><div class="sim-runtime">${icon('activity')} ARCHIVED RUNS Â· NOT LIVE</div></div>
 <div class="sim-card sim-toolbar"><div class="sim-select-group"><label for="simRunSelect">SELECT RECORDED EXPERIMENT</label><select id="simRunSelect" class="select" ${!sim.runs.length?'disabled':''} aria-label="Choose a recorded Webots simulation">${sim.runs.length?sim.runs.map(x=>`<option value="${e(x.run_id)}" ${sim.selected===x.run_id?'selected':''}>${e(simRunName(x.run_id))}</option>`).join(''):'<option value="">No records loaded</option>'}</select></div><div class="sim-toolbar-actions"><span class="sim-runtime">${icon('file')} ${sim.loading?'Loadingâ€¦':sim.loaded?sim.runs.length+' recorded runs':'Not loaded'}</span><button class="btn btn-outline" type="button" data-action="sim-refresh" ${sim.loading?'disabled':''}>${icon('refresh')} Refresh records</button></div></div>
 ${sim.error?`<div class="notice science-error" role="alert">${icon('warning')}<span>Could not load simulation records: ${e(sim.error)}. Confirm the simulation API endpoints in this Preview deployment.</span></div>`:''}
 ${sim.loading?`<section class="sim-card sim-pending" role="status">${icon('refresh')} Connecting to the simulation results APIâ€¦</section>`:''}
 ${!sim.loading&&!sim.error&&!sim.runs.length?`<div class="sim-empty">${icon('rover')}<h3>No recorded simulations found</h3><p>The platform will show only run data actually supplied by the simulation API.</p></div>`:''}
 ${!sim.loading&&!sim.error&&sim.runs.length?simRecordPanel():''}
 <div class="sim-footnote"><strong>Scientific scope:</strong> these outputs describe archived Webots experiments. They do not provide a live rover viewer, new simulation execution, verified planetary surface hazards or navigational safety. Live execution requires a separately deployed Webots simulation service.</div>
 </div>`;}


function modal(){
 if(s.modal==='workflow')return `<div class="modal-backdrop" role="presentation" data-action="close"><div class="modal" role="dialog" aria-modal="true" aria-label="Workflow"><div class="modal-header"><div><div class="overline">METHOD / EXPLORATORY VERSION</div><h2>From DEM to analog candidate</h2></div><button class="round-btn" data-action="close" aria-label="Close">${icon('close')}</button></div><div class="modal-body"><div class="workflow-detail">${[['01','Acquire DEMs','ASTER, NASADEM, SRTM, MOLA, SLDEM and LOLA'],['02','Prepare 5 Ã— 5 km','Metric reprojection, masks, heights and 3D viewer'],['03','Characterize','Slope, local roughness, TPI, hypsometric integral and metrics'],['04','Compare','Initial cosine score; resolution-sensitive exploratory comparisons']].map(([n,t,d])=>`<div><em>${n}</em><b>${t}</b><p>${d}</p></div>`).join('')}</div><div class="notice">${icon('warning')}<span>Scores do not prove geological equivalence. MOLA (~463 m/pixel) cannot resolve rover-sized obstacles.</span></div></div></div></div>`;
 return `<div class="modal-backdrop" role="presentation" data-action="close"><div class="modal" role="dialog" aria-modal="true" aria-label="Submit a DEM"><div class="modal-header"><div><div class="overline">COMMUNITY / OPEN TERRAIN DATA</div><h2>Submit your elevation model</h2></div><button class="round-btn" data-action="close" aria-label="Close">${icon('close')}</button></div><div class="modal-body">
 <p>Upload a <b>single-band numeric GeoTIFF</b> with a projected metric coordinate system and a 5 Ã— 5 km extent. A valid submission is listed in the community section of the terrain catalog; it will be visible to other visitors.</p>
 <form id="publicDemForm" class="community-upload-form"><label>Region or study title<input name="title" placeholder="Example: Volcanic test site" maxlength="80" required></label><label>Planet<select name="body"><option value="Tierra">Earth</option><option value="Marte">Mars</option><option value="Luna">Moon</option></select></label><label>Scientific elevation file (.tif, .tiff)<input name="file" type="file" accept=".tif,.tiff,image/tiff" required></label><label class="upload-consent"><input type="checkbox" name="public_consent" required><span>I understand my DEM and its terrain preview will be published openly in this research catalog. I confirm I have permission to share this data.</span></label><button class="btn btn-primary" type="submit" ${s.uploadBusy?'disabled':''}>${s.uploadBusy?'Checking DEMâ€¦':'Publish DEM to catalog'}</button></form>
 ${s.uploadMessage?`<div class="notice ${s.uploadBusy?'':'science-check'}" role="status">${e(s.uploadMessage)}</div>`:''}
 <p class="fine">Maximum 16 MB. Files must contain valid elevation values in meters; this process does not validate their geological accuracy. Submissions are subject to availability and moderation policies.</p></div></div></div>`;
}
function refreshOnlyPage(){document.getElementById('main-content').innerHTML=pageContent(route());if(route()==='explorador')setupMap()}
document.addEventListener('click',async ev=>{
 const n=ev.target.closest('[data-action]');if(!n)return;let action=n.dataset.action,v=n.dataset.value;
 
 if(action==='sim-refresh'){await loadSimulationRuns(true);return;}
 if(action==='sim-json'){
  if(!sim.record||!simIsValidId(sim.selected))return;
  const exportPayload={run_id:sim.selected,mode:'recorded',result:sim.record.result};
  const file=new Blob([JSON.stringify(exportPayload,null,2)],{type:'application/json'});
  const href=URL.createObjectURL(file);const a=document.createElement('a');
  a.href=href;a.download=sim.selected+'_results.json';document.body.appendChild(a);a.click();a.remove();
  setTimeout(()=>URL.revokeObjectURL(href),5000);
  return;
 }
 if(action==='runAnalysis'){
   const a=s.compareA,b=s.compareB;
   if(!a||!b||a===b)return;
   s.liveError=null;s.liveBusy=true;refreshOnlyPage();
   try{s.liveReport=await analyzeLive(a,b);}catch(error){s.liveError=error.message;}
   finally{s.liveBusy=false;refreshOnlyPage();}
   return;
 }
 if(action==='compare-match'){s.compareA=v;s.compareB=n.dataset.reference||'';s.liveReport=null;goto('comparador');return;}
 if(action==='close'){
   if(ev.target.closest('.modal')&&!ev.target.closest('button[data-action="close"]'))return;
   s.modal=null;shell();return;
 }
 if(action==='nav'){s.navOpen=!s.navOpen;shell();return}
 if(action==='collapse'){if(window.innerWidth<920){s.navOpen=!s.navOpen}else{s.sideCollapsed=!s.sideCollapsed;prefs.setItem('terrarover-sidebar',s.sideCollapsed?'compact':'full')}shell();return}
 if(action==='theme'){s.theme=s.theme==='dark'?'light':'dark';if(document.documentElement)document.documentElement.dataset.theme='light';prefs.setItem('terrarover-theme',s.theme);shell();return}
 if(action==='planet-next'||action==='planet-prev'){s.planetIndex=(s.planetIndex+(action==='planet-next'?1:2))%3;refreshOnlyPage();return}
 if(action==='workflow'){s.modal='workflow';shell();return}
 if(action==='upload-public'){s.uploadMessage='';s.modal='upload';shell();return}
 if(action==='search'){goto('catalogo');setTimeout(()=>document.getElementById('catalogSearch')?.focus(),50);return}
 if(action==='filter'){s.body=v;refreshOnlyPage();return}
 if(action==='world-filter'){ev.preventDefault();s.body=v;goto('catalogo');refreshOnlyPage();return}
 if(action==='mapbody'){s.mapBody=v;s.mapId=items().find(r=>r.body===v)?.id||'';s.mapZoom=1;s.mapX=s.mapY=0;refreshOnlyPage();return}
 if(action==='mapselect'){s.mapId=v;refreshOnlyPage();return}
 if(action==='zoom'){s.mapZoom=v==='0'?1:Math.min(5,Math.max(1,s.mapZoom*(v==='+'?1.4:1/1.4)));if(v==='0')s.mapX=s.mapY=0;updateMapTransform();return}
 if(action==='detailtab'){s.regionTab=v;refreshOnlyPage();return}
});
document.addEventListener('submit',async ev=>{
 if(ev.target.id!=='publicDemForm')return;
 ev.preventDefault();
 if(s.uploadBusy)return;
 const form=ev.target;
 const payload=new FormData(form);
 s.uploadBusy=true;s.uploadMessage='Validating numeric GeoTIFF and geographic footprintâ€¦';
 const button=form.querySelector('button[type="submit"]');
 if(button){button.disabled=true;button.textContent='Checking DEMâ€¦';}
 try{
   const response=await fetch('/api/community-upload',{method:'POST',body:payload});
   const result=await response.json().catch(()=>({}));
   if(!response.ok)throw Error(result.detail||'Upload failed. Check the numeric DEM format.');
   const updated=await fetch('./data/catalog.json',{cache:'no-store'});
   if(!updated.ok)throw Error('Submission stored, but the catalog could not be refreshed.');
   catalog=await updated.json();
   s.modal=null;s.body='Todos';s.q='';s.regionTab='2d';
   goto('region/'+encodeURIComponent(result.id));
   shell();
 }catch(err){s.uploadMessage='Could not publish DEM: '+err.message;
   s.uploadBusy=false;
   const status=form.parentElement.querySelector('[role="status"]');
   if(status){status.textContent=s.uploadMessage;}else{const n=document.createElement('p');n.className='notice science-error';n.setAttribute('role','status');n.textContent=s.uploadMessage;form.after(n);}
   if(button){button.disabled=false;button.textContent='Publish DEM to catalog';}
 }finally{s.uploadBusy=false;}
});
document.addEventListener('input',ev=>{
 if(ev.target.id==='catalogSearch'){
  s.q=ev.target.value;const dest=document.getElementById('catalogItems');if(dest)dest.innerHTML=filteredItems().map(card).join('')||'<div class="chart-empty">No matching regions.</div>';document.getElementById('catalogCount').textContent=filteredItems().length;
 }
});
document.addEventListener('change',ev=>{
 if(ev.target.id==='simRunSelect'){loadSimulationRecord(ev.target.value);return;}
 if(ev.target.id==='discoverSelect'){s.discoverId=ev.target.value;refreshOnlyPage();return;}
 if(ev.target.id==='analysisSelect'){s.analysisId=ev.target.value;refreshOnlyPage()}
 if(ev.target.id==='cmpA'){s.compareA=ev.target.value;s.liveReport=s.aiReport=null;s.liveError=s.aiError=null;refreshOnlyPage()}
 if(ev.target.id==='cmpB'){s.compareB=ev.target.value;s.liveReport=s.aiReport=null;s.liveError=s.aiError=null;refreshOnlyPage()}
});
function updateMapTransform(){const el=document.getElementById('mapStage');if(el)el.style.transform=`translate(${s.mapX}px,${s.mapY}px) scale(${s.mapZoom})`}
function setupMap(){const canvas=document.getElementById('mapCanvas');if(!canvas)return;let dragging=false,sx=0,sy=0;
 canvas.addEventListener('pointerdown',ev=>{if(ev.target.closest('.map-marker'))return;dragging=true;sx=ev.clientX-s.mapX;sy=ev.clientY-s.mapY;canvas.classList.add('dragging');canvas.setPointerCapture(ev.pointerId)});
 canvas.addEventListener('pointermove',ev=>{if(!dragging)return;s.mapX=ev.clientX-sx;s.mapY=ev.clientY-sy;updateMapTransform()});
 const end=()=>{dragging=false;canvas.classList.remove('dragging')};canvas.addEventListener('pointerup',end);canvas.addEventListener('pointercancel',end);
 canvas.addEventListener('wheel',ev=>{ev.preventDefault();s.mapZoom=Math.min(5,Math.max(1,s.mapZoom*(ev.deltaY<0?1.13:1/1.13)));updateMapTransform()},{passive:false});
}
document.addEventListener('keydown',ev=>{if(ev.key==='Escape'&&s.modal){s.modal=null;shell()}if(ev.key==='/'&&!s.modal&&!['INPUT','TEXTAREA'].includes(document.activeElement.tagName)){ev.preventDefault();goto('catalogo');setTimeout(()=>document.getElementById('catalogSearch')?.focus(),40)}});
window.addEventListener('hashchange',()=>{s.navOpen=false;if(['metodologia','resultados'].includes(route())){location.hash='#/inicio';return}window.scrollTo(0,0);shell()});
(async function init(){try{const r=await fetch('./data/catalog.json');if(!r.ok)throw Error(`HTTP ${r.status}`);catalog=await r.json();if(!Array.isArray(catalog.items))throw Error('Catalog response has no items array');try{const chemResp=await fetch('./data/chemistry.json');if(chemResp.ok)chemistry=await chemResp.json()}catch{}if(!location.hash)location.hash='#/inicio';s.apiInfo=await serverStatus();shell()}catch(err){root.innerHTML=`<div class="boot" style="flex-direction:column;padding:30px;text-align:center"><span class="boot-logo">âš </span><h2>Cannot load the catalog</h2><p>${e(err.message)}</p><p>The research catalog is temporarily unavailable. Please reload this page or try again later.</p></div>`}})();
