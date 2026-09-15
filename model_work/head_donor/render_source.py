"""Render and inventory the untouched downloaded Sulley donor."""
import json
from pathlib import Path
import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(HERE / 'sulley_donor_source.glb'))

meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
armatures = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE']
for obj in meshes:
    for poly in obj.data.polygons:
        poly.use_smooth = True

world = bpy.data.worlds.new('Studio')
bpy.context.scene.world = world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (.035, .04, .055, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = .4

coords = [o.matrix_world @ v.co for o in meshes for v in o.data.vertices]
lo = Vector([min(p[i] for p in coords) for i in range(3)])
hi = Vector([max(p[i] for p in coords) for i in range(3)])
center = (lo + hi) / 2
extent = hi - lo
for loc, power, size in [(center + Vector((4, -6, 6)), 850, 5), (center + Vector((-4, -3, 3)), 500, 4)]:
    bpy.ops.object.light_add(type='AREA', location=loc)
    lamp = bpy.context.object
    lamp.rotation_euler = (center - loc).to_track_quat('-Z', 'Y').to_euler()
    lamp.data.energy = power
    lamp.data.shape = 'DISK'
    lamp.data.size = size

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.render.resolution_x = 900
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.look = 'AgX - Medium High Contrast'
for name, offset in [('donor_front', Vector((0, -max(extent.y, extent.z) * 2.5, extent.z * .25))),
                     ('donor_threequarter', Vector((extent.x * 1.5, -max(extent.y, extent.z) * 2.2, extent.z * .3)))]:
    bpy.ops.object.camera_add(location=center + offset)
    camera = bpy.context.object
    camera.rotation_euler = (center + Vector((0, 0, extent.z * .06)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.lens = 52
    scene.camera = camera
    scene.render.filepath = str(HERE / f'{name}.png')
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(camera, do_unlink=True)

report = {
    'bounds': {'min': list(lo), 'max': list(hi), 'extent': list(extent)},
    'meshes': [{'name': o.name, 'vertices': len(o.data.vertices), 'polygons': len(o.data.polygons),
                'materials': [m.name if m else None for m in o.data.materials],
                'groups': len(o.vertex_groups)} for o in meshes],
    'armatures': [{'name': o.name, 'bones': len(o.data.bones)} for o in armatures],
    'images': [{'name': i.name, 'size': list(i.size), 'packed': bool(i.packed_file)} for i in bpy.data.images],
}
(HERE / 'donor_inventory.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
