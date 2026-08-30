from pathlib import Path
import trimesh, numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

root=Path(__file__).resolve().parent
scene=trimesh.load(root/'assets3d/Enterprise_CV6_1942_Midway.glb',force='scene')

def color_of(g):
    m=getattr(g.visual,'material',None)
    c=getattr(m,'baseColorFactor',None)
    if c is None: return (0.35,0.4,0.43,1)
    arr=np.array(c,dtype=float)
    if arr.max()>1.5: arr/=255.0
    return tuple(arr[:4])

def render(path,elev,azim,title):
    fig=plt.figure(figsize=(15,6),dpi=170)
    ax=fig.add_subplot(111,projection='3d')
    for g in scene.geometry.values():
        tri=g.vertices[g.faces]
        pc=Poly3DCollection(tri,facecolor=color_of(g),edgecolor=(0.08,0.09,0.1,0.25),linewidth=0.08)
        ax.add_collection3d(pc)
    b=scene.bounds; center=b.mean(axis=0); span=(b[1]-b[0]).max()/2
    ax.set_xlim(center[0]-span,center[0]+span)
    ax.set_ylim(center[1]-span,center[1]+span)
    ax.set_zlim(-10,34)
    ax.set_box_aspect((5.8,1.4,1.0))
    ax.view_init(elev=elev,azim=azim)
    ax.set_axis_off(); ax.set_title(title,pad=10,fontsize=15)
    fig.tight_layout(); fig.savefig(path,bbox_inches='tight',facecolor='#c9d3da'); plt.close(fig)

render(root/'assets3d/Enterprise_CV6_1942_Midway_preview.png',18,-55,'USS Enterprise (CV-6) — v2.7 Midway 1942 Reconstruction 3D Asset Preview')
render(root/'assets3d/Enterprise_CV6_1942_Midway_side.png',4,-90,'USS Enterprise (CV-6) — Starboard Silhouette Preview')
render(root/'assets3d/Enterprise_CV6_1942_Midway_top.png',88,-90,'USS Enterprise (CV-6) — Flight Deck Plan Preview')
