import os
import unreal

project_dir = unreal.Paths.project_dir()
root = os.path.abspath(os.path.join(project_dir, '..', '..'))
assets = [
    # Monolithic compatibility mesh retained, but v2.7 also imports streamable exterior modules.
    (os.path.join(root, 'assets3d', 'Enterprise_CV6_1942_Midway.glb'), '/Game/Enterprise/Compatibility', 'SM_Enterprise_CV6_1942'),
    (os.path.join(root, 'assets3d', 'modules', 'CV6_HullDeck_Hangar.glb'), '/Game/Enterprise/Exterior/HullDeck', 'SM_CV6_HullDeck_Hangar_1942'),
    (os.path.join(root, 'assets3d', 'modules', 'CV6_Island.glb'), '/Game/Enterprise/Exterior/Island', 'SM_CV6_Island_1942'),
    (os.path.join(root, 'assets3d', 'modules', 'CV6_Weapons_Fittings.glb'), '/Game/Enterprise/Exterior/WeaponsFittings', 'SM_CV6_WeaponsFittings_1942'),
    (os.path.join(root, 'assets3d', 'modules', 'CV6_DeckAircraft.glb'), '/Game/Enterprise/Exterior/DeckAircraft', 'SM_CV6_DeckAircraft_1942'),
    (os.path.join(root, 'assets3d', 'interiors', 'Enterprise_CV6_1942_Hangar_Interior.glb'), '/Game/Enterprise/Interiors/Hangar', 'SM_CV6_Hangar_1942'),
    (os.path.join(root, 'assets3d', 'interiors', 'Enterprise_CV6_1942_Bridge_Interior.glb'), '/Game/Enterprise/Interiors/Bridge', 'SM_CV6_Bridge_1942'),
    (os.path.join(root, 'assets3d', 'interiors', 'Enterprise_CV6_1942_CIC_Interior.glb'), '/Game/Enterprise/Interiors/CIC', 'SM_CV6_CIC_1942'),
    (os.path.join(root, 'assets3d', 'interiors', 'Enterprise_CV6_1942_Engineering_Interior.glb'), '/Game/Enterprise/Interiors/Engineering', 'SM_CV6_Engineering_1942'),
]

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
imported = []
for source, dest, name in assets:
    if not os.path.exists(source):
        raise RuntimeError(f'Missing CV-6 source asset: {source}')
    task = unreal.AssetImportTask()
    task.filename = source
    task.destination_path = dest
    task.destination_name = name
    task.automated = True
    task.replace_existing = True
    task.save = True
    asset_tools.import_asset_tasks([task])
    for path in task.imported_object_paths:
        obj = unreal.EditorAssetLibrary.load_asset(path)
        if isinstance(obj, unreal.StaticMesh):
            try:
                obj.set_editor_property('nanite_settings', unreal.MeshNaniteSettings(enabled=True))
            except Exception as exc:
                unreal.log_warning(f'Nanite setting skipped for {path}: {exc}')
            try:
                body = obj.get_editor_property('body_setup')
                if body:
                    # Reconstruction meshes are primarily static architecture. Interior gameplay
                    # collision can later be replaced with authored simple collision hulls per room.
                    body.set_editor_property('collision_trace_flag', unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
            except Exception as exc:
                unreal.log_warning(f'Complex collision setting skipped for {path}: {exc}')
            unreal.EditorAssetLibrary.save_loaded_asset(obj)
        imported.append(path)
        unreal.log(f'CV-6 v2.7 imported: {path}')

unreal.log(
    f'Enterprise CV-6 1942 v2.7 import complete: {len(imported)} Unreal assets. '
    'Hull/deck, island, weapons/fittings, deck aircraft and four interior reconstruction modules '
    'are separated for streaming, occlusion and independent historical refinement.'
)
