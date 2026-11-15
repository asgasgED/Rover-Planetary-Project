"""Dynamic plots from the two actual numeric DEMs; not from RGBA TIFFs."""
from io import BytesIO
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def comparison_png(a,b,report):
    fig,ax=plt.subplots(2,2,figsize=(11.2,8.1),dpi=125)
    fig.patch.set_facecolor('#FFFFFF')
    for i,d in enumerate([a,b]):
        v=np.where(d['mask'],d['z'],np.nan)
        # Independent color scale, explicitly marked. Different planets cannot
        # be projected to one shared physical height datum.
        im=ax[0,i].imshow(v,cmap='inferno',interpolation='nearest')
        ax[0,i].set_title(f'DEM {"A" if i==0 else "B"} · native altitude (m)')
        ax[0,i].set_xlabel(f'{d["shape"][1]} × {d["shape"][0]} cells / 5 km')
        fig.colorbar(im,ax=ax[0,i],shrink=.8,label='Original elevation (m)')
    def values(d):
        z=d['z'][d['mask']];return (z-z.min())/max(float(np.ptp(z)),1e-8)
    va,vb=values(a),values(b)
    ax[1,0].hist(va,bins=24,color='#2F28FB',alpha=.7,label='A',density=True)
    ax[1,0].hist(vb,bins=24,color='#FC3C23',alpha=.55,label='B',density=True)
    ax[1,0].legend();ax[1,0].set_title('Relative elevation distribution (not absolute height)')
    ax[1,0].set_xlabel('Normalized elevation [0..1]')
    metrics=report['feature_comparison']
    labels=['Slope mean','Slope spread','Roughness*','TPI spread*']
    keys=['pendiente_media_deg','pendiente_std_deg','tri_normalizado','tpi_std_normalizado']
    vals=[next(m for m in metrics if m['key']==k)['relative_change_pct'] for k in keys]
    ax[1,1].barh(labels,vals,color=['#2F28FB' if v>=0 else '#FC3C23' for v in vals])
    ax[1,1].axvline(0,color='#626262');ax[1,1].set_title('Difference B − A / max(|A|,|B|)')
    ax[1,1].set_xlabel('Relative contrast (%); not a calibrated effect size')
    fig.suptitle('TerraRover | Scientific terrain feature comparison',fontweight='bold',fontsize=15)
    fig.tight_layout(rect=[0,0,1,.96]);out=BytesIO();fig.savefig(out,format='png',facecolor='#FFFFFF');plt.close(fig)
    return out.getvalue()
