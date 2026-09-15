"""Approval-only preview: untouched Sulley GLB head on the accepted body.

No FBX export, Source 2 compile, VPK creation, or game-folder access occurs.
"""
import json
from pathlib import Path
import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASE = ROOT / 'fullbody' / 'accepted_baseline' / 'sulley_fullbody.blend'
SOURCE = Path(r'C:\Users\Owner\Downloads\sully.glb')
SCALE = .044
HEAD_OFFSET_Z = -.12


def delete_vertices(obj, indices):
    if not indices:
        return
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    for index in indices:
        obj.data.vertices[index].select = True
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.delete(type='VERT')
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.select_set(False)


def source_head_weight(vertex, names):
    return sum(group.weight for group in vertex.groups if any(token in names[group.group]
               for token in ('Head', 'Eye', 'Eyelid', 'Brow', 'Lip', 'Jaw', 'Teeth', 'mouth_master')))


def render(path, target, location, scale, closeup=False):
    bpy.ops.object.camera_add(location=location)
    camera = bpy.context.object
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = scale
    bpy.context.scene.camera = camera
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(camera, do_unlink=True)


bpy.ops.wm.open_mainfile(filepath=str(BASE))
arm = next(obj for obj in bpy.context.scene.objects if obj.type == 'ARMATURE')
body = bpy.data.objects.get('body')
if body is None:
    raise RuntimeError('Accepted baseline body was not found.')

# The accepted baseline's head (including its experimental fur) is display-only
# removed.  Partial head weights had left V2 face-shell geometry inside the
# donor muzzle in the first preview, so every vertex with any stock-head
# membership is now removed before the untouched donor is introduced.
head_group = body.vertex_groups.get('head')
if head_group is None:
    raise RuntimeError('Accepted baseline lacks a head vertex group.')
body_before = len(body.data.vertices)
delete_vertices(body, [v.index for v in body.data.vertices
                       if any(g.group == head_group.index and g.weight > 1e-6 for g in v.groups)])
# Remove only the central residual head/fur shell from the accepted body.  The
# retained arms and torso stay visible; this prevents the rejected V2 facial
# shell from peeking out behind the untouched donor unit in this preview.
delete_vertices(body, [v.index for v in body.data.vertices
                       if v.co.z > 2.35 and abs(v.co.x) < .72])
for obj in list(bpy.context.scene.objects):
    if obj.type == 'MESH' and obj is not body:
        bpy.data.objects.remove(obj, do_unlink=True)

target_head = arm.matrix_world @ arm.data.bones['head'].head_local
before = set(bpy.context.scene.objects)
bpy.ops.import_scene.gltf(filepath=str(SOURCE))
source_arm = next(obj for obj in bpy.context.scene.objects if obj not in before and obj.type == 'ARMATURE')
source_meshes = [obj for obj in bpy.context.scene.objects
                 if obj not in before and obj.type == 'MESH' and not obj.name.startswith('Icosphere')]
source_heads = {bone.name: source_arm.matrix_world @ source_arm.pose.bones[bone.name].head
                for bone in source_arm.data.bones}
source_head = source_heads[next(name for name in source_heads if name.removeprefix('Bip001_').split('_')[0] == 'Head')]

outputs = []
for ordinal, src in enumerate(sorted(source_meshes, key=lambda obj: -len(obj.data.vertices))):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = src.evaluated_get(depsgraph)
    mesh = bpy.data.meshes.new_from_object(evaluated, preserve_all_data_layers=True, depsgraph=depsgraph)
    obj = bpy.data.objects.new('untouched_head_surface' if ordinal == 0 else 'untouched_head_eyes', mesh)
    bpy.context.collection.objects.link(obj)
    for group in src.vertex_groups:
        obj.vertex_groups.new(name=group.name)
    for vertex in src.data.vertices:
        for membership in vertex.groups:
            obj.vertex_groups[membership.group].add([vertex.index], membership.weight, 'REPLACE')
    names = {group.index: group.name for group in obj.vertex_groups}
    # The original head contains some face surfaces whose skin membership is
    # shared with the upper torso.  Crop the main mesh by its actual head-space
    # height rather than discarding those surfaces by bone name; eyes remain a
    # separate complete mesh.  This is selection only: no surviving source
    # coordinate is reshaped before one uniform placement transform.
    if ordinal == 0:
        delete_vertices(obj, [v.index for v in obj.data.vertices
                              if (evaluated.matrix_world @ v.co).z < source_head.z - 8.0])
    for vertex in obj.data.vertices:
        point = evaluated.matrix_world @ vertex.co
        local = point - source_head
        vertex.co = target_head + local * SCALE + Vector((0, 0, HEAD_OFFSET_Z))
    obj.vertex_groups.clear()
    obj.vertex_groups.new(name='head').add(list(range(len(obj.data.vertices))), 1.0, 'REPLACE')
    obj.parent = arm
    obj.matrix_parent_inverse = arm.matrix_world.inverted()
    # This approval render is intentionally static.  Applying the armature
    # modifier here would already be a rig-binding experiment and can obscure
    # the untouched donor's real presentation.  Binding is a later, separate
    # approval gate after this visual fit is accepted.
    for poly in obj.data.polygons:
        poly.use_smooth = True
    outputs.append(obj)

for obj in list(bpy.context.scene.objects):
    if obj not in {body, arm, *outputs} and obj.type in {'MESH', 'ARMATURE'}:
        bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.render.resolution_x = 900
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.look = 'AgX - Medium High Contrast'
scene.view_settings.exposure = -.65
world = bpy.data.worlds.new('Approval Studio')
scene.world = world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (.035, .045, .065, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = .55
for location, energy, size in [((3, -4, 5), 1000, 4), ((-3, -2, 3), 650, 4), ((0, 3, 5), 900, 3)]:
    bpy.ops.object.light_add(type='AREA', location=location)
    light = bpy.context.object
    light.rotation_euler = (Vector((0, 0, 1.6)) - light.location).to_track_quat('-Z', 'Y').to_euler()
    light.data.energy = energy
    light.data.shape = 'DISK'
    light.data.size = size

render(HERE / 'body_front.png', (0, .15, 1.55), (0, -7, 3), 3.65)
render(HERE / 'body_threequarter.png', (0, .15, 1.55), (4.5, -6, 3.1), 3.65)
render(HERE / 'face_front.png', (0, .13, 2.72), (0, -4.0, 2.84), .92)
render(HERE / 'face_threequarter.png', (0, .13, 2.72), (1.9, -3.6, 2.88), .92)
body.hide_render = True
render(HERE / 'source_head_control.png', (0, .13, 2.72), (0, -4.0, 2.84), .92)
body.hide_render = False

report = {
    'scope': 'approval-only preview; no compile/package/install',
    'source': str(SOURCE),
    'source_head_transform': {'uniform_scale': SCALE, 'z_offset_m': HEAD_OFFSET_Z, 'target_head_m': list(target_head)},
    'preserved': ['source head coordinates after selection', 'separate eye mesh', 'source materials and UV mapping', 'horn and mouth geometry'],
    'not_applied': ['facial reshaping', 'smoothing modifier', 'procedural fur', 'V2 face edits', 'V3 donor substitution'],
    'accepted_body_head_vertices_removed_for_preview': body_before - len(body.data.vertices),
    'old_v2_face_objects_remaining': 0,
    'source_head_control_render': str(HERE / 'source_head_control.png'),
    'new_head_meshes': [{'name': obj.name, 'vertices': len(obj.data.vertices)} for obj in outputs],
    'fit_limitations': 'The source head is placed at the stock head location for a static visual fit only. Neck motion and the later single-head-weight binding are intentionally not tested here.'
}
(HERE / 'report.json').write_text(json.dumps(report, indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(HERE / 'untouched_head_approval.blend'))
print(json.dumps(report, indent=2))
