#!/usr/bin/env python3
"""Prepara el catálogo web TerraRover desde entregables DEM 5×5 km.

Solo lectura del directorio del usuario: nunca modifica las fuentes.
Dependencias: numpy, rasterio, scipy y matplotlib (para previsualización opcional).
"""
from __future__ import annotations
import argparse, csv, json, math, shutil, sys
from pathlib import Path
import numpy as np
import rasterio
from scipy.ndimage import uniform_filter
from scipy.stats import skew

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT/'data'
SIX = ('DEM.tif','Mapa_2D.tiff','Mapa_2D.png','Terreno_3D.html','Terreno_3D.obj','metadatos.json')

# Centers: planetocentric (lon east) for Mars/Moon; WGS84 lat/lon Earth.
CENTERS = {
 'Askja_ASTER': (65.033,-16.783),'Badwater_Basin_ASTER':(36.2298,-116.7674),
 'Black_Point_Lava_Flow_ASTER':(35.7,-111.3),'Black_Point_Lava_Flow_NASADEM':(35.7,-111.3),
 'Craters_of_the_Moon_NASADEM':(43.42,-113.52),'Haughton_Crater_ASTER':(75.3775,-89.65361),
 'Kilauea_ASTER':(19.421,-155.287),'La_Joya_NASADEM':(-16.7426,-72.04305),
 'La_Joya_SRTM':(-16.7426,-72.04305),'MDRS_Utah_NASADEM':(38.4062,-110.7894),
 'MDRS_Utah_SRTM':(38.4062,-110.7894),'Salar_Atacama_NASADEM':(-23.3281,-68.1669),
 'Sunset_Crater_ASTER':(35.3711,-111.5104),'Sunset_Crater_NASADEM':(35.3711,-111.5104),
 'Timanfaya_ASTER':(29.025,-13.77),'Wadi_Rum_ASTER':(29.6397,35.4339),
 'Yungay_NASADEM':(-24.0848,-69.9151),
 'Jezero_MOLA':(18.4,77.5),'Mare_Tranquillitatis_SLDEM':(0.68,23.43),
 'Mare_Imbrium_SLDEM':(32.8,344.4),'Marius_Hills_SLDEM':(14.1,303.3),
 'Tycho_Crater_SLDEM':(-43.3,348.6),'Copernicus_Crater_SLDEM':(9.6,339.9),
 'Rima_Hadley_SLDEM':(26.13,3.63),'Shackleton_Crater_LOLA_POLAR':(-89.9,0),
 'Gale_Crater_MOLA':(-5.44,137.7),'Gale_Dunes_MOLA':(-4.66,137.4),
 'Gale_Evaporites_MOLA':(-4.8,137.45),'Meridiani_Planum_MOLA':(0.2,357.5),
 'Meridiani_Evaporites_MOLA':(-1.9483,354.47417),'Arcadia_Planitia_MOLA':(46.66,192),
 'Elysium_Volcanic_MOLA':(24.74,146.9),'Elysium_Basaltic_MOLA':(2.98,154.74)
}
PLANET = {'Jezero_MOLA':'Mars','Mare_Tranquillitatis_SLDEM':'Moon'}
MARS_NEW = {'Gale_Crater_MOLA','Gale_Dunes_MOLA','Gale_Evaporites_MOLA','Meridiani_Planum_MOLA','Meridiani_Evaporites_MOLA','Arcadia_Planitia_MOLA','Elysium_Volcanic_MOLA','Elysium_Basaltic_MOLA'}
MOON_NEW = {'Mare_Imbrium_SLDEM','Marius_Hills_SLDEM','Tycho_Crater_SLDEM','Copernicus_Crater_SLDEM','Rima_Hadley_SLDEM','Shackleton_Crater_LOLA_POLAR'}
REPORTED_RANGES = {
 'Gale_Crater_MOLA':(-3072.38,-2374.83),
 'Gale_Dunes_MOLA':(-4497.84,-4200.86),
 'Gale_Evaporites_MOLA':(-3817.48,-2549.41),
 'Meridiani_Planum_MOLA':(-1262.29,-1207.20),
 'Meridiani_Evaporites_MOLA':(-1389.26,-1378.21),
 'Arcadia_Planitia_MOLA':(-4017.82,-4004.45),
 'Elysium_Volcanic_MOLA':(12735.19,13471.52),
 'Elysium_Basaltic_MOLA':(-2729.00,-2714.26),
}


def planet(name):
    if name.endswith('_MOLA'):return 'Marte'
    if name.endswith('_SLDEM') or name.endswith('_LOLA_POLAR'):return 'Luna'
    return 'Tierra'


def source(name):
    return ('LOLA POLAR' if name.endswith('_LOLA_POLAR') else name.rsplit('_',1)[-1])


def title(name):
    suf='_LOLA_POLAR' if name.endswith('_LOLA_POLAR') else '_'+name.rsplit('_',1)[-1]
    return name.removesuffix(suf).replace('_',' ')


def default_entry(name, audit=None):
    a=audit or {}; pl=planet(name)
    state = 'auditoria_historica' if audit else 'cli_reportada' if name in MARS_NEW else 'pendiente'
    center=CENTERS.get(name,(None,None))
    elev=REPORTED_RANGES.get(name,(a.get('elevacion_min_m'),a.get('elevacion_max_m')))
    return {'id':name,'title':title(name),'body':pl,'source':source(name),
        'lat':center[0],'lon':center[1], 'area_km2':25,
        'status':state,'assets':{},'metrics':None,'profile':None,'histogram':None,
        'elevation_min_m':elev[0],'elevation_max_m':elev[1],
        'native_resolution_m':a.get('resolucion_nativa_aprox_m',463.0577 if pl=='Marte' else 59.2 if pl=='Luna' else 30.87),
        'coverage_pct':a.get('cobertura_pct'), 'anomaly_count':a.get('candidatos_anomalia'), 'verdict':a.get('veredicto','SOLO_RELIEVE_REGIONAL' if pl=='Marte' else 'SIN_VALIDACION_LOCAL'),
        'provenance':('Historical 19-region audit (source DEM not bundled)' if audit else
                      'Team-reported CLI execution (source DEM not bundled)' if name in MARS_NEW else
                      'Site catalogued; final DEM verification pending'),
        'warning':('MOLA ~463 m/cell: insufficient for rover-scale obstacles' if pl=='Marte' else
                   'Regional topography only; composition and rover mobility unverified')}


def compute_features(path:Path):
    """7 indicadores compatibles con la idea inicial del equipo.
    Advertencia: índices exploratorios, no métricas validadas de análogos.
    """
    with rasterio.open(path) as ds:
        data=ds.read(1).astype('float64'); sx,sy=map(abs,ds.res)
        valid=np.isfinite(data)
        if ds.nodata is not None: valid &= data != ds.nodata
        if not valid.any():raise ValueError('DEM sin píxeles válidos')
        if ds.crs is None:raise ValueError('DEM sin CRS')
        coverage=100.0*valid.mean()
        fill=float(np.mean(data[valid]))
        zz=np.where(valid,data,fill)
        mn,mx=float(data[valid].min()),float(data[valid].max())
        dz=max(mx-mn,1e-8)
        gy,gx=np.gradient(zz,sy,sx)
        slope_rad=np.arctan(np.hypot(gx,gy))
        tri=float(np.mean(np.abs(zz-uniform_filter(zz,size=3,mode='reflect')))/dz)
        tpi=zz-uniform_filter(zz,size=15,mode='reflect')
        sk=float(skew(data[valid])) if np.std(data[valid])>1e-10 else 0.0
        if not math.isfinite(sk):sk=0.0
        features={
          'integral_hipsometrica':float(np.mean((zz-mn)/dz)),
          'pendiente_media_deg':float(np.degrees(np.mean(slope_rad))),
          'pendiente_std_deg':float(np.degrees(np.std(slope_rad))),
          'asimetria_elevacion':sk,
          'razon_area_3d2d':float(np.mean(np.sqrt(1+gx**2+gy**2))),
          'tri_normalizado':tri,
          'tpi_std_normalizado':float(np.std(tpi)/dz),
        }
        # El perfil central representa una sección real del DEM, no un análisis de ruta.
        row=data[data.shape[0]//2,:]
        ix=np.linspace(0,len(row)-1,min(120,len(row)),dtype=int)
        profile=[None if not valid[data.shape[0]//2,int(j)] else round(float(row[int(j)]),3) for j in ix]
        edges=np.linspace(mn,mx+1e-8,19)
        hist,edges=np.histogram(data[valid],bins=edges)
        return {
          'metrics':{k:round(v,8) for k,v in features.items()},
          'profile':profile,'histogram':{'bins':[round(float((edges[j]+edges[j+1])/2),2) for j in range(18)],'counts':hist.tolist()},
          'min':mn,'max':mx,'coverage':coverage,'size':[ds.width,ds.height],
          'pixel_m':[sx,sy],'crs':str(ds.crs),'width_m':round(ds.width*sx,5),'height_m':round(ds.height*sy,5),
        }


def apply_source(entry,folder:Path,output_root:Path,source_label='entrega_5km'):
    existing=[x for x in SIX if (folder/x).is_file()]
    if len(existing) !=len(SIX):
        print(f'  [INCOMPLETO] {folder.name}: {len(existing)}/6 archivos. No se publica.')
        return False
    try:data=compute_features(folder/'DEM.tif')
    except Exception as e:
        print(f'  [ERROR] {folder.name}: {e}')
        return False
    if abs(data['width_m']-5000)>0.01 or abs(data['height_m']-5000)>0.01:
        print(f'  [RECHAZADO] {folder.name}: la extensión no es de 5×5 km')
        return False
    dst=output_root/'regions'/folder.name
    dst.mkdir(parents=True,exist_ok=True)
    for f in SIX:
        if f=='DEM.tif':
            # El DEM real se publica como descarga. En hosting público significa acceso público.
            pass
        shutil.copy2(folder/f,dst/f)
    try:metadata=json.loads((folder/'metadatos.json').read_text(encoding='utf8'))
    except Exception:metadata={}
    center=metadata.get('centro_wgs84') or metadata.get('centro_planetocentrico') or {}
    lat=center.get('lat',entry['lat']);lon=center.get('lon',center.get('lon_este',entry['lon']))
    entry.update({'lat':lat,'lon':lon,'status':'disponible','metrics':data['metrics'],
          'profile':data['profile'],'histogram':data['histogram'],
          'elevation_min_m':round(data['min'],3),'elevation_max_m':round(data['max'],3),
          'coverage_pct':round(data['coverage'],2),'size_px':data['size'],
          'pixel_m':data['pixel_m'],'crs':data['crs'],
          'native_resolution_m':metadata.get('resolucion_nativa_aproximada_m',entry['native_resolution_m']),
          'verdict':metadata.get('veredicto',entry['verdict']),
          'warning': 'Numerical DEM imported. Morphological likeness does not prove geological equivalence or rover viability.'
                 if entry['body']!='Marte' else 'MOLA supports regional topography only; small obstacles are unresolved.',
          'provenance':f'Imported from {source_label}; GeoTIFF inspected',
          'assets':{f:'data/regions/'+folder.name+'/'+f for f in SIX},
          'zero_pixels':metadata.get('elevacion_cero_pixeles',None), 'anomaly_count':metadata.get('anomalías_candidatas',entry.get('anomaly_count'))})
    return True


def build(args):
    PUBLIC.mkdir(parents=True,exist_ok=True)
    old=[]
    audit_path=args.audit
    if audit_path and audit_path.is_file():
        audit=json.loads(audit_path.read_text(encoding='utf8'))
        old=audit.get('resultados',[])
    lookup={x['carpeta']:x for x in old}
    names=sorted(set(CENTERS)|set(lookup))
    catalog={name:default_entry(name,lookup.get(name)) for name in names}
    generated=[]
    if args.source:
        if not args.source.is_dir():raise ValueError(f'No existe: {args.source}')
        for folder in sorted(args.source.iterdir()):
            if not folder.is_dir() or not (folder/'DEM.tif').is_file():continue
            if folder.name not in catalog:catalog[folder.name]=default_entry(folder.name)
            if apply_source(catalog[folder.name],folder,PUBLIC,args.source.as_posix()):generated.append(folder.name)
        js=args.source/'plotly.min.js'
        if js.is_file():shutil.copy2(js,PUBLIC/'regions'/'plotly.min.js')
    if args.demo:
        demo=Path(args.demo)
        if demo.is_dir():
            k='Timanfaya_ASTER'
            if k not in catalog:catalog[k]=default_entry(k)
            if apply_source(catalog[k],demo,PUBLIC,'DEM real compartido en conversación'):
                generated.append(k)
    # Create Plotly JS if source copy absent; may take ~1 second, ~4.7 MB.
    if generated and not (PUBLIC/'regions'/'plotly.min.js').exists():
        from plotly.offline import get_plotlyjs
        (PUBLIC/'regions'/'plotly.min.js').write_text(get_plotlyjs(),encoding='utf8')
    # Mark any regions with a local DEM but without a collected audit as unverified source.
    entries=list(catalog.values())
    body_order={'Tierra':0,'Marte':1,'Luna':2}
    entries.sort(key=lambda e:(body_order.get(e['body'],3),e['title'],e['source']))
    payload={'name':'TerraRover — Killa Coders','schema':'1.0',
      'methodology':{'algorithm':'Seven-feature terrain profile + uncalibrated cosine v0',
                     'note':'Uncalibrated cosine does not establish geological similarity. MOLA cannot support rover-scale slopes.'},
      'items':entries}
    (PUBLIC/'catalog.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')
    print('Catálogo creado:',PUBLIC/'catalog.json')
    print(f'  {len(entries)} regiones catalogadas; {sum(e["status"]=="disponible" for e in entries)} con seis archivos reales')
    if generated:print('  Publicados:',', '.join(sorted(generated)))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,help='Ruta a resultado_dem/entrega_5km completo')
    p.add_argument('--audit',type=Path,help='Ruta a auditoria.json histórica')
    p.add_argument('--demo',type=Path,help='Ruta local a una carpeta regional de ejemplo')
    a=p.parse_args()
    try:build(a)
    except Exception as e:sys.exit(f'Error: {e}')
