"""Fit the original full Sulley mesh to the stock Abrams bind pose.

Source skin weights drive an explicit joint mapping. No nearest-surface transfer
from Abrams's coat, no changes to the stock rig, no global camera offsets.
Run in Blender background mode. Outputs are confined to this experiment.
"""
import json
import re
from pathlib import Path
import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
CONTENT = PROJECT / 'tools/Reduced_CSDK_12/content/citadel_addons/sulley_fullbody/models/heroes_wip/abrams'
SCALE = 0.044


def short(name):
    return re.sub(r'_\d+$', '', name.removeprefix('Bip001_'))


def mappings(names):
    result = {}
    trunk = {'_rootJoint': 'pelvis', 'Pelvis': 'pelvis', 'Spine': 'spine_0',
             'Spine1': 'spine_1', 'Spine2': 'spine_3', 'Neck': 'neck_0',
             'Neck1': 'head', 'Head': 'head'}
    limbs = {'Thigh': 'leg_upper', 'Calf': 'leg_lower', 'Foot': 'ankle',
             'Toe0': 'ball', 'Clavicle': 'clavicle', 'UpperArm': 'arm_upper',
             'Forearm': 'arm_lower', 'Hand': 'hand'}
    for name in names:
        key = short(name)
        target = trunk.get(key)
        if key[:2] in ('L_', 'R_'):
            side, part = key.split('_', 1)
            if part in limbs: target = limbs[part] + '_' + side
            elif part.startswith('Finger'):
                finger = part.removeprefix('Finger')
                digit = {'0': 'thumb', '1': 'index', '2': 'middle', '3': 'pinky'}[finger[0]]
                joint = '1' if len(finger) > 1 else '0'
                target = f'finger_{digit}_{joint}_{side}'
        if key.startswith('bn_Wrist'):
            side = 'L' if '_L' in key else 'R'
            target = f'arm_lower_{side}_TWIST1' if '_Mid_' in key else f'arm_lower_{side}'
        if key.startswith('bn_shoulder'):
            side = 'L' if '_L' in key else 'R'
            target = f'arm_upper_{side}_TWIST1' if key.endswith('_02') else f'arm_upper_{side}'
        if key.startswith('bn_Tail'):
            target = {'bn_Tail_01': 'tail_0', 'bn_Tail_02': 'tail_4',
                      'bn_Tail_03': 'tail_8', 'bn_Tail_04': 'tail_12'}[key]
        # Facial detail retains its source shape in this first body test.
        if target is None:
            if key.startswith(('bn_brow', 'bn_Eye', 'bn_corner', 'bn_jaw', 'bn_lip', 'bn_teeth', 'mouth_master')):
                target = 'head'
            else: raise ValueError(f'Unmapped source bone: {name} / {key}')
        result[name] = target
    return result


def render(path, look, position):
    scene = bpy.context.scene
    bpy.ops.object.camera_add(location=position)
    cam = bpy.context.object
    cam.rotation_euler = (Vector(look) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = 3.65
    scene.camera = cam
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(HERE / 'stock/abrams.gltf'))
for action in bpy.data.actions: action.use_fake_user = True
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
arm.name = 'Abrams_stock_rig'
arm.animation_data_clear()
for p in arm.pose.bones: p.matrix_basis.identity()
bpy.context.view_layer.update()
target_heads = {b.name: arm.matrix_world @ b.head_local for b in arm.data.bones}
stock_meshes = [o for o in bpy.data.objects if o.type == 'MESH' and o.name != 'Icosphere']
for o in stock_meshes:
    o.hide_render = True
    o.hide_set(True)
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(HERE.parent / 'import_head/sully.glb'))
source = next(o for o in bpy.data.objects if o not in before and o.type == 'ARMATURE')
source_meshes = [o for o in bpy.data.objects if o not in before and o.type == 'MESH' and not o.name.startswith('Icosphere')]
bone_map = mappings([b.name for b in source.data.bones])
source_heads = {b.name: source.matrix_world @ source.pose.bones[b.name].head for b in source.data.bones}
by_short = {short(n): n for n in source_heads}
head_source = source_heads[by_short['Head']]

outputs = []
stats = []
for src in sorted(source_meshes, key=lambda o: -len(o.data.vertices)):
    deps = bpy.context.evaluated_depsgraph_get()
    ev = src.evaluated_get(deps)
    mesh = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=deps)
    obj = bpy.data.objects.new('body' if not outputs else 'face', mesh)
    bpy.context.collection.objects.link(obj)
    source_group_names = {g.index: g.name for g in src.vertex_groups}
    weights = []
    for v in mesh.vertices:
        point = ev.matrix_world @ v.co
        groups = [(source_group_names[g.group], g.weight) for g in v.groups if g.weight > 1e-6]
        total = sum(w for _, w in groups)
        if not total: raise ValueError(f'Unweighted source vertex {src.name}:{v.index}')
        dest_weights = {}
        for name, w in groups:
            target = bone_map[name]
            dest_weights[target] = dest_weights.get(target, 0) + w / total
        # Preserve the source silhouette with a monotone vertical fit.
        z_src = [-11.382, -9.02, -4.434, 0, 4.162, 8.707, 13.475, 20.193, 23.301, 25.695, 31.566]
        z_dst = [0.015, 0.223, 0.895, 1.537, 1.682, 1.866, 2.079, 2.35, 2.477, 2.697, 2.955]
        torso = Vector((point.x * SCALE, point.y * SCALE + 0.1,
                        float(np.interp(point.z, z_src, z_dst))))
        position = Vector()
        for name, w in groups:
            key = short(name)
            target = bone_map[name]
            value = torso.copy()
            if target == 'head':
                value = target_heads['head'] + (point - head_source) * SCALE
            elif key.startswith('bn_Tail'):
                # Fit the curve to the stock tail chain so it bends at the
                # actual joints instead of plunging through the ground.
                ys = [5.785, 10.152, 14.923, 22.045, 31.469]
                zs = [2.535, -1.819, -7.42, -8.44, -8.44]
                targets = [target_heads[n] for n in ['tail_0', 'tail_4', 'tail_8', 'tail_12', 'tail_end']]
                center = Vector([float(np.interp(point.y, ys, [p[j] for p in targets])) for j in range(3)])
                value = center + Vector((point.x * .04, 0, (point.z - float(np.interp(point.y, ys, zs))) * .04))
            elif target.startswith(('arm_', 'hand_', 'finger_', 'clavicle_')):
                side = 'L' if ('_L' in target or key.startswith('L_')) else 'R'
                src_joints = [source_heads[by_short[f'{side}_{part}']] for part in ['Hand', 'Forearm', 'UpperArm']]
                dst_joints = [target_heads[f'{part}_{side}'] for part in ['hand', 'arm_lower', 'arm_upper']]
                heights = [p.z for p in src_joints]
                s_anchor = Vector([float(np.interp(point.z, heights, [p[j] for p in src_joints])) for j in range(3)])
                d_anchor = Vector([float(np.interp(point.z, heights, [p[j] for p in dst_joints])) for j in range(3)])
                value = d_anchor + (point - s_anchor) * 0.038
            position += value * (w / total)
        v.co = position
        weights.append(dest_weights)
    # Evaluated meshes retain deform indices. Recreate the source group layout
    # before removing it, so no stale indices contaminate the new skin.
    for g in src.vertex_groups: obj.vertex_groups.new(name=g.name)
    obj.vertex_groups.clear()
    for name in sorted({n for w in weights for n in w}): obj.vertex_groups.new(name=name)
    for i, weights_i in enumerate(weights):
        for name, weight in weights_i.items(): obj.vertex_groups[name].add([i], weight, 'REPLACE')
    obj.parent = arm
    obj.matrix_parent_inverse = arm.matrix_world.inverted()
    mod = obj.modifiers.new('Stock Abrams deformation', 'ARMATURE')
    mod.object = arm
    for polygon in obj.data.polygons: polygon.use_smooth = True
    for mat in obj.data.materials:
        if mat:
            mat.name = 'models/heroes_wip/abrams/materials/sulley_fullbody_' + ('body' if obj.name == 'body' else 'eyes')
            if mat.use_nodes:
                for node in mat.node_tree.nodes:
                    if node.type == 'BSDF_PRINCIPLED': node.inputs['Roughness'].default_value = 0.8
    coords = [v.co for v in mesh.vertices]
    stats.append({'mesh': obj.name, 'vertices': len(coords), 'bones': len(obj.vertex_groups),
                  'min_m': [min(v[i] for v in coords) for i in range(3)],
                  'max_m': [max(v[i] for v in coords) for i in range(3)]})
    outputs.append(obj)
for o in list(bpy.data.objects):
    if o not in before and o not in outputs: bpy.data.objects.remove(o, do_unlink=True)
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o.name == 'Icosphere': bpy.data.objects.remove(o, do_unlink=True)

scene = bpy.context.scene
scene.world = bpy.data.worlds.new('Studio')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (0.14, 0.16, 0.20, 1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = 0.6
for location, power, size in [((3, -4, 6), 700, 5), ((-3, -1, 3), 450, 4), ((0, 4, 5), 650, 3)]:
    bpy.ops.object.light_add(type='AREA', location=location)
    light = bpy.context.object
    light.rotation_euler = (Vector((0, 0, 1.5)) - light.location).to_track_quat('-Z', 'Y').to_euler()
    light.data.energy = power
    light.data.shape = 'DISK'
    light.data.size = size
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.render.resolution_x = 800
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'AgX'
bpy.ops.wm.save_as_mainfile(filepath=str(HERE / 'sulley_fullbody.blend'))
render(HERE / 'preview_front.png', (0, 0, 1.5), (0, -7, 3))
render(HERE / 'preview_side.png', (0, 0.2, 1.5), (7, -1, 3))

# Export frozen bind-pose copies in inches using the previously verified FBX settings.
CONTENT.mkdir(parents=True, exist_ok=True)
for obj in outputs:
    obj.parent = None
    obj.matrix_world.identity()
    obj.data.transform(Matrix.Scale(1 / 0.0254, 4))
arm.parent = None
arm.data.transform(Matrix.Scale(1 / 0.0254, 4) @ arm.matrix_world)
arm.matrix_world.identity()
scene.unit_settings.system = 'IMPERIAL'
scene.unit_settings.scale_length = 0.0254
for obj in outputs:
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(filepath=str(CONTENT / f'sulley_{obj.name}.fbx'),
                            use_selection=True, object_types={'ARMATURE', 'MESH'},
                            add_leaf_bones=False, bake_anim=False, apply_unit_scale=True,
                            apply_scale_options='FBX_SCALE_UNITS', axis_forward='-Z', axis_up='Y',
                            mesh_smooth_type='FACE', use_mesh_modifiers=True,
                            use_armature_deform_only=True, armature_nodetype='NULL',
                            path_mode='STRIP', embed_textures=False, global_scale=1.0)
(HERE / 'fit_report.json').write_text(json.dumps({'mapping': bone_map, 'meshes': stats}, indent=2))
print('FULLBODY BUILD COMPLETE', stats)
