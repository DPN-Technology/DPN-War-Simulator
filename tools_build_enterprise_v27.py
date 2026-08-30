from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np
import trimesh
from trimesh.transformations import rotation_matrix
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'assets3d'
INT = OUT / 'interiors'
TEX = OUT / 'textures'
MOD = OUT / 'modules'
for p in (OUT, INT, TEX, MOD): p.mkdir(parents=True, exist_ok=True)

# Source-driven Yorktown-class / CV-6 scale target.
L_OVERALL = 251.4
L_DECK = 244.6
W_DECK = 29.9
W_WATERLINE = 25.4
DRAFT = 7.9
FLIGHT_Z = 10.72
HANGAR_FLOOR_Z = 5.95
HANGAR_CEILING_Z = 10.05

RGBA = {
    'hazegray': (70, 84, 91, 255),
    'hazegray_light': (91, 104, 110, 255),
    'hazegray_dark': (48, 61, 68, 255),
    'underwater': (104, 45, 41, 255),
    'deck_edge': (65, 75, 80, 255),
    'steel': (88, 98, 103, 255),
    'darksteel': (28, 35, 39, 255),
    'black': (20, 23, 25, 255),
    'glass': (34, 58, 68, 210),
    'wood': (67, 69, 60, 255),
    'white': (205, 206, 198, 255),
    'brass': (134, 112, 61, 255),
    'rubber': (30, 30, 29, 255),
    'red': (136, 42, 38, 255),
    'green': (54, 86, 59, 255),
    'warm_light': (255, 230, 174, 255),
    'battle_red': (198, 38, 30, 255),
}

def pbr(name, rgba, rough=.66, metal=.18, emissive=None):
    kw = dict(name=name, baseColorFactor=np.array(rgba, dtype=np.uint8), metallicFactor=float(metal), roughnessFactor=float(rough))
    if emissive is not None:
        kw['emissiveFactor'] = np.array(emissive[:3], dtype=float) / 255.0
    return trimesh.visual.material.PBRMaterial(**kw)

MATS = {k: pbr(k, v, .80 if k in ('wood','rubber') else .64, .03 if k in ('wood','glass','rubber') else .22) for k,v in RGBA.items()}
MATS['warm_light'] = pbr('warm_light', RGBA['warm_light'], .35, .0, RGBA['warm_light'])
MATS['battle_red'] = pbr('battle_red', RGBA['battle_red'], .35, .0, RGBA['battle_red'])

scene = trimesh.Scene()
part_stats = {}
part_groups = {}


def add(mesh, name, material='steel', group='exterior', preserve_visual=False):
    if not isinstance(mesh, trimesh.Trimesh):
        return mesh
    if not preserve_visual:
        mesh.visual.material = MATS[material]
    mesh.metadata['part_name'] = name
    mesh.metadata['group'] = group
    scene.add_geometry(mesh, node_name=name, geom_name=name)
    part_stats[name] = {'vertices': int(len(mesh.vertices)), 'faces': int(len(mesh.faces)), 'material': material, 'group': group}
    part_groups.setdefault(group, []).append(name)
    return mesh


def box(extents, center, name, material='steel', angle_deg=0.0, group='exterior'):
    m = trimesh.creation.box(extents=extents)
    if angle_deg:
        m.apply_transform(rotation_matrix(math.radians(angle_deg), [0,0,1]))
    m.apply_translation(center)
    return add(m, name, material, group)


def cyl(radius, height, center, name, material='steel', sections=16, axis='z', group='exterior'):
    m = trimesh.creation.cylinder(radius=radius, height=height, sections=sections)
    if axis == 'x': m.apply_transform(rotation_matrix(math.pi/2,[0,1,0]))
    elif axis == 'y': m.apply_transform(rotation_matrix(math.pi/2,[1,0,0]))
    m.apply_translation(center)
    return add(m, name, material, group)


def sphere(radius, center, name, material='steel', subdivisions=2, group='exterior'):
    m=trimesh.creation.icosphere(subdivisions=subdivisions, radius=radius)
    m.apply_translation(center)
    return add(m,name,material,group)


def beam_between(a, b, radius, name, material='steel', sections=8, group='exterior'):
    a=np.array(a,float); b=np.array(b,float); v=b-a; L=float(np.linalg.norm(v))
    if L < 1e-6: return None
    m=trimesh.creation.cylinder(radius=radius,height=L,sections=sections)
    z=np.array([0.,0.,1.]); d=v/L
    cross=np.cross(z,d); dot=float(np.clip(np.dot(z,d),-1,1))
    if np.linalg.norm(cross)>1e-7:
        m.apply_transform(rotation_matrix(math.acos(dot), cross/np.linalg.norm(cross)))
    elif dot<0: m.apply_transform(rotation_matrix(math.pi,[1,0,0]))
    m.apply_translation((a+b)/2)
    return add(m,name,material,group)


def prism_polygon(points_xy, z0, z1, name, material='steel', group='exterior'):
    pts=np.asarray(points_xy,float); n=len(pts)
    verts=np.vstack([np.c_[pts,np.full(n,z0)], np.c_[pts,np.full(n,z1)]])
    faces=[]
    # Convex/near-convex reconstruction polygons used by this builder.
    for i in range(1,n-1): faces += [[0,i+1,i],[n,n+i,n+i+1]]
    for i in range(n):
        j=(i+1)%n; faces += [[i,j,n+j],[i,n+j,n+i]]
    m=trimesh.Trimesh(verts,np.asarray(faces),process=True)
    return add(m,name,material,group)

def conical_frustum_mesh(radius_base, radius_top, height, sections=16):
    ang=np.linspace(0,2*math.pi,sections,endpoint=False)
    vb=np.c_[np.cos(ang)*radius_base,np.sin(ang)*radius_base,np.full(sections,-height/2)]
    vt=np.c_[np.cos(ang)*radius_top,np.sin(ang)*radius_top,np.full(sections,height/2)]
    verts=np.vstack([vb,vt,[[0,0,-height/2],[0,0,height/2]]])
    faces=[]; cb=2*sections; ct=cb+1
    for i in range(sections):
        j=(i+1)%sections
        faces += [[i,j,sections+j],[i,sections+j,sections+i],[cb,j,i],[ct,sections+i,sections+j]]
    return trimesh.Trimesh(verts,np.asarray(faces),process=True)

def frustum_rect(center, lower, upper, height, name, material='steel', group='exterior'):
    cx,cy,cz=center; lx,ly=lower; ux,uy=upper; z0=cz-height/2; z1=cz+height/2
    v=np.array([
      [cx-lx/2,cy-ly/2,z0],[cx+lx/2,cy-ly/2,z0],[cx+lx/2,cy+ly/2,z0],[cx-lx/2,cy+ly/2,z0],
      [cx-ux/2,cy-uy/2,z1],[cx+ux/2,cy-uy/2,z1],[cx+ux/2,cy+uy/2,z1],[cx-ux/2,cy+uy/2,z1]],float)
    f=np.array([[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]])
    return add(trimesh.Trimesh(v,f,process=True),name,material,group)


def mesh_with_uv(mesh, material, uv):
    mesh.visual = trimesh.visual.TextureVisuals(uv=np.asarray(uv,float), material=material)
    return mesh


def make_textures():
    rng=np.random.default_rng(1942)
    n=2048
    base=np.zeros((n,n,3),dtype=np.uint8)
    base[:]=[61,65,61]
    # longitudinal planks (ship X maps to U, beam to V); subtle blue-gray stain + wear.
    for y in range(n):
        plank=(y//18)%6
        base[y,:,0] = np.clip(base[y,:,0] + plank - 3,0,255)
        base[y,:,1] = np.clip(base[y,:,1] + plank - 2,0,255)
    noise=rng.normal(0,4,(n,n,1))
    base=np.clip(base+noise,0,255).astype(np.uint8)
    img=Image.fromarray(base,'RGB'); d=ImageDraw.Draw(img)
    for y in range(0,n,18): d.line((0,y,n,y),fill=(37,40,39),width=2)
    # tie-down metal strips across the planking.
    for x in range(0,n,116):
        d.rectangle((x,0,x+5,n),fill=(91,96,91))
        d.line((x+2,0,x+2,n),fill=(126,128,117),width=1)
    # worn center traffic lanes and oil/fuel stains.
    d.rectangle((n//2-11,0,n//2+11,n),fill=(91,88,74))
    for _ in range(55):
        x=int(rng.integers(40,n-40)); y=int(rng.integers(40,n-40)); r=int(rng.integers(8,45))
        d.ellipse((x-r,y-r,x+r,y+r),fill=(44,45,42))
    img=img.filter(ImageFilter.GaussianBlur(.35)); img.save(TEX/'cv6_1942_flightdeck_albedo.png')
    rough=Image.new('L',(n,n),210); rd=ImageDraw.Draw(rough)
    for x in range(0,n,116): rd.rectangle((x,0,x+5,n),fill=125)
    rough.save(TEX/'cv6_1942_flightdeck_roughness.png')
    normal=np.zeros((n,n,3),dtype=np.uint8); normal[:]=[128,128,255]
    for y in range(0,n,18): normal[max(0,y-1):min(n,y+2),:,1]=115
    Image.fromarray(normal).save(TEX/'cv6_1942_flightdeck_normal.png')

    hn=1024; h=np.zeros((hn,hn,3),dtype=np.uint8); h[:]=[61,76,84]
    h=np.clip(h+rng.normal(0,3,(hn,hn,1)),0,255).astype(np.uint8)
    hi=Image.fromarray(h,'RGB'); hd=ImageDraw.Draw(hi)
    for y in range(0,hn,96): hd.line((0,y,hn,y),fill=(49,63,70),width=2)
    for x in range(0,hn,128): hd.line((x,0,x,hn),fill=(55,68,75),width=1)
    hi.save(TEX/'cv6_1942_hull_albedo.png')
    Image.new('L',(hn,hn),182).save(TEX/'cv6_1942_hull_roughness.png')
    Image.new('RGB',(hn,hn),(128,128,255)).save(TEX/'cv6_1942_hull_normal.png')

    # interior painted steel + anti-skid deck.
    Image.new('RGB',(512,512),(75,86,90)).save(TEX/'cv6_1942_interior_steel_albedo.png')
    Image.new('L',(512,512),165).save(TEX/'cv6_1942_interior_steel_roughness.png')
    return img, hi


def build_hull(hull_img):
    xs=np.linspace(-L_OVERALL/2,L_OVERALL/2,81)
    verts=[]; rings=[]
    for x in xs:
        t=(x+L_OVERALL/2)/L_OVERALL
        # Yorktown-class reconstruction: fuller midbody, fine bow, cruiser stern, rising bow sheer.
        stern=max(.01,min(1.0,t/.18)); bow=max(.01,min(1.0,(1-t)/.215)); f=min(stern,bow)
        half=1.3+(W_WATERLINE/2-1.3)*(math.sin(f*math.pi/2)**.58)
        bow_end=max(0.0,(t-.80)/.20); stern_end=max(0.0,(.18-t)/.18)
        sheer=2.05*(bow_end**2)+.82*(stern_end**2)
        flare=1.0+0.14*bow_end
        keel_lift=5.2*(bow_end**2)+2.8*(stern_end**2)
        keel=-DRAFT+.28*math.cos((t-.5)*math.pi)+keel_lift
        levels=[
            (0.0,keel),
            (half*.25,-6.5+keel_lift*.84),
            (half*.52,-5.0+keel_lift*.67),
            (half*.74,-3.2+keel_lift*.46),
            (half*.92,-.8+keel_lift*.20),
            (half,2.5+sheer*.28),
            (half*1.06*flare,5.65+sheer),
        ]
        ring=[]
        # Raked bow stem and rounded cruiser-stern cue: lower sections terminate inboard of upper hull.
        def x_profile(zv):
            q=np.clip((zv+7.9)/15.6,0.0,1.0)
            return x - 5.2*bow_end*(1.0-q) + 2.6*stern_end*(1.0-q)
        for y,z in [(-yy,zz) for yy,zz in levels[::-1]]:
            ring.append(len(verts)); verts.append([x_profile(z),y,z])
        for y,z in levels[1:]: ring.append(len(verts)); verts.append([x_profile(z),y,z])
        rings.append(ring)
    faces=[]; n=len(rings[0])
    for a,b in zip(rings[:-1],rings[1:]):
        for i in range(n):
            j=(i+1)%n; faces += [[a[i],b[i],b[j]],[a[i],b[j],a[j]]]
    for rr in (rings[0],list(reversed(rings[-1]))):
        for i in range(1,len(rr)-1): faces.append([rr[0],rr[i],rr[i+1]])
    m=trimesh.Trimesh(np.asarray(verts),np.asarray(faces),process=True)
    u=(m.vertices[:,0]+L_OVERALL/2)/L_OVERALL; v=(m.vertices[:,2]+DRAFT)/(DRAFT+14)
    hull_mat=trimesh.visual.material.PBRMaterial(name='hull_textured',baseColorTexture=hull_img,roughnessFactor=.68,metallicFactor=.12)
    mesh_with_uv(m,hull_mat,np.c_[u,v]); add(m,'Hull_Main_Textured',preserve_visual=True,group='hull')
    # Keel / skeg / stern details.
    prism_polygon([[-22,-.3],[18,-.3],[18,.3],[-22,.3]],-7.45,-6.1,'Keel_Skeg','hazegray_dark','hull')
    # Hawse pipes + anchors, both bows.
    for side in (-1,1):
        cyl(.58,.32,[111.5,side*8.7,2.2],f'HawsePipe_{side}','darksteel',18,axis='y',group='hull')
        cyl(.18,4.0,[109.8,side*8.85,1.2],f'AnchorShank_{side}','darksteel',10,axis='z',group='hull')
        box([1.6,.18,.45],[109.8,side*8.95,-.55],f'AnchorFluke_{side}','darksteel',group='hull')
    # Shaft lines and struts.
    for y in (-5.4,-1.8,1.8,5.4):
        beam_between((-116,y,-4.7),(-124,y,-5.4),.20,f'PropShaft_{y}','steel',10,'hull')
        cyl(.31,.55,[-124.2,y,-5.4],f'PropHub_{y}','brass',14,axis='x',group='hull')
        for a in (0,120,240):
            blade=trimesh.creation.box(extents=[.11,1.65,.33]); blade.apply_transform(rotation_matrix(math.radians(a),[1,0,0])); blade.apply_translation([-124.45,y,-5.4]); add(blade,f'PropBlade_{y}_{a}','brass','hull')
    # Rudder and stern steering surface.
    prism_polygon([[-125.0,-.15],[-117.8,-.15],[-117.1,.15],[-125.0,.15]],-5.7,-1.0,'Rudder','hazegray_dark','hull')


def deck_plan_points():
    x0=-L_DECK/2; x1=L_DECK/2
    return np.array([[x0,-6.6],[x0+4,-10.7],[x0+12,-13.0],[x0+32,-14.6],[x1-28,-14.95],[x1-10,-12.5],[x1,-7.9],[x1,7.9],[x1-10,12.5],[x1-28,14.95],[x0+32,14.6],[x0+12,13.0],[x0+4,10.7],[x0,6.6]],float)


def build_flight_deck(deck_img):
    pts=deck_plan_points()
    n=len(pts); z0=FLIGHT_Z-.17; z1=FLIGHT_Z+.17
    verts=np.vstack([np.c_[pts,np.full(n,z0)],np.c_[pts,np.full(n,z1)]])
    faces=[]
    for i in range(1,n-1): faces += [[0,i+1,i],[n,n+i,n+i+1]]
    for i in range(n):
        j=(i+1)%n; faces += [[i,j,n+j],[i,n+j,n+i]]
    m=trimesh.Trimesh(verts,np.asarray(faces),process=True)
    uv=np.c_[(m.vertices[:,0]+L_DECK/2)/L_DECK,(m.vertices[:,1]+W_DECK/2)/W_DECK]
    dmat=trimesh.visual.material.PBRMaterial(name='flightdeck_textured',baseColorTexture=deck_img,roughnessFactor=.83,metallicFactor=.02)
    mesh_with_uv(m,dmat,uv); add(m,'Flight_Deck_Textured',preserve_visual=True,group='deck')
    # Deep flight deck fascia/edge beam.
    for side in (-1,1):
        box([205,.7,.58],[-1,side*15.2,10.35],f'FlightDeck_EdgeBeam_{side}','deck_edge',group='deck')
    # Three elevator platforms/opening rims.
    for i,(x,l,w) in enumerate(((-63,11.4,8.8),(0,11.8,8.9),(67,11.5,8.8)),1):
        box([l,w,.16],[x,0,FLIGHT_Z+.20],f'Elevator_{i}_Platform','steel',group='deck')
        for sy in (-1,1): box([l+.3,.10,.06],[x,sy*(w/2+.05),FLIGHT_Z+.31],f'Elevator_{i}_Side_{sy}','white',group='deck')
        for sx in (-1,1): box([.10,w+.3,.06],[x+sx*(l/2+.05),0,FLIGHT_Z+.31],f'Elevator_{i}_End_{sx}','white',group='deck')
    # Arresting gear / barriers / center markings.
    for n,x in enumerate(np.linspace(69,101,10)): box([.08,25.6,.035],[float(x),0,FLIGHT_Z+.36],f'ArrestingWire_{n:02d}','darksteel',group='deck')
    for x in (44,52): box([.09,25.0,.04],[x,0,FLIGHT_Z+.37],f'BarrierWire_{x}','darksteel',group='deck')
    box([218,.12,.035],[-3,0,FLIGHT_Z+.38],'Deck_Centerline','white',group='deck')
    for x in (-96,-72,-48,-24,0,24,48,72,96): box([1.8,.18,.04],[x,0,FLIGHT_Z+.39],f'Deck_DistanceMark_{x}','white',group='deck')
    # LSO platform aft port and deck-edge catwalks.
    box([5.2,2.2,.22],[-97,-16.1,9.85],'LSO_Platform','deck_edge',group='deck')
    for side in (-1,1):
        box([196,.95,.14],[-2,side*15.55,9.82],f'Catwalk_{side}','deck_edge',group='deck')
        # railing / safety net stanchions every 3m
        for j,x in enumerate(np.arange(-100,100.1,3.0)):
            cyl(.022,.78,[float(x),side*15.95,10.15],f'CatwalkPost_{side}_{j:02d}','steel',8,group='deck')
        box([198,.045,.045],[-1,side*15.95,10.82],f'CatwalkTopRail_{side}','steel',group='deck')
        # safety net lower rails
        box([198,.035,.035],[-1,side*15.95,10.46],f'CatwalkMidRail_{side}','steel',group='deck')


def build_hangar():
    # Open-sided hangar structure; modeled as framing and decks, not a slab.
    box([170,19.1,.22],[-1,0,HANGAR_FLOOR_Z],'Hangar_Deck','darksteel',group='hangar')
    box([170,19.1,.22],[-1,0,HANGAR_CEILING_Z],'Hangar_Overhead','hazegray_dark',group='hangar')
    box([.45,19.0,4.2],[-86,0,8.0],'Hangar_Aft_Bulkhead','hazegray_dark',group='hangar')
    box([.45,19.0,4.2],[84,0,8.0],'Hangar_Forward_Bulkhead','hazegray_dark',group='hangar')
    # side framing, open bays, gallery belts
    for side in (-1,1):
        box([183,.9,.55],[-1,side*10.55,8.0],f'GalleryBelt_{side}','deck_edge',group='hangar')
        box([180,.65,.18],[-1,side*10.95,9.82],f'GalleryWalk_{side}','deck_edge',group='hangar')
        xs=np.linspace(-83,81,29)
        for j,x in enumerate(xs):
            box([.20,.46,4.05],[float(x),side*10.1,8.02],f'HangarFrame_{side}_{j:02d}','steel',group='hangar')
            beam_between((x,side*10.0,9.82),(x+1.8,side*10.0,8.15),.045,f'HangarKneeA_{side}_{j:02d}','steel',6,'hangar')
            if j < len(xs)-1:
                # overhead transverse truss roughly every frame bay
                beam_between((x,side*9.1,9.85),(x,0,9.5),.045,f'HangarTruss_{side}_{j:02d}','steel',6,'hangar')
        # some representative roll-down curtain sections partly closed, leaving most bays open
        for k,x in enumerate((-74,-32,47,76)):
            box([4.3,.08,1.55],[x,side*10.18,9.1],f'HangarCurtain_{side}_{k}','hazegray_dark',group='hangar')
    # overhead beams, ventilation trunks, lights, fire curtain tracks.
    for j,x in enumerate(np.arange(-80,81,8.0)):
        box([.18,18.2,.18],[float(x),0,9.72],f'HangarCrossBeam_{j:02d}','steel',group='hangar')
        for y in (-5.3,0,5.3):
            cyl(.14,.9,[float(x),y,9.35],f'HangarLight_{j:02d}_{y}','warm_light',12,group='hangar')
    for side in (-1,1): box([160,.72,.62],[-1,side*6.8,9.35],f'HangarVentTrunk_{side}','hazegray_light',group='hangar')
    for x in (-41,21): box([.22,18.0,3.5],[x,0,7.9],f'FireCurtainTrack_{x}','steel',group='hangar')
    # representative aviation shops / workbenches along inboard sides.
    for side in (-1,1):
        for j,x in enumerate((-70,-54,-38,-22,36,52,68)):
            box([5.4,1.4,1.4],[x,side*7.75,6.75],f'AviationShop_{side}_{j}','hazegray',group='hangar')
            box([4.4,.75,.12],[x,side*6.75,6.55],f'Workbench_{side}_{j}','wood',group='hangar')
    # aircraft tractor / tow bars
    for j,x in enumerate((-58,18,54)):
        box([2.0,1.15,.65],[x,-2.5,6.35],f'HangarTractor_{j}','hazegray_dark',group='hangar')
        cyl(.30,.18,[x-.65,-3.0,6.10],f'HangarTractorWheelA_{j}','rubber',12,axis='y',group='hangar')
        cyl(.30,.18,[x+.65,-3.0,6.10],f'HangarTractorWheelB_{j}','rubber',12,axis='y',group='hangar')


def build_galleries_sponsons():
    # 5-inch galleries and island/AA tubs.
    for x in (-89,-58,65,92):
        for side in (-1,1):
            prism_polygon([[x-3.7,side*13.2],[x+3.7,side*13.2],[x+3.1,side*16.0],[x-3.1,side*16.0]],9.55,9.88,f'5inGallery_{x}_{side}','deck_edge','weapons')
            # semicircle impression via low-sided cylinder deck tub
            cyl(2.0,.75,[x,side*14.75,10.2],f'5inTub_{x}_{side}','hazegray',18,group='weapons')
    # Additional AA tubs / platforms.
    tubs=[(-55,-15.2),(-55,15.2),(75,-15.2),(75,15.2),(22,8.2),(39,8.2)]
    for j,(x,y) in enumerate(tubs): cyl(1.55,.6,[x,y,10.2],f'AATub_{j:02d}','hazegray',18,group='weapons')


def build_island():
    # Photo-constrained irregular island footprints; dimensions remain reconstruction.
    lower=np.array([[19.0,8.6],[43.5,8.6],[44.0,14.0],[36.0,15.0],[22.0,14.8],[18.0,12.7]])
    mid=np.array([[23.0,9.1],[42.0,9.1],[42.4,14.1],[35.0,14.7],[24.0,14.5],[21.7,12.5]])
    bridge=np.array([[27.2,8.8],[42.8,8.8],[43.6,13.8],[38.0,14.7],[28.0,14.5],[25.8,12.0]])
    prism_polygon(lower,10.72,13.25,'Island_Lower_Complex','hazegray','island')
    prism_polygon(mid,13.25,15.55,'Island_Mid_Complex','hazegray','island')
    prism_polygon(bridge,15.55,17.75,'PilotHouse_Bridge','hazegray_light','island')
    # Cantilevered open signal/flag platform aft and bridge wings.
    prism_polygon([[18.5,8.0],[30,8.0],[31,15.0],[19,15.0]],17.65,17.90,'SignalBridge_Deck','deck_edge','island')
    box([6.0,1.8,.18],[40.0,7.9,16.35],'BridgeWing_Port','deck_edge',group='island')
    box([6.0,1.8,.18],[40.0,15.2,16.35],'BridgeWing_Starboard','deck_edge',group='island')
    # Window bands: forward, port and starboard.
    for j,x in enumerate(np.linspace(29.0,41.0,7)):
        box([1.35,.10,.72],[float(x),8.74,16.72],f'BridgeWindow_Port_{j}','glass',group='island')
    for j,x in enumerate(np.linspace(29.5,40.5,6)):
        box([1.45,.10,.72],[float(x),14.62,16.72],f'BridgeWindow_Stbd_{j}','glass',group='island')
    for j,y in enumerate(np.linspace(9.8,13.8,5)):
        box([.10,.78,.72],[43.45,float(y),16.72],f'BridgeWindow_Forward_{j}','glass',group='island')
    # Funnel: rectangular tapered stack is closer to period photos than a round cylinder.
    frustum_rect((22.8,12.25,18.1),(5.2,4.7),(4.2,3.9),5.25,'Funnel_Main','hazegray','island')
    frustum_rect((22.8,12.25,20.82),(4.35,4.05),(4.10,3.8),.55,'Funnel_Cap','black','island')
    # uptake cap inner black opening
    box([3.25,2.9,.08],[22.8,12.25,21.10],'Funnel_Opening','black',group='island')
    # Mast: tripod, platform, yards, stays.
    mast_top=(35.8,11.65,26.8)
    for j,p in enumerate(((35.8,11.65,17.9),(33.9,10.2,17.8),(33.9,13.15,17.8))): beam_between(p,mast_top,.095,f'MastLeg_{j}','steel',10,'island')
    cyl(.15,7.5,[35.8,11.65,24.2],'MastUpper','steel',12,group='island')
    box([8.4,.10,.10],[35.8,11.65,22.7],'MastLowerYard','steel',group='island')
    box([10.5,.09,.09],[35.8,11.65,25.0],'MastUpperYard','steel',group='island')
    # CXAM-1 rectangular mattress approximation from photo evidence.
    box([5.6,.10,1.55],[35.8,11.58,27.55],'CXAM1_MainFrame','steel',group='island')
    for z in np.linspace(26.95,28.15,5): box([5.35,.035,.035],[35.8,11.50,float(z)],f'CXAM1_H_{z:.2f}','steel',group='island')
    for x in np.linspace(33.3,38.3,9): box([.035,.035,1.4],[float(x),11.50,27.55],f'CXAM1_V_{x:.2f}','steel',group='island')
    # YE homing beacon cue above/near mast.
    cyl(.42,.12,[35.8,11.65,28.65],'YE_HomingBeacon','darksteel',20,group='island')
    # Aircraft crane aft of island: post, boom, cable/hook.
    cyl(.15,4.7,[15.6,14.0,14.8],'AircraftCrane_Post','steel',12,group='island')
    beam_between((15.6,14.0,17.0),(23.2,14.0,19.8),.13,'AircraftCrane_Boom','steel',10,'island')
    beam_between((23.2,14.0,19.8),(23.2,14.0,12.1),.035,'AircraftCrane_Cable','darksteel',6,'island')
    sphere(.16,(23.2,14.0,12.0),'AircraftCrane_Hook','darksteel',1,'island')
    # Searchlights and loudspeakers prominent in period island photos.
    for j,(x,y,z) in enumerate(((18.6,9.5,18.4),(20.0,9.5,18.4),(32.0,8.4,18.6),(39.0,8.5,18.7))):
        cyl(.58,.52,[x,y,z],f'Searchlight_{j}','steel',16,axis='y',group='island')
        cyl(.42,.54,[x,y-.32,z],f'SearchlightLens_{j}','glass',16,axis='y',group='island')
    for j,(x,y,z) in enumerate(((19.0,14.8,17.0),(21.0,14.8,17.0),(31.0,14.9,18.0),(40.0,14.6,18.1))):
        # horn speaker: short frustum-like box/cylinder cue
        cyl(.23,.55,[x,y,z],f'Loudspeaker_{j}','darksteel',12,axis='y',group='island')
    # Mk.33 director aft-island position from March 1942 photo.
    cyl(1.12,.55,[17.6,12.0,18.35],'Mk33_Director_Base','hazegray',18,group='island')
    frustum_rect((17.6,12.0,19.15),(2.0,1.55),(1.7,1.35),1.1,'Mk33_Director_House','hazegray_light','island')
    for side in (-1,1): cyl(.22,1.7,[17.6,12.0+side*1.35,19.25],f'Mk33_Rangefinder_{side}','steel',12,axis='y',group='island')
    # external ladders and railings around island.
    for j,z in enumerate(np.arange(11.5,17.4,.45)): box([.55,.04,.04],[25.0,8.35,float(z)],f'IslandLadderRung_{j:02d}','steel',group='island')
    beam_between((24.72,8.35,11.3),(24.72,8.35,17.6),.03,'IslandLadderRailA','steel',6,'island')
    beam_between((25.28,8.35,11.3),(25.28,8.35,17.6),.03,'IslandLadderRailB','steel',6,'island')
    # wire stays/antenna leads.
    for j,(a,b) in enumerate((((35.8,11.65,26.7),(25.0,8.8,17.9)),((35.8,11.65,26.7),(43.0,14.0,17.8)),((35.8,11.65,25.0),(22.0,11.0,17.8)))):
        beam_between(a,b,.015,f'MastStay_{j}','darksteel',5,'island')


def gun_5in(x,y,heading,name):
    cyl(.62,.45,[x,y,10.4],name+'_Base','steel',16,group='weapons')
    cyl(.46,.65,[x,y,10.95],name+'_Pedestal','hazegray',16,group='weapons')
    # shield / breech / barrel
    box([1.15,1.0,.8],[x,y,11.45],name+'_Breech','hazegray',angle_deg=heading,group='weapons')
    ang=math.radians(heading); dx,dy=math.cos(ang),math.sin(ang)
    beam_between((x+dx*.35,y+dy*.35,11.55),(x+dx*3.1,y+dy*3.1,11.75),.075,name+'_Barrel','darksteel',10,'weapons')
    for side in (-1,1): beam_between((x-dy*.5*side,y+dx*.5*side,11.05),(x-dy*.5*side,y+dx*.5*side,11.75),.025,name+f'_ShieldRail{side}','steel',6,'weapons')


def gun_quad_11(x,y,heading,name):
    cyl(.62,.42,[x,y,10.85],name+'_Base','steel',16,group='weapons')
    box([1.5,1.2,.58],[x,y,11.35],name+'_Mount','hazegray',angle_deg=heading,group='weapons')
    ang=math.radians(heading); dx,dy=math.cos(ang),math.sin(ang)
    for i,off in enumerate((-0.27,-0.09,.09,.27)):
        a=(x-dy*off,y+dx*off,11.65); b=(x+dx*2.05-dy*off,y+dy*2.05+dx*off,11.78)
        beam_between(a,b,.035,name+f'_Barrel{i}','darksteel',7,'weapons')


def gun_20mm(x,y,heading,name):
    cyl(.15,.38,[x,y,10.82],name+'_Pedestal','steel',10,group='weapons')
    ang=math.radians(heading); dx,dy=math.cos(ang),math.sin(ang)
    # small circular shoulder rest + shield plate + barrel
    cyl(.17,.05,[x,y,11.18],name+'_SightRing','darksteel',12,axis='x',group='weapons')
    box([.06,.72,.55],[x+dx*.12,y+dy*.12,11.25],name+'_Shield','hazegray',angle_deg=heading,group='weapons')
    beam_between((x+dx*.12,y+dy*.12,11.28),(x+dx*1.18,y+dy*1.18,11.40),.028,name+'_Barrel','darksteel',6,'weapons')


def build_weapons():
    five=[(-89,-14.6,-90),(-58,-14.8,-90),(65,-14.8,-90),(92,-14.2,-90),(-89,14.6,90),(-58,14.8,90),(65,14.8,90),(92,14.2,90)]
    for i,p in enumerate(five,1): gun_5in(*p,f'5in38_{i}')
    quads=[(25,7.3,180),(38.5,7.3,180),(-55,14.3,90),(76,14.3,90)]
    for i,p in enumerate(quads,1): gun_quad_11(*p,f'1p1_quad_{i}')
    pos=[]
    for x in np.linspace(-104,104,12): pos.append((float(x),-15.25,-90))
    for x in np.linspace(-104,104,12): pos.append((float(x),15.25,90))
    pos += [(22,8.0,180),(27,8.0,180),(32,8.0,180),(37,8.0,180),(25,14.9,90),(43,14.9,90)]
    for i,p in enumerate(pos[:30],1): gun_20mm(*p,f'Oerlikon20_{i:02d}')


def build_boats_rafts_fittings():
    # Stacked life rafts / boats along gallery edges.
    for side in (-1,1):
        for j,x in enumerate(np.linspace(-78,80,12)):
            for k in range(2): box([2.45,.56,.38],[float(x),side*(13.1+k*.4),8.2+k*.4],f'LifeRaft_{side}_{j:02d}_{k}','wood',group='fittings')
    for i,(x,y) in enumerate(((6,13.2),(13,13.2),(47,13.25),(54,13.25))):
        # capsule as boat hull, plus small cabin rim
        m=trimesh.creation.capsule(height=5.2,radius=.62,count=[10,10]); m.apply_transform(rotation_matrix(math.pi/2,[0,1,0])); m.apply_translation([x,y,8.75]); add(m,f'ShipsBoat_{i+1}','hazegray','fittings')
        box([1.7,.85,.38],[x,y,9.32],f'ShipsBoat_Cabin_{i+1}','hazegray_light',group='fittings')
    # Bollards, chocks, deck vents and hose reels.
    for j,x in enumerate((-108,-92,-70,-45,-20,8,57,88,108)):
        for side in (-1,1):
            cyl(.14,.55,[x,side*13.6,10.95],f'DeckBollard_{j}_{side}','darksteel',10,group='fittings')
            cyl(.28,.18,[x+1.1,side*13.3,10.96],f'DeckVent_{j}_{side}','hazegray',12,group='fittings')
    # deck edge piping and fire-main cues.
    for side in (-1,1): beam_between((-96,side*13.4,9.2),(96,side*13.4,9.2),.055,f'FireMain_{side}','red',8,'fittings')
    # anchor chain approximation on forward deck edge.
    for side in (-1,1):
        for j,x in enumerate(np.linspace(102,115,14)):
            cyl(.13,.10,[float(x),side*7.5,10.98],f'AnchorChain_{side}_{j:02d}','darksteel',8,axis='x',group='fittings')



def build_surface_microdetails():
    """High-detail exterior pass for the UE asset. Positions remain reconstruction unless listed in manifest."""
    # Tie-down eyes / deck fittings: sparse enough for runtime grouping, dense enough to read at human scale.
    for ix,x in enumerate(np.arange(-108,109,9.0)):
        for iy,y in enumerate((-9.0,-4.5,4.5,9.0)):
            cyl(.055,.025,[float(x),float(y),FLIGHT_Z+.385],f'TieDown_{ix:02d}_{iy}','darksteel',8,group='deck_detail')
    # Arresting gear machinery covers and barrier stanchions.
    for j,x in enumerate(np.linspace(69,101,6)):
        for side in (-1,1):
            box([.85,.52,.26],[float(x),side*13.15,FLIGHT_Z+.48],f'ArrestGearHousing_{j}_{side}','hazegray_dark',group='deck_detail')
    for j,x in enumerate((43.5,52.0)):
        for side in (-1,1): cyl(.09,1.35,[x,side*12.8,FLIGHT_Z+.92],f'BarrierStanchion_{j}_{side}','steel',10,group='deck_detail')
    # Catwalk safety-net diagonal cues.
    for side in (-1,1):
        for j,x in enumerate(np.arange(-96,97,9.0)):
            beam_between((x,side*15.95,10.15),(x+4.0,side*15.95,10.78),.012,f'SafetyNetDiagA_{side}_{j:02d}','steel',5,'deck_detail')
            beam_between((x+4.0,side*15.95,10.15),(x,side*15.95,10.78),.012,f'SafetyNetDiagB_{side}_{j:02d}','steel',5,'deck_detail')
    # Deck-edge hose reels, fire lockers, deck winches/capstans.
    for side in (-1,1):
        for j,x in enumerate((-84,-62,-28,8,58,86)):
            tor=trimesh.creation.torus(major_radius=.30,minor_radius=.045,major_sections=18,minor_sections=6)
            tor.apply_transform(rotation_matrix(math.pi/2,[1,0,0])); tor.apply_translation([x,side*14.4,10.55]); add(tor,f'HoseReel_{side}_{j}','red','deck_detail')
            box([.68,.42,.85],[x+1.0,side*14.1,10.55],f'FireLocker_{side}_{j}','hazegray',group='deck_detail')
        for j,x in enumerate((-104,-75,74,104)):
            cyl(.34,.42,[x,side*11.7,10.97],f'DeckCapstan_{side}_{j}','darksteel',16,group='deck_detail')
    # Mid-body hull plating seams and scupper/opening cues.
    for side in (-1,1):
        for j,z in enumerate((-4.6,-2.7,-.6,1.55,3.65,5.25)):
            beam_between((-88,side*12.72,z),(88,side*12.72,z),.018,f'HullLongSeam_{side}_{j}','hazegray_dark',5,'hull_detail')
        for j,x in enumerate(np.arange(-84,85,8.0)):
            box([.035,.045,5.0],[float(x),side*12.73,2.2],f'HullFrameSeam_{side}_{j:02d}','hazegray_dark',group='hull_detail')
        for j,x in enumerate(np.arange(-76,77,12.0)):
            box([.65,.055,.22],[float(x),side*12.78,4.75],f'GalleryScupper_{side}_{j:02d}','black',group='hull_detail')
    # Boot-topping / antifouling visual cue (material boundary is reconstruction, not claimed exact 1942 color).
    for side in (-1,1):
        box([178,.16,.42],[0,side*12.35,-.15],f'BootTop_{side}','black',group='hull_detail')
        box([170,.12,2.9],[-1,side*11.7,-2.15],f'AntifoulingSide_{side}','underwater',group='hull_detail')
    # Island doors, access hatches, portholes, platform railings and signal halyards.
    doors=[(27.0,8.55,12.0),(36.0,8.55,12.0),(25.2,14.62,14.2),(39.3,14.55,14.2)]
    for j,(x,y,z) in enumerate(doors):
        box([.82,.06,1.72],[x,y,z],f'IslandDoor_{j}','hazegray_dark',group='island_detail')
        cyl(.045,.05,[x+.27,y-.045,z],f'IslandDoorHandle_{j}','brass',8,axis='y',group='island_detail')
    for j,(x,y,z) in enumerate(((20.4,8.5,12.4),(22.4,8.5,12.4),(24.4,8.5,12.4),(31.0,14.7,14.4),(33.0,14.7,14.4))):
        cyl(.13,.04,[x,y,z],f'IslandPorthole_{j}','glass',14,axis='y',group='island_detail')
    # bridge-wing railings
    for side_y,name in ((7.0,'Port'),(16.1,'Starboard')):
        for j,x in enumerate(np.linspace(37.2,42.8,6)): cyl(.02,.72,[float(x),side_y,16.72],f'BridgeWingPost_{name}_{j}','steel',6,group='island_detail')
        beam_between((37.0,side_y,17.08),(43.0,side_y,17.08),.025,f'BridgeWingRail_{name}','steel',6,'island_detail')
    for j,x in enumerate((32.5,34.0,35.5,37.0,38.5,40.0)):
        beam_between((x,11.65,24.9),(x-13.0,7.8,17.9),.009,f'SignalHalyard_{j}','darksteel',5,'island_detail')
    # Gallery access ladders and deck-edge ready lockers.
    for side in (-1,1):
        for k,x in enumerate((-72,-36,4,52,88)):
            for j,z in enumerate(np.arange(8.4,10.2,.32)): box([.52,.035,.025],[x,side*14.25,float(z)],f'GalleryLadderRung_{side}_{k}_{j}','steel',group='deck_detail')
            beam_between((x-.27,side*14.25,8.2),(x-.27,side*14.25,10.35),.022,f'GalleryLadderRailA_{side}_{k}','steel',6,'deck_detail')
            beam_between((x+.27,side*14.25,8.2),(x+.27,side*14.25,10.35),.022,f'GalleryLadderRailB_{side}_{k}','steel',6,'deck_detail')
            box([.72,.55,.82],[x+1.15,side*13.85,9.7],f'ReadyLocker_{side}_{k}','hazegray',group='deck_detail')

def aircraft_mesh(kind, center, heading=0, idx=1, folded=False):
    x,y,z=center; scale={'F4F':1.0,'SBD':1.08,'TBD':1.14}[kind]; matname={'F4F':'hazegray','SBD':'hazegray_dark','TBD':'hazegray_light'}[kind]
    # fuselage from tapered cone + radial-engine cylinder.
    body=conical_frustum_mesh(radius_top=.20*scale,radius_base=.42*scale,height=5.6*scale,sections=14)
    body.apply_transform(rotation_matrix(math.pi/2,[0,1,0])); body.apply_translation([x,y,z+.72]); add(body,f'{kind}_{idx}_Fuselage',matname,'aircraft')
    cyl(.42*scale,.35,[x+2.85*scale,y,z+.72],f'{kind}_{idx}_Engine','darksteel',16,axis='x',group='aircraft')
    # polygon wings with taper and rounded-ish tips.
    span={'F4F':11.6,'SBD':12.7,'TBD':15.0}[kind]*scale; chord={'F4F':2.0,'SBD':2.25,'TBD':2.2}[kind]*scale
    if folded and kind in ('F4F','TBD'):
        # inner wing + raised folded panels as visual cue.
        box([1.35*scale,5.6*scale,.12],[x+.25*scale,y,z+.76],f'{kind}_{idx}_WingInner',matname,angle_deg=heading,group='aircraft')
        for side in (-1,1):
            panel=trimesh.creation.box(extents=[1.0*scale,(span-5.6*scale)/2,.10])
            panel.apply_transform(rotation_matrix(math.radians(70*side),[1,0,0])); panel.apply_translation([x+.2*scale,y+side*(4.0*scale),z+2.1*scale]); add(panel,f'{kind}_{idx}_WingFold_{side}',matname,'aircraft')
    else:
        box([chord,span,.12],[x+.25*scale,y,z+.76],f'{kind}_{idx}_Wing',matname,angle_deg=heading,group='aircraft')
    box([1.1*scale,4.5*scale,.10],[x-2.0*scale,y,z+.80],f'{kind}_{idx}_Tailplane',matname,angle_deg=heading,group='aircraft')
    box([1.1*scale,.10,1.25*scale],[x-2.25*scale,y,z+1.25],f'{kind}_{idx}_Fin',matname,angle_deg=heading,group='aircraft')
    # canopy + landing gear + propeller.
    frustum_rect((x+.1*scale,y,z+1.25),(1.3*scale,.78*scale),(.75*scale,.5*scale),.5*scale,f'{kind}_{idx}_Canopy','glass','aircraft')
    for side in (-1,1):
        beam_between((x+.7*scale,y+side*.7*scale,z+.65),(x+.65*scale,y+side*.95*scale,z+.1),.035,f'{kind}_{idx}_Gear_{side}','darksteel',6,'aircraft')
        cyl(.16*scale,.12,[x+.65*scale,y+side*.95*scale,z+.05],f'{kind}_{idx}_Wheel_{side}','rubber',10,axis='y',group='aircraft')
    for a in (0,90):
        prop=trimesh.creation.box(extents=[.05,2.0*scale,.09]); prop.apply_transform(rotation_matrix(math.radians(a),[1,0,0])); prop.apply_translation([x+3.08*scale,y,z+.72]); add(prop,f'{kind}_{idx}_Prop_{a}','black','aircraft')


def build_deck_aircraft():
    spots=[(-96,-5.2,'TBD',True),(-87,4.8,'TBD',True),(-70,-4.0,'SBD',False),(-59,4.7,'SBD',False),(-40,-4.6,'F4F',True),(-29,4.5,'F4F',True),(69,-4.0,'SBD',False),(83,4.4,'F4F',True)]
    for i,(x,y,k,fold) in enumerate(spots,1): aircraft_mesh(k,(x,y,FLIGHT_Z+.38),0,i,fold)


def build_bridge_module(path):
    s=trimesh.Scene(); old_scene,old_stats,old_groups=globals()['scene'],globals()['part_stats'],globals()['part_groups']
    globals()['scene'],globals()['part_stats'],globals()['part_groups']=s,{},{}
    try:
        # 1942 pilot-house reconstruction, sized from exterior; equipment placement is reconstruction.
        box([13.0,6.6,.16],[0,0,0],'Bridge_Floor','darksteel',group='bridge')
        box([13.0,6.6,.12],[0,0,2.65],'Bridge_Ceiling','hazegray',group='bridge')
        for side in (-1,1): box([13.0,.10,2.65],[0,side*3.25,1.35],f'BridgeSide_{side}','hazegray',group='bridge')
        # forward windows across bow-facing wall
        for j,y in enumerate(np.linspace(-2.6,2.6,7)): box([.12,.62,.82],[6.48,float(y),1.75],f'BridgeWindow_{j}','glass',group='bridge')
        # helm and mechanical wheel
        cyl(.16,.75,[2.0,0,1.05],'HelmColumn','brass',12,group='bridge')
        wheel=trimesh.creation.torus(major_radius=.48,minor_radius=.035,major_sections=24,minor_sections=8); wheel.apply_transform(rotation_matrix(math.pi/2,[0,1,0])); wheel.apply_translation([2.35,0,1.35]); add(wheel,'HelmWheel','brass','bridge')
        for a in np.linspace(0,2*math.pi,8,endpoint=False): beam_between((2.35,0,1.35),(2.35,.42*math.cos(a),1.35+.42*math.sin(a)),.018,f'HelmSpoke_{a:.2f}','brass',6,'bridge')
        # engine order telegraphs, gyro repeaters, chart table, voice tubes, annunciator panels.
        for side in (-1,1):
            cyl(.24,1.0,[1.1,side*1.7,.75],f'EOT_{side}','brass',14,group='bridge')
            sphere(.28,[1.1,side*1.7,1.32],f'EOT_Dial_{side}','glass',2,'bridge')
        box([2.4,1.3,.9],[-1.4,-1.4,.55],'ChartTable','wood',group='bridge')
        box([2.0,.18,.95],[-2.8,2.7,1.2],'AnnunciatorPanel','darksteel',group='bridge')
        cyl(.18,1.4,[-3.9,2.7,1.25],'VoiceTube','brass',10,group='bridge')
        for j,x in enumerate((-5.0,-3.0,-1.0,1.0,3.0,5.0)): cyl(.11,.5,[x,0,2.40],f'BridgeLight_{j}','warm_light',10,group='bridge')
        # Magnetic compass/binnacle, gyro repeaters, pelorus stands, chairs and bridge talkers.
        cyl(.32,.85,[3.55,0,.60],'CompassBinnacle','brass',18,group='bridge'); sphere(.23,[3.55,0,1.08],'CompassGlass','glass',2,'bridge')
        for side in (-1,1):
            cyl(.18,.95,[4.35,side*2.25,.65],f'PelorusStand_{side}','steel',12,group='bridge')
            cyl(.30,.12,[4.35,side*2.25,1.18],f'PelorusHead_{side}','brass',18,group='bridge')
            box([.55,.55,.08],[-.2,side*2.35,.62],f'BridgeChairSeat_{side}','wood',group='bridge')
            box([.08,.55,.72],[-.45,side*2.35,.93],f'BridgeChairBack_{side}','wood',group='bridge')
        # Mechanical dial bank and clock/engine indicators on aft bulkhead.
        for j,y in enumerate(np.linspace(-2.2,2.2,6)):
            cyl(.18,.04,[-6.43,float(y),1.55],f'BridgeDial_{j}','glass',14,axis='x',group='bridge')
        box([.10,1.0,1.85],[-6.44,-2.75,1.15],'BridgeWatertightDoor','hazegray_dark',group='bridge')
        path.write_bytes(trimesh.exchange.gltf.export_glb(s))
    finally:
        globals()['scene'],globals()['part_stats'],globals()['part_groups']=old_scene,old_stats,old_groups


def build_cic_module(path):
    s=trimesh.Scene(); old_scene,old_stats,old_groups=globals()['scene'],globals()['part_stats'],globals()['part_groups']; globals()['scene'],globals()['part_stats'],globals()['part_groups']=s,{},{}
    try:
        box([13.5,8.0,.18],[0,0,0],'CIC_Floor','darksteel',group='cic'); box([13.5,8,.12],[0,0,2.6],'CIC_Ceiling','hazegray_dark',group='cic')
        for side in (-1,1): box([13.5,.12,2.6],[0,side*3.95,1.3],f'CIC_Wall_{side}','hazegray_dark',group='cic')
        # Early-war radar/fighter-direction room reconstruction: plotting tables, scopes, phones, status boards.
        box([4.0,2.2,.82],[0,0,.48],'CIC_PlotTable','wood',group='cic')
        for j,(x,y) in enumerate(((-4.8,-2.5),(-4.8,0),(-4.8,2.5),(4.8,-2.5),(4.8,0),(4.8,2.5))):
            box([1.2,.8,1.45],[x,y,.78],f'CIC_Console_{j}','darksteel',group='cic')
            sphere(.28,[x-.58 if x>0 else x+.58,y,1.35],f'CIC_Scope_{j}','glass',2,'cic')
        box([.12,5.5,1.6],[6.6,0,1.2],'CIC_StatusBoard','black',group='cic')
        for j,x in enumerate(np.linspace(-5,5,5)): cyl(.1,.4,[float(x),0,2.38],f'CIC_RedLight_{j}','battle_red',10,group='cic')
        # Battle-phone racks, plotting tools, stools and overhead cable trays.
        for side in (-1,1):
            box([3.8,.20,1.15],[0,side*3.75,1.05],f'CIC_PhoneRack_{side}','hazegray',group='cic')
            for j,x in enumerate(np.linspace(-1.4,1.4,5)):
                cyl(.10,.08,[float(x),side*3.62,1.30],f'CIC_Handset_{side}_{j}','black',10,axis='y',group='cic')
        for j,x in enumerate((-1.4,0,1.4)):
            cyl(.22,.62,[x,1.45,.35],f'CIC_Stool_{j}','steel',12,group='cic'); cyl(.35,.08,[x,1.45,.69],f'CIC_StoolSeat_{j}','wood',12,group='cic')
        for y in (-2.8,2.8): box([12.5,.24,.18],[0,y,2.38],f'CIC_CableTray_{y}','darksteel',group='cic')
        box([.10,1.0,1.85],[-6.66,3.1,1.05],'CIC_WatertightDoor','hazegray',group='cic')
        path.write_bytes(trimesh.exchange.gltf.export_glb(s))
    finally: globals()['scene'],globals()['part_stats'],globals()['part_groups']=old_scene,old_stats,old_groups


def build_engineering_module(path):
    s=trimesh.Scene(); old_scene,old_stats,old_groups=globals()['scene'],globals()['part_stats'],globals()['part_groups']; globals()['scene'],globals()['part_stats'],globals()['part_groups']=s,{},{}
    try:
        box([28,14,.2],[0,0,0],'Machinery_Floor','darksteel',group='engineering'); box([28,14,.12],[0,0,5.8],'Machinery_Overhead','hazegray_dark',group='engineering')
        # representative Yorktown-class machinery-room reconstruction: boilers/turbines/generators, catwalks, pipes, valves.
        for j,x in enumerate((-9,-3,3,9)):
            cyl(1.65,4.4,[x,-3.2,2.35],f'Boiler_{j}','hazegray',24,axis='x',group='engineering')
            cyl(.55,5.5,[x,2.0,1.1],f'Turbine_{j}','steel',20,axis='x',group='engineering')
        for j,x in enumerate((-7,0,7)): cyl(.9,2.0,[x,5.1,1.1],f'Generator_{j}','hazegray_light',18,axis='x',group='engineering')
        for side in (-1,1):
            box([27,.9,.15],[0,side*5.9,3.1],f'Catwalk_{side}','deck_edge',group='engineering')
            for j,x in enumerate(np.arange(-12,13,3)): cyl(.025,.85,[float(x),side*6.25,3.48],f'CatwalkPost_{side}_{j}','steel',8,group='engineering')
            beam_between((-13,side*6.25,3.9),(13,side*6.25,3.9),.035,f'CatwalkRail_{side}','steel',6,'engineering')
        colors=('red','green','steel')
        for i,y in enumerate((-5,-3.8,3.6,4.8)):
            beam_between((-13,y,4.7),(13,y,4.7),.10,f'MainPipe_{i}',colors[i%3],10,'engineering')
            for j,x in enumerate((-10,-5,0,5,10)):
                tor=trimesh.creation.torus(major_radius=.24,minor_radius=.035,major_sections=18,minor_sections=6); tor.apply_transform(rotation_matrix(math.pi/2,[0,1,0])); tor.apply_translation([x,y,4.7]); add(tor,f'ValveWheel_{i}_{j}','red','engineering')
        for j,x in enumerate(np.arange(-12,13,4)): cyl(.12,.6,[float(x),0,5.4],f'EngLight_{j}','warm_light',10,group='engineering')
        # Gauge/manifold boards, ladders, floor gratings and auxiliary pumps.
        for j,x in enumerate((-10,-5,0,5,10)):
            box([1.15,.18,1.55],[x,-6.75,1.45],f'GaugeBoard_{j}','hazegray',group='engineering')
            for k,z in enumerate((1.1,1.55,2.0)): cyl(.13,.035,[x,-6.64,z],f'PressureGauge_{j}_{k}','glass',12,axis='y',group='engineering')
            cyl(.42,.8,[x,0,.55],f'AuxPump_{j}','hazegray_dark',16,axis='x',group='engineering')
        for side in (-1,1):
            for j,z in enumerate(np.arange(.5,3.5,.35)): box([.60,.035,.025],[12.8,side*5.8,float(z)],f'EngLadderRung_{side}_{j}','steel',group='engineering')
            beam_between((12.5,side*5.8,.35),(12.5,side*5.8,3.6),.025,f'EngLadderRailA_{side}','steel',6,'engineering')
            beam_between((13.1,side*5.8,.35),(13.1,side*5.8,3.6),.025,f'EngLadderRailB_{side}','steel',6,'engineering')
        for j,x in enumerate(np.arange(-11,12,2.75)): box([1.9,2.0,.04],[float(x),0,.16],f'EngFloorGrating_{j}','steel',group='engineering')
        box([.10,1.15,2.0],[-13.92,5.9,1.1],'EngineeringWatertightDoor','hazegray',group='engineering')
        path.write_bytes(trimesh.exchange.gltf.export_glb(s))
    finally: globals()['scene'],globals()['part_stats'],globals()['part_groups']=old_scene,old_stats,old_groups


def build_hangar_module(path):
    # Full interior-only module to allow Unreal streaming/occlusion independent of the exterior.
    s=trimesh.Scene(); old_scene,old_stats,old_groups=globals()['scene'],globals()['part_stats'],globals()['part_groups']; globals()['scene'],globals()['part_stats'],globals()['part_groups']=s,{},{}
    try:
        box([166,18.7,.18],[0,0,0],'HangarModule_Floor','darksteel',group='hangar_module'); box([166,18.7,.16],[0,0,4.1],'HangarModule_Ceiling','hazegray_dark',group='hangar_module')
        for j,x in enumerate(np.arange(-80,81,6.5)):
            box([.18,18.0,.20],[float(x),0,3.82],f'HangarModule_Beam_{j}','steel',group='hangar_module')
            for side in (-1,1): box([.20,.38,4.0],[float(x),side*9.0,2.0],f'HangarModule_Frame_{j}_{side}','steel',group='hangar_module')
        for side in (-1,1): beam_between((-80,side*6.9,3.45),(80,side*6.9,3.45),.30,f'HangarModule_Vent_{side}','hazegray_light',12,'hangar_module')
        for j,x in enumerate(np.arange(-76,77,8)): 
            for y in (-4.8,0,4.8): cyl(.10,.45,[float(x),y,3.55],f'HangarModule_Light_{j}_{y}','warm_light',10,group='hangar_module')
        # Elevator trunks/rails, aviation fire stations, shop benches, tow tractors and fire-curtain tracks.
        for e,x in enumerate((-63,0,67),1):
            for side in (-1,1): box([11.7,.10,3.8],[x,side*4.55,1.95],f'HangarElevatorRail_{e}_{side}','steel',group='hangar_module')
            for end in (-1,1): box([.10,9.0,3.8],[x+end*5.85,0,1.95],f'HangarElevatorEndRail_{e}_{end}','steel',group='hangar_module')
        for j,x in enumerate((-70,-46,-22,22,46,70)):
            box([1.05,.45,1.35],[x,-8.55,.78],f'HangarFireStation_{j}','red',group='hangar_module')
            box([4.0,.85,.90],[x,7.7,.52],f'HangarWorkbench_{j}','wood',group='hangar_module')
        for j,x in enumerate((-52,18,56)):
            box([1.9,1.1,.62],[x,-2.7,.42],f'HangarTowTractor_{j}','hazegray_dark',group='hangar_module')
            for side in (-1,1): cyl(.28,.16,[x, -2.7+side*.55,.18],f'HangarTowWheel_{j}_{side}','rubber',12,axis='y',group='hangar_module')
        for x in (-41,21): box([.18,18.0,3.8],[x,0,1.95],f'HangarFireCurtainTrack_{x}','steel',group='hangar_module')
        path.write_bytes(trimesh.exchange.gltf.export_glb(s))
    finally: globals()['scene'],globals()['part_stats'],globals()['part_groups']=old_scene,old_stats,old_groups



def export_selected_runtime(groupset, path):
    """Export a streamable runtime module with material/zone batching while preserving textured UV meshes."""
    selected=[]
    for name,g in scene.geometry.items():
        if g.metadata.get('group','exterior') in groupset:
            selected.append((name,g))
    out=trimesh.Scene(); buckets={}
    for name,g in selected:
        mat=getattr(getattr(g.visual,'material',None),'name','steel') or 'steel'
        zone=g.metadata.get('group','exterior')
        textured=isinstance(g.visual,trimesh.visual.TextureVisuals)
        buckets.setdefault((zone,mat,'tex' if textured else 'plain'),[]).append(g.copy())
    for (zone,mat,kind),items in buckets.items():
        if kind=='tex':
            for n,m in enumerate(items): out.add_geometry(m,node_name=f'CV6_{zone}_{mat}_{n}',geom_name=f'CV6_{zone}_{mat}_{n}')
        else:
            mg=trimesh.util.concatenate(items); mg.visual.material=MATS.get(mat,MATS['steel'])
            out.add_geometry(mg,node_name=f'CV6_{zone}_{mat}',geom_name=f'CV6_{zone}_{mat}')
    path.write_bytes(trimesh.exchange.gltf.export_glb(out))
    return {'source_parts':len(selected),'runtime_meshes':len(out.geometry),'bytes':path.stat().st_size}

def export_grouped_runtime():
    # Runtime asset groups by material + logical zone, keeping texture-backed meshes intact.
    grouped=trimesh.Scene(); groups={}
    for name,g in scene.geometry.items():
        mat=getattr(getattr(g.visual,'material',None),'name','steel') or 'steel'; zone=g.metadata.get('group','exterior')
        textured=isinstance(g.visual,trimesh.visual.TextureVisuals)
        key=(zone,mat,'tex' if textured else 'plain')
        groups.setdefault(key,[]).append(g.copy())
    for (zone,mat,kind),items in groups.items():
        if kind=='tex':
            # Avoid concatenating unrelated UV islands; currently one textured mesh per key.
            for n,m in enumerate(items): grouped.add_geometry(m,node_name=f'CV6_{zone}_{mat}_{n}',geom_name=f'CV6_{zone}_{mat}_{n}')
        else:
            mg=trimesh.util.concatenate(items)
            mg.visual.material=MATS.get(mat,MATS['steel'])
            grouped.add_geometry(mg,node_name=f'CV6_{zone}_{mat}',geom_name=f'CV6_{zone}_{mat}')
    return grouped, groups


def write_preview_manifest(groups):
    bounds=scene.bounds
    stats={
      'version':'2.7.0',
      'visual_target':'USS Enterprise (CV-6), Battle of Midway configuration, late May / early June 1942',
      'coordinate_system':'meters; X longitudinal (+ bow), Y starboard, Z up',
      'source_driven_dimensions_m':{'overall_length':L_OVERALL,'flight_deck_length':L_DECK,'flight_deck_width':W_DECK,'waterline_beam':W_WATERLINE,'draft':DRAFT},
      'photo_constrained_features':['March 1942 island face/window massing','aft aircraft crane','Mk.33 director cue','1.1-inch AA positions near island','CXAM-1 radar mattress','searchlights/loudspeakers','open hangar side framing','March 1942 20mm fit count'],
      'class_plan_constrained_features':['long open hangar envelope','three elevators','Yorktown-class overall deck proportions','major deck level relationships'],
      'reconstruction_only':['exact hull frame offsets','exact island compartment geometry','exact AA gun coordinates','exact gallery/rail dimensions','interior machinery equipment placement','interior bridge/CIC console placement','surface RGB/roughness values','deck aircraft parking','hull plate seam spacing','boot topping / antifouling boundary','deck fitting coordinates','door/porthole coordinates'],
      'modeled_period_details':['251.4m lofted hull','textured 244.6m flight deck','open-sided framed hangar','three elevators','faceted island/pilot house','tapered rectangular funnel','tripod mast with CXAM-style radar','Mk.33 director','aircraft crane','searchlights/loudspeakers','8 5in/38 singles','4 quad 1.1in mounts','30 20mm positions','gallery/catwalk/LSO platform','boats/life rafts','anchors/chains/shafts/rudder','representative folded-wing aircraft','deck tie-down eyes and arresting-gear housings','catwalk safety-net lattice','hull plate/scupper cues','island access doors/portholes','deck-edge hose reels/capstans/lockers'],
      'geometry':{'editable_objects':len(scene.geometry),'runtime_groups':len(groups),'vertices':int(sum(len(g.vertices) for g in scene.geometry.values())),'triangles':int(sum(len(g.faces) for g in scene.geometry.values())),'bounds_m':bounds.tolist()},
      'parts':part_stats,
      'logical_groups':{k:v for k,v in part_groups.items()},
      'exterior_modules':['CV6_HullDeck_Hangar.glb','CV6_Island.glb','CV6_Weapons_Fittings.glb','CV6_DeckAircraft.glb'],
      'interior_modules':['Enterprise_CV6_1942_Hangar_Interior.glb','Enterprise_CV6_1942_Bridge_Interior.glb','Enterprise_CV6_1942_CIC_Interior.glb','Enterprise_CV6_1942_Engineering_Interior.glb'],
      'historical_boundary':'Where a detail is directly visible in March-June 1942 imagery or supported by Yorktown-class plans, the manifest calls it source/photo/class-plan constrained. Precise shapes and hidden interior arrangements remain reconstruction until traced from archival Enterprise-specific drawings.'
    }
    (OUT/'Enterprise_CV6_1942_Midway_manifest.json').write_text(json.dumps(stats,indent=2),encoding='utf-8')
    return stats


def main():
    deck_img,hull_img=make_textures()
    build_hull(hull_img); build_flight_deck(deck_img); build_hangar(); build_galleries_sponsons(); build_island(); build_weapons(); build_boats_rafts_fittings(); build_surface_microdetails(); build_deck_aircraft()
    editable=trimesh.exchange.gltf.export_glb(scene); (OUT/'Enterprise_CV6_1942_Midway_EDITABLE.glb').write_bytes(editable)
    runtime,groups=export_grouped_runtime(); (OUT/'Enterprise_CV6_1942_Midway.glb').write_bytes(trimesh.exchange.gltf.export_glb(runtime))
    module_stats={}
    module_stats['hull_deck_hangar']=export_selected_runtime({'hull','hull_detail','deck','deck_detail','hangar'}, MOD/'CV6_HullDeck_Hangar.glb')
    module_stats['island']=export_selected_runtime({'island','island_detail'}, MOD/'CV6_Island.glb')
    module_stats['weapons_fittings']=export_selected_runtime({'weapons','fittings'}, MOD/'CV6_Weapons_Fittings.glb')
    module_stats['deck_aircraft']=export_selected_runtime({'aircraft'}, MOD/'CV6_DeckAircraft.glb')
    merged=trimesh.util.concatenate([g for g in scene.geometry.values()]); (OUT/'Enterprise_CV6_1942_Midway.obj').write_text(trimesh.exchange.obj.export_obj(merged,include_normals=True,include_texture=False),encoding='utf-8')
    build_hangar_module(INT/'Enterprise_CV6_1942_Hangar_Interior.glb')
    build_bridge_module(INT/'Enterprise_CV6_1942_Bridge_Interior.glb')
    build_cic_module(INT/'Enterprise_CV6_1942_CIC_Interior.glb')
    build_engineering_module(INT/'Enterprise_CV6_1942_Engineering_Interior.glb')
    stats=write_preview_manifest(groups)
    print(json.dumps(stats['geometry'],indent=2))

if __name__=='__main__': main()
