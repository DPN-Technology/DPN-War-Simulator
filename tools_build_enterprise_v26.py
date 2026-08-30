from __future__ import annotations
import json, math, os
from pathlib import Path
import numpy as np
import trimesh
from trimesh.transformations import rotation_matrix, translation_matrix
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'assets3d'
TEX=OUT/'textures'
OUT.mkdir(exist_ok=True); TEX.mkdir(exist_ok=True)

# Visual target: late May / early June 1942 Midway configuration.
L_OVERALL=251.4
L_DECK=244.6
W_DECK=29.9
W_WATERLINE=25.4
DRAFT=7.9
DECK_Z=10.7
HANGAR_Z=5.0

COLORS={
    'hull': (39,55,64,255),
    'hull_dark': (27,39,47,255),
    'underwater': (107,48,43,255),
    'deck': (61,62,52,255),
    'deck_edge': (70,78,80,255),
    'island': (77,91,98,255),
    'island_light': (93,107,113,255),
    'metal': (89,98,102,255),
    'dark': (28,34,38,255),
    'glass': (39,69,82,210),
    'white': (205,207,198,255),
    'yellow': (202,176,92,255),
    'wood': (83,78,62,255),
}

def mat(name, rgba, rough=.72, metal=.15):
    return trimesh.visual.material.PBRMaterial(
        name=name,
        baseColorFactor=np.array(rgba, dtype=np.uint8),
        metallicFactor=float(metal),
        roughnessFactor=float(rough),
    )

MATS={k:mat(k,v, .82 if k in ('deck','wood') else .68, .05 if k in ('deck','wood','glass') else .2) for k,v in COLORS.items()}

scene=trimesh.Scene()
part_stats={}

def add(mesh, name, material='metal'):
    if not isinstance(mesh, trimesh.Trimesh):
        return
    mesh.visual.material=MATS[material]
    mesh.metadata['part_name']=name
    scene.add_geometry(mesh, node_name=name, geom_name=name)
    part_stats[name]={'vertices':int(len(mesh.vertices)),'faces':int(len(mesh.faces)),'material':material}


def box(extents, center, name, material='metal', angle_deg=0.0):
    m=trimesh.creation.box(extents=extents)
    if angle_deg:
        m.apply_transform(rotation_matrix(math.radians(angle_deg), [0,0,1]))
    m.apply_translation(center)
    add(m,name,material)
    return m


def cyl(radius, height, center, name, material='metal', sections=16, axis='z'):
    m=trimesh.creation.cylinder(radius=radius,height=height,sections=sections)
    if axis=='x': m.apply_transform(rotation_matrix(math.pi/2,[0,1,0]))
    elif axis=='y': m.apply_transform(rotation_matrix(math.pi/2,[1,0,0]))
    m.apply_translation(center)
    add(m,name,material)
    return m


def loft_hull():
    # X longitudinal, +X bow. Station loft with pronounced Yorktown-style fine bow,
    # fuller amidships sections, cruiser stern and a small amount of sheer/flare.
    xs=np.linspace(-L_OVERALL/2,L_OVERALL/2,33)
    verts=[]; rings=[]
    for x in xs:
        t=(x+L_OVERALL/2)/L_OVERALL
        # stern at t=0, bow at t=1
        stern=max(.03,min(1.0,t/.17))
        bow=max(.02,min(1.0,(1.0-t)/.19))
        fullness=min(stern,bow)
        hb=2.0+(W_WATERLINE/2-2.0)*(math.sin(fullness*math.pi/2)**.52)
        # fine waterline ends; slightly stronger flare approaching hangar deck
        sheer=1.15*(max(0.0,(t-.80)/.20)**2)+.55*(max(0.0,(.14-t)/.14)**2)
        z_keel=-DRAFT+.35*math.cos((t-.5)*math.pi)
        levels=[
            (0.0,z_keel),
            (hb*.35,-6.3),
            (hb*.67,-4.0),
            (hb*.90,-1.0),
            (hb,2.7+sheer*.35),
            (hb*1.055,5.65+sheer),
        ]
        ring=[]
        for y,z in [(-yy,zz) for yy,zz in levels[::-1]]:
            ring.append(len(verts)); verts.append([float(x),float(y),float(z)])
        for y,z in levels[1:]:
            ring.append(len(verts)); verts.append([float(x),float(y),float(z)])
        rings.append(ring)
    faces=[]; n=len(rings[0])
    for a,b in zip(rings[:-1],rings[1:]):
        for i in range(n):
            j=(i+1)%n
            faces.append([a[i],b[i],b[j]]); faces.append([a[i],b[j],a[j]])
    for ring, reverse in ((rings[0], False), (rings[-1], True)):
        rr=list(reversed(ring)) if reverse else list(ring)
        for i in range(1,len(rr)-1): faces.append([rr[0],rr[i],rr[i+1]])
    m=trimesh.Trimesh(vertices=np.array(verts),faces=np.array(faces),process=True)
    add(m,'Hull_Main','hull')
    # Narrow antifouling band visible only below the design waterline.
    lower=trimesh.creation.box(extents=[L_OVERALL*.88,W_WATERLINE*.66,.85])
    lower.apply_translation([-4,0,-7.25]); add(lower,'Hull_Antifouling_Approx','underwater')

def deck_polygon(z, thickness=.28, name='Flight_Deck'):
    # straight-deck planform with tapered bow/stern and slight corner clipping
    x0=-L_DECK/2; x1=L_DECK/2
    pts=np.array([
        [x0, -7.0],[x0+5,-12.0],[x0+16,-14.5],[x0+55,-W_DECK/2],
        [x1-28,-W_DECK/2],[x1-8,-12.5],[x1,-8.5],[x1,8.5],[x1-8,12.5],
        [x1-28,W_DECK/2],[x0+55,W_DECK/2],[x0+16,14.5],[x0+5,12.0],[x0,7.0]
    ],float)
    # extrude simple polygon using trimesh path + shapely if available; fallback triangulation fan.
    try:
        from shapely.geometry import Polygon
        m=trimesh.creation.extrude_polygon(Polygon(pts),height=thickness)
        m.apply_translation([0,0,z-thickness/2])
    except Exception:
        center=np.array([[0,0,z]])
        v=np.vstack([np.c_[pts,np.full(len(pts),z-thickness/2)],np.c_[pts,np.full(len(pts),z+thickness/2)]])
        faces=[]; n=len(pts)
        for i in range(1,n-1): faces.append([n,n+i,n+i+1])
        for i in range(1,n-1): faces.append([0,i+1,i])
        for i in range(n):
            j=(i+1)%n; faces += [[i,j,n+j],[i,n+j,n+i]]
        m=trimesh.Trimesh(v,faces,process=True)
    add(m,name,'deck')


def hangar_structure():
    # Open-sided hangar: horizontal structure + repeated frames instead of one opaque box.
    box([170.0,19.1,.22],[-1.0,0,5.95],'Hangar_Deck','dark')
    box([170.0,19.1,.24],[-1.0,0,10.12],'Hangar_Overhead','hull_dark')
    # fore/aft end bulkheads
    box([.45,19.0,4.15],[-86.0,0,8.03],'Hangar_Aft_Bulkhead','hull_dark')
    box([.45,19.0,4.15],[84.0,0,8.03],'Hangar_Fwd_Bulkhead','hull_dark')
    # gallery bands, frames, openings and catwalk edge
    for side in (-1,1):
        box([184,1.0,.58],[-1,side*10.55,8.0],f'Gallery_Band_{side}','deck_edge')
        box([178,.72,.18],[-1,side*10.92,9.88],f'Gallery_Catwalk_{side}','deck_edge')
        for n,x in enumerate(np.linspace(-83,81,22)):
            box([.24,.55,4.05],[float(x),side*10.1,8.02],f'Hangar_Frame_{side}_{n:02d}','metal')
            # knee braces make the side structure read as carrier framing, not fence posts
            m=trimesh.creation.box(extents=[2.4,.11,.11])
            m.apply_transform(rotation_matrix(math.radians(37 if side>0 else -37),[0,1,0]))
            m.apply_translation([float(x)+.72,side*10.04,9.13])
            add(m,f'Hangar_Knee_{side}_{n:02d}','metal')
    # deep dark interior slab, inset from the open sides.
    box([166,15.8,.08],[-1,0,6.06],'Hangar_Interior_Floor','dark')
    # three centerline elevators
    for i,x in enumerate((-63.0,0.0,67.0),1):
        box([11.2,8.8,.12],[x,0,DECK_Z+.11],f'Elevator_{i}','metal')
        box([11.4,.10,.08],[x,-4.45,DECK_Z+.22],f'Elevator_{i}_PortEdge','white')
        box([11.4,.10,.08],[x,4.45,DECK_Z+.22],f'Elevator_{i}_StbdEdge','white')
    # 5in gun sponsons / deck-edge platforms
    for x in (-88,-57,64,91):
        for side in (-1,1):
            box([7.0,2.7,.35],[x,side*14.45,9.75],f'GunSponson_{x}_{side}','deck_edge')

def deck_details():
    # tie-down strip impression and Midway-era distance marking cues
    for x in np.linspace(-105,108,30):
        box([.05,25.0,.025],[float(x),0,DECK_Z+.30],f'TieDown_Long_{x:.1f}','metal')
    for x in (66,72,78,84,90,96,102,108):
        box([.07,24.5,.03],[x,0,DECK_Z+.33],f'ArrestingWire_{x}','dark')
    box([220/2,0.10,.03],[-5,0,DECK_Z+.34],'Centerline','white')
    for x in (-84,-60,-36,-12,12,36,60,84):
        box([2.0,.16,.035],[x,0,DECK_Z+.36],f'DistanceMark_{x}','white')
    # deck edge catwalks/rails
    for side in (-1,1):
        box([205,.78,.12],[-1,side*15.15,9.92],f'Catwalk_{side}','deck_edge')
        for x in np.arange(-101,104,4.0):
            cyl(.025,.68,[float(x),side*15.28,10.15],f'RailPost_{side}_{x:.0f}','metal',8)
        box([205,.04,.04],[-1,side*15.28,10.82],f'RailTop_{side}','metal')


def island():
    # Starboard island centered forward of midships, based on period silhouette.
    ix,iy=31.0,11.0
    box([21.0,6.1,2.6],[ix,iy,12.0],'Island_Lower','island')
    box([16.0,5.4,2.4],[ix+1.2,iy,14.3],'Island_Mid','island')
    box([13.0,5.7,2.15],[ix+3.0,iy,16.45],'Bridge_House','island_light')
    # bridge glazing
    box([9.7,.12,.75],[ix+3.0,iy-2.92,16.65],'Bridge_Glass_Port','glass')
    # big stack aft side of island
    cyl(1.65,5.1,[ix-4.8,iy+.7,18.3],'Funnel','island',20)
    cyl(1.7,.25,[ix-4.8,iy+.7,20.95],'Funnel_Cap','dark',20)
    # mast tripod and yards
    for dx,dy in ((5.4,0),(4.4,-.9),(4.4,.9)):
        cyl(.09,8.0,[ix+dx,iy+dy,20.2],f'MastLeg_{dx}_{dy}','metal',10)
    box([8.5,.10,.10],[ix+5.0,iy,22.0],'Mast_Yard_X','metal')
    box([.10,5.4,.10],[ix+5.0,iy,20.8],'Mast_Yard_Y','metal')
    # CXAM-1-style rectangular antenna lattice approximation
    box([4.7,.08,1.2],[ix+5.0,iy,23.3],'CXAM1_Radar_Frame','metal')
    for z in (22.85,23.25,23.65):
        box([4.6,.04,.04],[ix+5.0,iy-.06,z],f'CXAM_H_{z}','metal')
    for xx in np.linspace(ix+2.9,ix+7.1,7):
        box([.04,.04,1.1],[float(xx),iy-.06,23.3],f'CXAM_V_{xx:.2f}','metal')
    # crane aft of island, searchlights
    cyl(.11,4.0,[ix-9.5,iy+1.8,14.5],'Aircraft_Crane_Post','metal',10)
    box([7.0,.18,.18],[ix-6.2,iy+1.8,17.0],'Aircraft_Crane_Boom','metal',angle_deg=18)
    for k,(x,y) in enumerate(((ix-1.2,iy-2.1),(ix+6.2,iy-2.0))):
        cyl(.55,.48,[x,y,18.2],f'Searchlight_{k}','metal',14)


def gun_5in(x,y,side,name):
    # open pedestal mount with long barrel
    cyl(.62,.5,[x,y,10.5],name+'_Base','metal',14)
    cyl(.44,.72,[x,y,11.05],name+'_Mount','island',14)
    bx=x+1.35*side
    box([2.9,.12,.12],[(x+bx)/2,y,11.35],name+'_Barrel','metal')


def gun_quad_11(x,y,heading,name):
    cyl(.55,.45,[x,y,11.05],name+'_Base','metal',14)
    box([1.4,1.1,.52],[x,y,11.5],name+'_Mount','island')
    ang=math.radians(heading); dx,dy=math.cos(ang),math.sin(ang)
    for i,off in enumerate((-0.24,-0.08,.08,.24)):
        cx=x+dx*.9-dy*off; cy=y+dy*.9+dx*off
        m=trimesh.creation.box(extents=[1.8,.045,.045]); m.apply_transform(rotation_matrix(ang,[0,0,1])); m.apply_translation([cx,cy,11.85]); add(m,name+f'_Barrel{i}','metal')


def gun_20mm(x,y,heading,name):
    cyl(.18,.28,[x,y,10.72],name+'_Pedestal','metal',10)
    ang=math.radians(heading); dx,dy=math.cos(ang),math.sin(ang)
    cx=x+dx*.42; cy=y+dy*.42
    m=trimesh.creation.box(extents=[.9,.035,.035]); m.apply_transform(rotation_matrix(ang,[0,0,1])); m.apply_translation([cx,cy,11.18]); add(m,name+'_Barrel','dark')


def armament():
    # 8 x 5"/38 singles on deck-edge galleries; approximate Yorktown-class positions.
    five=[(-88,-14.3,-1),(-57,-14.6,-1),(64,-14.6,-1),(91,-14.0,-1),(-88,14.3,1),(-57,14.6,1),(64,14.6,1),(91,14.0,1)]
    for i,(x,y,s) in enumerate(five): gun_5in(x,y,s,f'5in38_{i+1}')
    # 4 quad 1.1" mounts in Midway-era fit, with two conspicuous near island.
    quads=[(24,7.2,180),(37,7.2,180),(-55,13.8,90),(75,13.8,90)]
    for i,p in enumerate(quads): gun_quad_11(*p,f'1p1_quad_{i+1}')
    # 30 single 20mm Oerlikons: distribute along deck edge + island.
    pos=[]
    for x in np.linspace(-105,105,12): pos.append((float(x),-15.1,-90))
    for x in np.linspace(-105,105,12): pos.append((float(x),15.1,90))
    pos += [(25,8,180),(30,8,180),(35,8,180),(40,8,180),(24,14,90),(43,14,90)]
    for i,p in enumerate(pos[:30]): gun_20mm(*p,f'Oerlikon20_{i+1:02d}')


def life_rafts_and_boats():
    for side in (-1,1):
        for i,x in enumerate(np.linspace(-75,78,8)):
            box([2.6,.55,.55],[float(x),side*13.3,8.2],f'LifeRaft_{side}_{i}','wood')
    # a few ship's boats stowed near island/gallery as elongated hull-like forms
    for i,(x,y) in enumerate(((10,13.4),(17,13.4),(47,13.4))):
        m=trimesh.creation.capsule(height=5.0,radius=.62,count=[8,8]); m.apply_transform(rotation_matrix(math.pi/2,[0,1,0])); m.apply_translation([x,y,8.7]); add(m,f'ShipsBoat_{i+1}','metal')


def props():
    for y in (-5.1,-1.7,1.7,5.1):
        cyl(.45,2.5,[-L_OVERALL/2+4,y,-5.2],f'PropShaft_{y}','metal',12,axis='x')
        # hub and 3 blades
        cyl(.25,.45,[-L_OVERALL/2+2.7,y,-5.2],f'PropHub_{y}','metal',12,axis='x')
        for a in (0,120,240):
            m=trimesh.creation.box(extents=[.12,1.6,.28]); m.apply_transform(rotation_matrix(math.radians(a),[1,0,0])); m.apply_translation([-L_OVERALL/2+2.5,y,-5.2]); add(m,f'PropBlade_{y}_{a}','metal')


def aircraft_model(kind, center, heading=0, idx=1):
    x,y,z=center; scale={'F4F':1.0,'SBD':1.12,'TBD':1.18}[kind]
    matname={'F4F':'island','SBD':'hull','TBD':'island_light'}[kind]
    cyl(.34*scale,5.4*scale,[x,y,z+.65],f'{kind}_{idx}_Fuselage',matname,12,axis='x')
    box([1.0*scale,10.8*scale,.12*scale],[x,y,z+.65],f'{kind}_{idx}_Wing',matname,angle_deg=heading)
    box([.8*scale,4.2*scale,.10*scale],[x-2.0*scale,y,z+.75],f'{kind}_{idx}_Tail',matname,angle_deg=heading)
    box([1.4*scale,.12*scale,1.15*scale],[x-2.35*scale,y,z+1.25],f'{kind}_{idx}_Fin',matname,angle_deg=heading)
    cyl(.08,.9,[x+3.0*scale,y,z+.65],f'{kind}_{idx}_PropHub','dark',8,axis='x')


def create_deck_texture():
    n=1024
    img=Image.new('RGB',(n,n),(61,64,58)); d=ImageDraw.Draw(img)
    # stained planks and tie-down strip impressions
    for y in range(0,n,14):
        shadev=54+(y//14)%4*2
        d.rectangle((0,y,n,y+12),fill=(shadev+7,shadev+7,shadev+2))
        d.line((0,y,n,y),fill=(33,36,34),width=1)
    for x in range(0,n,96):
        d.rectangle((x,0,x+4,n),fill=(84,87,82))
    # worn longitudinal traffic bands
    for x in (n//2-4,n//2+4): d.line((x,0,x,n),fill=(142,137,111),width=2)
    img.save(TEX/'flight_deck_albedo.png')
    # roughness and simple normal maps
    Image.new('L',(n,n),205).save(TEX/'flight_deck_roughness.png')
    Image.new('RGB',(n,n),(128,128,255)).save(TEX/'flight_deck_normal.png')
    hull=Image.new('RGB',(512,512),(53,68,78)); hd=ImageDraw.Draw(hull)
    for y in range(0,512,64): hd.rectangle((0,y,512,y+5),fill=(48,62,72))
    hull.save(TEX/'hull_bluegray_albedo.png')
    Image.new('L',(512,512),180).save(TEX/'hull_roughness.png')


def main():
    loft_hull(); deck_polygon(DECK_Z); hangar_structure(); deck_details(); island(); armament(); life_rafts_and_boats(); props()
    # representative Midway deck park, intentionally modest so the ship model remains the focus.
    for i,(x,y,k) in enumerate(((-91,-5,'TBD'),(-82,4,'TBD'),(-64,-4,'SBD'),(-53,5,'SBD'),(-35,-5,'F4F'),(-24,4,'F4F'),(72,-4,'SBD'),(84,4,'F4F')),1):
        aircraft_model(k,(x,y,DECK_Z+.35),0,i)
    create_deck_texture()
    glb=trimesh.exchange.gltf.export_glb(scene)
    (OUT/'Enterprise_CV6_1942_Midway_EDITABLE.glb').write_bytes(glb)
    # Runtime GLB groups the hundreds of editable parts into one mesh per material to reduce draw calls.
    grouped=trimesh.Scene()
    bymat={}
    for g in scene.geometry.values():
        key=getattr(getattr(g.visual,'material',None),'name','metal') or 'metal'
        bymat.setdefault(key,[]).append(g.copy())
    for key,items in bymat.items():
        mg=trimesh.util.concatenate(items)
        mg.visual.material=MATS.get(key,MATS['metal'])
        grouped.add_geometry(mg,node_name=f'CV6_{key}',geom_name=f'CV6_{key}')
    (OUT/'Enterprise_CV6_1942_Midway.glb').write_bytes(trimesh.exchange.gltf.export_glb(grouped))
    # OBJ export from concatenated geometry keeps an easy interchange path.
    merged=trimesh.util.concatenate([g for g in scene.geometry.values()])
    (OUT/'Enterprise_CV6_1942_Midway.obj').write_text(trimesh.exchange.obj.export_obj(merged,include_normals=True,include_texture=False),encoding='utf-8')
    bounds=scene.bounds
    stats={
        'visual_target':'USS Enterprise (CV-6), late May / early June 1942, Midway configuration',
        'coordinate_system':'meters; X longitudinal (+ bow), Y starboard, Z up',
        'source_driven_dimensions_m':{'overall_length':L_OVERALL,'flight_deck_length':L_DECK,'flight_deck_width':W_DECK,'waterline_beam':W_WATERLINE,'draft':DRAFT},
        'modeled_period_details':[
            'wooden flight deck with metal tie-down strip and distance-marking cues',
            'three centerline elevators',
            'starboard island with large stack, bridge glazing, cranes/searchlights',
            'CXAM-1-style masthead radar lattice approximation',
            '8 single 5in/38 mounts',
            '4 quad 1.1in AA mounts',
            '30 single 20mm Oerlikon positions',
            'deck-edge catwalks/rails/life rafts',
            'representative F4F/SBD/TBD deck park'
        ],
        'historical_boundary':'Dimensions and named visible period features are source-driven. Exact mesh station shapes, precise gun coordinates, island compartment dimensions, camouflage RGB values and aircraft parking are reconstruction/game-art approximations pending archival plan tracing.',
        'geometry':{'editable_objects':len(scene.geometry),'runtime_material_groups':len(bymat),'vertices':int(sum(len(g.vertices) for g in scene.geometry.values())),'triangles':int(sum(len(g.faces) for g in scene.geometry.values())),'bounds_m':bounds.tolist()},
        'parts':part_stats,
    }
    (OUT/'Enterprise_CV6_1942_Midway_manifest.json').write_text(json.dumps(stats,indent=2),encoding='utf-8')
    print(json.dumps(stats['geometry'],indent=2))

if __name__=='__main__': main()
