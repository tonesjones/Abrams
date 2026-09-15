"""Build V3: preserve the accepted body and swap in the downloaded Sulley head.

The donor skeleton is discarded.  The imported head is static in the stock
Abrams bind pose and receives a single stock ``head`` weight, so the existing
host animation graph, attachment points, physics and camera resources survive
the splice untouched.
"""
from pathlib import Path
import json
import shutil
import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
BASE = PROJECT / 'model_work/fullbody/sulley_fullbody.blend'
SOURCE = HERE / 'sulley_donor_source.glb'
CONTENT = PROJECT / 'tools/Reduced_CSDK_12/content/citadel_addons/sulley_head_donor/models/heroes_wip/abrams'

# Mapped from the donor's armature-baked world axes to Deadlock's stock bind
# pose.  After baking, Z is donor height, Y is face direction, X is width.
HEAD_SCALE_X = .135
HEAD_SCALE_Y = .143
HEAD_SCALE_Z = .110
HEAD_Y_OFFSET = .947
HEAD_Z_OFFSET = 1.406


def delete_indices(obj, indices):
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
               for token in ('Head', 'Eye', 'Eyelid', 'Brow', 'Lip', 'Jaw', 'Teeth')))


def bounds(obj):
    coords = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    return {'min': [min(point[i] for point in coords) for i in range(3)],
            'max': [max(point[i] for point in coords) for i in range(3)]}


def make_face_material(image):
    mat = bpy.data.materials.new('models/heroes_wip/abrams/materials/sulley_head_donor_face')
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    shader = next(node for node in nodes if node.type == 'BSDF_PRINCIPLED')
    texture = nodes.new('ShaderNodeTexImage')
    texture.image = image
    links.new(texture.outputs['Color'], shader.inputs['Base Color'])
    shader.inputs['Roughness'].default_value = .82
    return mat


def render(path, look, location):
    bpy.ops.object.camera_add(location=location)
    camera = bpy.context.object
    camera.rotation_euler = (Vector(look) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = .95
    bpy.context.scene.camera = camera
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(camera, do_unlink=True)


bpy.ops.wm.open_mainfile(filepath=str(BASE))
arm = next(obj for obj in bpy.context.scene.objects if obj.type == 'ARMATURE')
body = bpy.data.objects.get('body')
if body is None:
    raise RuntimeError('The accepted full-body source has no body object.')

# Remove the old face and its V2 procedural fur.  No non-head body vertex is
# changed; the existing stock weights are retained verbatim.
head_group = body.vertex_groups.get('head')
if head_group is None:
    raise RuntimeError('Accepted body has no stock head group.')
old_count = len(body.data.vertices)
delete_indices(body, [vertex.index for vertex in body.data.vertices
                      if any(group.group == head_group.index and group.weight > .5 for group in vertex.groups)])
body.name = 'body'
for material in body.data.materials:
    if material:
        material.name = 'models/heroes_wip/abrams/materials/sulley_head_donor_body'
for obj in list(bpy.context.scene.objects):
    if obj.type == 'MESH' and obj is not body and obj.name not in {'Icosphere'}:
        bpy.data.objects.remove(obj, do_unlink=True)

before = set(bpy.context.scene.objects)
bpy.ops.import_scene.gltf(filepath=str(SOURCE))
src = next(obj for obj in bpy.context.scene.objects if obj not in before and obj.type == 'MESH' and len(obj.data.vertices) > 1000)
# The GLB's visible pose is supplied by its own armature modifier.  Bake that
# pose before discarding the donor armature; using raw mesh coordinates folds
# the face back into its undeformed FBX bind state.
depsgraph = bpy.context.evaluated_depsgraph_get()
evaluated = src.evaluated_get(depsgraph)
face_mesh = bpy.data.meshes.new_from_object(evaluated, preserve_all_data_layers=True, depsgraph=depsgraph)
face = bpy.data.objects.new('face', face_mesh)
bpy.context.collection.objects.link(face)
for group in src.vertex_groups:
    face.vertex_groups.new(name=group.name)
for vertex in src.data.vertices:
    for membership in vertex.groups:
        face.vertex_groups[membership.group].add([vertex.index], membership.weight, 'REPLACE')
# Retain the head, facial controls, and its small neck skirt.  The body,
# clavicles and arms in this compact donor are intentionally excluded.
source_groups = {group.index: group.name for group in src.vertex_groups}
delete_indices(face, [vertex.index for vertex in face.data.vertices
                      if source_head_weight(vertex, source_groups) < .5
                      and sum(group.weight for group in vertex.groups
                              if 'Neck' in source_groups[group.group]) < .5])

# Bake the source object's world transform, then place the full untouched head
# region by its real axes.  This is intentionally a single fitted transform,
# not a local facial deformation.
for vertex in face.data.vertices:
    point = evaluated.matrix_world @ vertex.co
    vertex.co = Vector((point.x * HEAD_SCALE_X,
                        point.y * HEAD_SCALE_Y + HEAD_Y_OFFSET,
                        point.z * HEAD_SCALE_Z + HEAD_Z_OFFSET))
for group in list(face.vertex_groups):
    face.vertex_groups.remove(group)
face.vertex_groups.new(name='head').add([vertex.index for vertex in face.data.vertices], 1.0, 'REPLACE')

image = next(image for image in bpy.data.images if image.packed_file and image.size[0] > 0)
image.filepath_raw = str(HERE / 'sulley_head_donor_color.png')
image.file_format = 'PNG'
image.save()
face.data.materials.clear()
# Retain the donor's original material graph for the source closeup.  It uses
# the embedded color map directly and is the visual control for V3; the
# separately generated Source 2 material consumes the exact same PNG.
face_material = src.data.materials[0].copy()
face_material.name = 'models/heroes_wip/abrams/materials/sulley_head_donor_face'
face.data.materials.append(face_material)
for polygon in face.data.polygons:
    polygon.use_smooth = True
face.parent = arm
face.matrix_parent_inverse = arm.matrix_world.inverted()
modifier = face.modifiers.new('Stock Abrams head deformation', 'ARMATURE')
modifier.object = arm

# Delete the temporary imported donor rig and meshes.  Only our face remains.
for obj in list(bpy.context.scene.objects):
    if obj not in {body, face, arm} and obj.type in {'MESH', 'ARMATURE'}:
        bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.render.resolution_x = 800
scene.render.resolution_y = 800
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
render(HERE / 'head_donor_front.png', (0, -.02, 2.68), (0, -4, 2.78))
render(HERE / 'head_donor_threequarter.png', (0, -.02, 2.68), (1.8, -3.6, 2.82))

bpy.ops.wm.save_as_mainfile(filepath=str(HERE / 'sulley_head_donor.blend'))

# Export both custom meshes on the unmodified stock skeleton in inches.
CONTENT.mkdir(parents=True, exist_ok=True)
for obj in [body, face]:
    obj.parent = None
    obj.matrix_world.identity()
    obj.data.transform(__import__('mathutils').Matrix.Scale(1 / .0254, 4))
arm.parent = None
arm.data.transform(__import__('mathutils').Matrix.Scale(1 / .0254, 4) @ arm.matrix_world)
arm.matrix_world.identity()
scene.unit_settings.system = 'IMPERIAL'
scene.unit_settings.scale_length = .0254
for obj in [body, face]:
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(filepath=str(CONTENT / f'sulley_{obj.name}.fbx'), use_selection=True,
                             object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
                             bake_anim=False, apply_unit_scale=True,
                             apply_scale_options='FBX_SCALE_UNITS', axis_forward='-Z', axis_up='Y',
                             mesh_smooth_type='FACE', use_mesh_modifiers=True,
                             use_armature_deform_only=True, armature_nodetype='NULL',
                             path_mode='STRIP', embed_textures=False, global_scale=1.0)

report = {'revision': 'head_donor_v3', 'old_body_vertices': old_count,
          'body_vertices_after_old_face_removal': len(body.data.vertices),
          'donor_face_vertices': len(face.data.vertices), 'body_bounds_m': bounds(body),
          'face_bounds_m': bounds(face),
          'donor_source': str(SOURCE),
          'approach': 'Single transform of the new donor head; no procedural facial edits or fur strands.'}
(HERE / 'head_donor_report.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
