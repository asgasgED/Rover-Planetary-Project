export const icons = {
  grid:'<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
  globe:'<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c-3 3-3 15 0 18M12 3c3 3 3 15 0 18"/>',
  layers:'<path d="m12 2 9 5-9 5-9-5 9-5Zm-9 10 9 5 9-5M3 17l9 5 9-5"/>',
  chart:'<path d="M3 3v18h18M7 16l4-5 4 3 5-8"/>',
  compare:'<rect x="3" y="4" width="7" height="16" rx="1"/><rect x="14" y="4" width="7" height="16" rx="1"/><path d="M12 8v8"/>',
  file:'<path d="M5 3h9l5 5v13H5zM14 3v6h5M8 13h8M8 17h8"/>',
  rover:'<rect x="5" y="8" width="14" height="8" rx="2"/><circle cx="7" cy="19" r="2"/><circle cx="17" cy="19" r="2"/><path d="M12 8V4m0 0 3-2"/>',
  book:'<rect x="4" y="3" width="17" height="18" rx="2"/><path d="M8 3v18m5-12h5m-5 4h5"/>',
  search:'<circle cx="10" cy="10" r="7"/><path d="m15 15 6 6"/>',
  arrow:'<path d="M5 12h14m-6-6 6 6-6 6"/>',
  chevron:'<path d="m9 18 6-6-6-6"/>',
  download:'<path d="M12 3v13m-5-5 5 5 5-5M4 18v3h16v-3"/>',
  filter:'<path d="M3 5h18M7 12h10M10 19h4"/>',
  clock:'<circle cx="12" cy="12" r="9"/><path d="M12 7v6l4 2"/>',
  check:'<path d="m5 12 4 4L19 6"/>',
  warning:'<path d="m12 3 10 18H2L12 3Zm0 7v4m0 3v.5"/>',
  info:'<circle cx="12" cy="12" r="9"/><path d="M12 10v7m0-11v.5"/>',
  external:'<path d="M13 4h7v7m0-7-9 9M20 13v7H4V4h7"/>',
  zoom:'<path d="M12 5v14M5 12h14"/>',
  minus:'<path d="M5 12h14"/>',
  target:'<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4"/><path d="M12 1v4m0 14v4M1 12h4m14 0h4"/>',
  moon:'<path d="M20 15A9 9 0 0 1 9 4a9 9 0 1 0 11 11Z"/>',
  rocket:'<path d="M4 14 2 21l7-2 9-9 2-8-8 2-8 10Zm6 0-3 3m2-12 5 1"/><circle cx="15" cy="9" r="2"/>',
  upload:'<path d="M12 16V3m-5 5 5-5 5 5M3 16v5h18v-5"/>',
  close:'<path d="M4 4 20 20M20 4 4 20"/>',
  menu:'<path d="M3 6h18M3 12h18M3 18h18"/>',
  eye:'<path d="M2 12c4-7 16-7 20 0-4 7-16 7-20 0Z"/><circle cx="12" cy="12" r="3"/>',
  activity:'<path d="M2 12h5l3-8 4 16 3-8h5"/>',
  link:'<path d="M9 15l6-6M8 8l-3 3a4 4 0 0 0 6 6l2-2m-2-6 2-2a4 4 0 0 1 6 6l-3 3"/>',
  compass:'<circle cx="12" cy="12" r="9"/><path d="m16 8-2 6-6 2 2-6z"/>',
  star:'<path d="m12 2 3 7 7 3-7 3-3 7-3-7-7-3 7-3z"/>',
  refresh:'<path d="M20 10a8 8 0 1 0-2 7M20 4v6h-6"/>',
  more:'<circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/>',
};
export function icon(name,cls=''){return `<svg class="i ${cls}" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.7">${icons[name]||icons.info}</svg>`}
export function escapeHTML(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
export function nice(v, digits=1){return v===null||v===undefined||!Number.isFinite(+v)?'—':Number(v).toLocaleString('en-US',{maximumFractionDigits:digits})}
export const bodyEnglish=body=>({'Tierra':'Earth','Marte':'Mars','Luna':'Moon'})[body]||body;
export function bodyBadge(body){let color=body==='Tierra'?'earth':body==='Marte'?'mars':'moon';return `<span class="body-tag ${color}"><span class="body-dot"></span>${escapeHTML(bodyEnglish(body))}</span>`}
export function statusBadge(s){const statuses={disponible:['Elevation available','ready'],auditoria_historica:['Dataset pending','neutral'],cli_reportada:['Dataset pending','info'],pendiente:['Not yet available','muted']};let [name,sty]=statuses[s]||['Unknown','muted'];return `<span class="status-tag ${sty}"><span></span>${name}</span>`}
export const featureLabels={
 integral_hipsometrica:['Hypsometric integral','dimensionless'],
 pendiente_media_deg:['Mean slope','°'],
 pendiente_std_deg:['Slope standard deviation','°'],
 asimetria_elevacion:['Elevation skewness','dimensionless'],
 razon_area_3d2d:['3D-to-2D area ratio','ratio'],
 tri_normalizado:['Local roughness proxy (TRI*)','normalized'],
 tpi_std_normalizado:['TPI window variation*','normalized'],
};
export function urlFor(path){if(!path)return '#';return './'+String(path).replace(/^\/+/, '')}
export function lineChart(values,{height=230,color='#2F28FB',fill=true,second=null,axes=true}={}){
 const a=(values||[]).map(v=>v===null?NaN:Number(v));const b=second?.map(v=>v===null?NaN:Number(v))||[];
 const nums=[...a,...b].filter(Number.isFinite);if(!nums.length)return '<div class="chart-empty">No numeric elevation samples imported.</div>';
 let min=Math.min(...nums),max=Math.max(...nums);if(min===max){min-=1;max+=1}
 let span=max-min,pad=axes?36:10,w=800,h=height,left=pad,right=w-15,bottom=h-(axes?28:10),top=15;
 const px=j=>left+(right-left)*j/Math.max(1,a.length-1),py=v=>bottom-(v-min)/span*(bottom-top);
 const draw=(arr,col)=>{
  let d='',open=false;
  arr.forEach((v,j)=>{if(Number.isFinite(v)){d+=`${open?' L':' M'} ${px(j).toFixed(2)} ${py(v).toFixed(2)}`;open=true}else{open=false}});
  return `<path d="${d}" stroke="${col}" fill="none" stroke-width="2.7" stroke-linecap="round" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>`;
 };
 const grid=axes?[0,.25,.5,.75,1].map(x=>{const y=bottom-(bottom-top)*x;return `<line x1="${left}" x2="${right}" y1="${y}" y2="${y}" stroke="#2F28FB" stroke-opacity=".17"/><text x="${left-9}" y="${y+4}" fill="#2F28FB" text-anchor="end" font-size="12">${nice(min+x*span,0)}</text>`}).join(''):'';
 const path=a.map((v,j)=>Number.isFinite(v)?[px(j),py(v)]:null).filter(Boolean);const area=fill&&path.length?`<polygon points="${path.map(p=>p.join(',')).join(' ')} ${right},${bottom} ${left},${bottom}" fill="${color}" fill-opacity=".075"/>`:'';
 return `<svg class="line-chart" role="img" aria-label="DEM elevation profile" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none">${grid}${area}${draw(a,color)}${b.length?draw(b,'#FC3E00'):''}</svg>`
}
export function histogram(data){if(!data?.counts?.length)return '<div class="chart-empty">Histogram awaits numeric data.</div>';let counts=data.counts,max=Math.max(1,...counts);return `<div class="histogram" aria-label="Elevation distribution">${counts.map((n,i)=>`<div class="hist-col" title="${nice(data.bins[i],1)} m · ${n} cells" style="height:${Math.max(3,100*n/max)}%"></div>`).join('')}</div><div class="chart-axis"><span>${nice(data.bins[0],0)} m</span><span>${nice(data.bins.at(-1),0)} m</span></div>`}
export function sectionHeading(kicker,title,desc='',end=''){return `<div class="section-heading"><div><div class="overline">${kicker}</div><h2>${title}</h2>${desc?`<p>${desc}</p>`:''}</div>${end}</div>`}
