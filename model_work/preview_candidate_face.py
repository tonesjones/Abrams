"""Render an unchanged GLB candidate's head for approval; no export or packaging."""
import bpy, sys
from pathlib import Path
from mathutils import Vector

source = Path(sys.argv[-1])
out = Path(__file__).resolve().parent / "candidate_preview"
out.mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(source))
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
depsgraph = bpy.context.evaluated_depsgraph_get()
evaluated_meshes = [o.evaluated_get(depsgraph) for o in meshes]
coords = [o.matrix_world @ v.co for o in evaluated_meshes for v in o.data.vertices]
lo = Vector(tuple(min(p[i] for p in coords) for i in range(3)))
hi = Vector(tuple(max(p[i] for p in coords) for i in range(3)))
extent = hi - lo
head_points = [p for p in coords if p.z > lo.z + extent.z * .72]
center = sum(head_points, Vector()) / len(head_points)

world = bpy.data.worlds.new("Studio")
bpy.context.scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (.035, .04, .055, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = .8
for offset, power, size in [((3,-5,4),3500,5),((-3,-3,2),2200,4)]:
    loc = center + Vector(offset) * (extent.z / 3)
    bpy.ops.object.light_add(type="AREA", location=loc)
    lamp=bpy.context.object
    lamp.rotation_euler=(center-loc).to_track_quat('-Z','Y').to_euler()
    lamp.data.energy=power; lamp.data.shape='DISK'; lamp.data.size=size

scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE_NEXT'
scene.render.resolution_x=900; scene.render.resolution_y=900; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.look='AgX - Medium High Contrast'; scene.view_settings.exposure=1.5
for name, direction in [('front',(0,-1,.04)),('threequarter',(.55,-1,.08))]:
    bpy.ops.object.camera_add()
    camera=bpy.context.object
    camera.location=center+Vector(direction)*(extent.z*1.25)
    camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.type='ORTHO'; camera.data.ortho_scale=extent.z*.35; camera.data.clip_end=10000
    scene.camera=camera; scene.render.filepath=str(out/f'{name}.png')
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(camera,do_unlink=True)
