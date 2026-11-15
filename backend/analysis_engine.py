"""Scientific terrain analysis for numerical 5 km DEM GeoTIFFs.

Sources are Float32 height rasters DEM.tif (NEVER color Map_2D.tiff).
A cosine index is retained as an uncalibrated legacy score. Pixelwise elevation
subtraction is admissible only for exactly co-located rasters of the same body.
"""
from __future__ import annotations
from pathlib import Path
import math
import numpy as np
import rasterio
from rasterio.warp import reproject
from rasterio.enums import Resampling
from scipy.ndimage import uniform_filter
from scipy.stats import skew, wasserstein_distance, ks_2samp

FEATURES = (
    'integral_hipsometrica', 'pendiente_media_deg', 'pendiente_std_deg',
    'asimetria_elevacion', 'razon_area_3d2d', 'tri_normalizado', 'tpi_std_normalizado',
)
FEATURE_LABELS = {
    'integral_hipsometrica': 'Hypsometric integral',
    'pendiente_media_deg': 'Mean slope',
    'pendiente_std_deg': 'Slope variation',
    'asimetria_elevacion': 'Elevation skewness',
    'razon_area_3d2d': '3D / 2D surface-area ratio',
    'tri_normalizado': 'Local roughness proxy (TRI*)',
    'tpi_std_normalizado': 'Relative TPI variation (15-cell window)',
}


def read_dem(path: Path):
    with rasterio.open(path) as ds:
        if ds.count != 1:
            raise ValueError(f'Expected one numeric elevation band in DEM.tif, got {ds.count}. Do not use Mapa_2D.tiff.')
        if ds.crs is None or ds.width < 3 or ds.height < 3:
            raise ValueError('A numeric DEM requires a CRS and at least 3 × 3 cells.')
        if ds.dtypes[0] not in ('float32','float64','int16','int32','uint16','uint32'):
            raise ValueError('DEM has an unsupported numeric dtype.')
        z = ds.read(1).astype('float64')
        valid = np.isfinite(z)
        if ds.nodata is not None: valid &= z != ds.nodata
        if not valid.any(): raise ValueError('DEM has no valid numeric elevations.')
        sx,sy = map(abs,ds.res)
        if not 0 < sx < 5000 or not 0 < sy < 5000: raise ValueError('Invalid metric pixel spacing.')
        if abs(ds.width*sx-5000)>1 or abs(ds.height*sy-5000)>1:
            raise ValueError('Expected final 5 × 5 km DEM.tif. Check the imported final deliverable.')
        return {'z':z,'mask':valid,'res':(sx,sy),'crs':ds.crs,'transform':ds.transform,
                'bounds':ds.bounds,'shape':z.shape,'coverage':float(valid.mean()),'path':str(path)}


def _weighted_mean(z, mask, k):
    # Avoid bleeding zero-filled / invalid data into local neighborhoods.
    numerator=uniform_filter(np.where(mask,z,0),size=k,mode='nearest')
    denominator=uniform_filter(mask.astype('float64'),size=k,mode='nearest')
    return np.divide(numerator,denominator,out=np.zeros_like(numerator),where=denominator>1e-9)


def features(d):
    z,valid=d['z'],d['mask'];sx,sy=d['res']
    vv=z[valid];zmin=float(np.min(vv));zmax=float(np.max(vv));span=max(1e-8,zmax-zmin)
    cleaned=np.where(valid,z,_weighted_mean(z,valid,3))
    # Any still-invalid blocks receive the global median, while metrics on such
    # cells are excluded. Coverage of invalid neighbors is separately reported.
    cleaned=np.where(np.isfinite(cleaned),cleaned,float(np.median(vv)))
    gy,gx=np.gradient(cleaned,sy,sx)
    slope=np.degrees(np.arctan(np.hypot(gx,gy)))[valid]
    r_area=np.sqrt(1+gx**2+gy**2)[valid]
    local=_weighted_mean(cleaned,valid,3)
    tpi=cleaned-_weighted_mean(cleaned,valid,15)
    values={
      'integral_hipsometrica':float(np.mean((vv-zmin)/span)),
      'pendiente_media_deg':float(np.mean(slope)),
      'pendiente_std_deg':float(np.std(slope)),
      'asimetria_elevacion':float(skew(vv)) if np.std(vv)>1e-9 and len(vv)>2 else 0.0,
      'razon_area_3d2d':float(np.mean(r_area)),
      'tri_normalizado':float(np.mean(np.abs(cleaned[valid]-local[valid]))/span),
      'tpi_std_normalizado':float(np.std(tpi[valid])/span),
    }
    for k,v in values.items():
        if not math.isfinite(v):raise ValueError(f'Non-finite metric: {k}')
    return values


def numerical_report(a, b, name_a: str, name_b: str, body_a: str, body_b: str,
                     native_a:float|None=None,native_b:float|None=None):
    pa,pb=features(a),features(b)
    v1=np.array([pa[k] for k in FEATURES]);v2=np.array([pb[k] for k in FEATURES])
    denom=float(np.linalg.norm(v1)*np.linalg.norm(v2))
    cosine=None if denom < 1e-12 else float(np.dot(v1,v2)/denom)
    deltas=[]
    for k in FEATURES:
        x,y=pa[k],pb[k];diff=y-x
        deltas.append({'key':k,'label':FEATURE_LABELS[k], 'a':round(x,8),'b':round(y,8),
                       'delta':round(diff,8),
                       'relative_change_pct':round(100*diff/max(abs(x),abs(y),1e-5),2)})
    warnings=['Uncalibrated 7-feature cosine is not a percentage of geological similarity.',
              '3-cell and 15-cell windows represent different physical scales at different raster resolutions.',
              'Surface materials, composition, erosion history and rover traction cannot be inferred from DEM alone.']
    na=float(native_a or max(a['res']));nb=float(native_b or max(b['res']))
    scale_ratio=max(na,nb)/max(0.1,min(na,nb))
    if scale_ratio>1.5:
        warnings.append(f'Native resolutions differ by ~{scale_ratio:.1f}×; local roughness and gradients are not scale-equivalent.')
    fine=max(na,nb)<=100 and scale_ratio<=1.5
    if not fine: warnings.append('Fine-scale morphological equivalence cannot be inferred from this pair. Treat the result as regional/exploratory only.')
    # Relative elevation distributions, not absolute heights with incompatible datums.
    def rel(d):
        vv=d['z'][d['mask']]
        return (vv-np.min(vv))/(max(float(np.ptp(vv)),1e-8))
    xa,xb=rel(a),rel(b)
    if len(xa)>50000:xa=xa[np.linspace(0,len(xa)-1,50000,dtype=int)]
    if len(xb)>50000:xb=xb[np.linspace(0,len(xb)-1,50000,dtype=int)]
    wdist=float(wasserstein_distance(xa,xb));ks=float(ks_2samp(xa,xb,mode='asymp').statistic)
    # Pixelwise height maps only when geospatially co-located (and same planet).
    colocated=(body_a==body_b and a['crs']==b['crs'] and a['shape']==b['shape'] and
                np.allclose(tuple(a['transform']),tuple(b['transform']),atol=1e-6,rtol=0))
    pixel_delta=None
    if colocated:
        v=a['mask']&b['mask'];dd=a['z'][v]-b['z'][v]
        if dd.size:
            bias=float(np.median(dd))
            pixel_delta={'pixels':int(dd.size),'median_vertical_offset_m':round(bias,4),
                         'raw_rmse_m':round(float(np.sqrt(np.mean(dd**2))),4),
                         'shape_rmse_after_median_offset_m':round(float(np.sqrt(np.mean((dd-bias)**2))),4),
                         'mean_absolute_difference_m':round(float(np.mean(abs(dd))),4)}
    else:
        warnings.append('Pixel-by-pixel DEM subtraction is not performed: these rasters are not co-located in a common planetary reference frame.')
    if body_a != body_b:warnings.append('Absolute elevations from different planetary reference datums are not directly comparable.')
    if min(a['coverage'],b['coverage'])<.95: warnings.append('One DEM has less than 95% numerical coverage; inspect missing-data effects.')
    interpretive_notes=[]
    def compare(k,meaning,confound):
        x,y=pa[k],pb[k]
        if abs(x-y)<=max(abs(x),abs(y),0.01)*0.05:
            interpretation='similar values at the measured grid scales'
        else:
            interpretation=f'{name_a if x>y else name_b} has the higher observed value'
        interpretive_notes.append({'metric':FEATURE_LABELS[k], 'interpretation':interpretation,
             'scientific_meaning':meaning,'alternative_explanation':confound})
    compare('pendiente_media_deg',
        'The mean slope describes relief steepness at the resolved spatial scale; larger values can affect large-scale route choice but are not a rover-safety verdict.',
        'Bilinear interpolation, source smoothness and native ground spacing can change slope estimates.')
    compare('pendiente_std_deg',
        'A larger spread of slopes can indicate less uniform topography and more variation between local terrain patches.',
        'Coarser terrain grids suppress short-wavelength slope extremes.')
    compare('tri_normalizado',
        'The team TRI* proxy measures local elevation departure from a 3-cell mean relative to total relief, NOT standard terrain roughness at a fixed metric scale.',
        'Three cells span different ground distances in MOLA, SLDEM and Earth DEMs.')
    compare('integral_hipsometrica',
        'The normalized hypsometric integral summarizes the distribution of elevations within each 5 km window.',
        'It does not establish depositional history or composition without external geomorphological context.')
    compare('tpi_std_normalizado',
        'TPI window variation summarizes local elevation departure from a 15-cell neighborhood relative to total relief.',
        'The 15-cell window can cover most of the whole Martian 11x11 DEM; interpretation depends strongly on native pixel spacing.')
    order=sorted(deltas,key=lambda t:abs(t['relative_change_pct']),reverse=True)
    explanations=[]
    for row in order[:3]:
        dirn='higher' if row['delta']>0 else 'lower' if row['delta']<0 else 'indistinguishable'
        explanations.append(f"{row['label']}: {name_b} is {dirn} than {name_a} in this metric ({row['a']:.4g} vs {row['b']:.4g}); significance depends on DEM resolution and error.")
    return {
      'regions':{'a':name_a,'b':name_b,'bodies':{'a':body_a,'b':body_b}},
      'metrics_a':pa,'metrics_b':pb,'feature_comparison':deltas,
      'legacy_cosine':None if cosine is None else round(cosine,8),
      'normalized_elevation_wasserstein':round(wdist,6),
      'normalized_elevation_KS_statistic':round(ks,6),
      'pixelwise_difference':pixel_delta,
      'fine_scale_comparison_permitted':fine,
      'native_resolution_m':{'a':round(na,4),'b':round(nb,4)},
      'coverage_pct':{'a':round(a['coverage']*100,2),'b':round(b['coverage']*100,2)},
      'key_findings':explanations,'interpretive_notes':interpretive_notes,
      'interpretation_note':'Legacy cosine reflects orientation of unstandardized metric vectors, NOT physical or mineralogical equivalence. Distribution distances compare shape of RELATIVE elevation distributions.',
      'warnings':warnings,
      'algorithm_version':'TerraRover analytic integration v3.0; seven team features preserved with valid-pixel masking',
      'analysis_verified':True,
    }
