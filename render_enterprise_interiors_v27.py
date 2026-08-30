from pathlib import Path
import numpy as np, trimesh
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

root=Path(__file__).resolve().parent
mods=[
 ('Hangar — cutaway',root/'assets3d/interiors/Enterprise_CV6_1942_Hangar_Interior.glb',(20,-62),('HangarModule_Ceiling',)),
 ('Bridge / Pilot House — cutaway',root/'assets3d/interiors/Enterprise_CV6_1942_Bridge_Interior.glb',(30,-72),('Bridge_Ceiling','BridgeSide_-1','BridgeSide_1')),
 ('CIC Reconstruction — cutaway',root/'assets3d/interiors/Enterprise_CV6_1942_CIC_Interior.glb',(31,-68),('CIC_Ceiling','CIC_Wall_-1','CIC_Wall_1')),
 ('Machinery Reconstruction — cutaway',root/'assets3d/interiors/Enterprise_CV6_1942_Engineering_Interior.glb',(22,-56),('Machinery_Overhead',)),
]
def col(g):
 m=getattr(g.visual,'material',None); c=getattr(m,'baseColorFactor',None)
 if c is None:return (.35,.4,.43,1)
 a=np.array(c,dtype=float); a=a/255 if a.max()>1.5 else a
 return tuple(a[:4])

fig=plt.figure(figsize=(17,10),dpi=150)
for i,(title,path,view,skip) in enumerate(mods,1):
 s=trimesh.load(path,force='scene'); ax=fig.add_subplot(2,2,i,projection='3d')
 for name,g in s.geometry.items():
  if any(name.startswith(prefix) for prefix in skip):
   continue
  tri=g.vertices[g.faces]
  ax.add_collection3d(Poly3DCollection(tri,facecolor=col(g),edgecolor=(.04,.05,.06,.20),linewidth=.06))
 b=s.bounds; c=b.mean(axis=0); dims=b[1]-b[0]
 # Closer crop for long hangar while retaining scale cues.
 if title.startswith('Hangar'):
  ax.set_xlim(-44,44); ax.set_ylim(-11,11); ax.set_zlim(-.5,4.7); ax.set_box_aspect((88,22,9))
 else:
  span=max(dims[0],dims[1])/2
  ax.set_xlim(c[0]-span,c[0]+span); ax.set_ylim(c[1]-span,c[1]+span); ax.set_zlim(b[0,2]-.4,b[1,2]+.4)
  ax.set_box_aspect((max(1,dims[0]),max(1,dims[1]),max(1,dims[2])))
 ax.view_init(elev=view[0],azim=view[1]); ax.set_axis_off(); ax.set_title(title,fontsize=13,pad=8)
fig.suptitle('USS Enterprise CV-6 — v2.7 Streamable Interior Reconstruction Modules\nCutaway visualization; hidden arrangements remain reconstruction unless source-traced',fontsize=16)
fig.tight_layout(rect=[0,0,1,.93]); fig.savefig(root/'assets3d/Enterprise_CV6_1942_InteriorModules_preview.png',facecolor='#c9d3da',bbox_inches='tight')
