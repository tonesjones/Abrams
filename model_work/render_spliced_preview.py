import bpy
from mathutils import Vector
from pathlib import Path

GLTF = r"C:\TestCode\Abrams\model_work\abrams_spliced.gltf"
OUT = r"C:\TestCode\Abrams\model_work\sully_export\spliced_stockhost_preview.png"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLTF)
bpy.context.view_layer.update()

meshes = [o for o in bpy.data.objects if o.type == "MESH"]
print("meshes", [(o.name, len(o.data.vertices)) for o in meshes])

world = bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.15, 0.15, 0.18, 1)

# show body + face only
keep = []
for o in meshes:
    n = o.name.lower()
    show = o.type == "MESH" and "gun" not in n and "book" not in n and "ico" not in n
    o.hide_render = not show
    o.hide_viewport = not show
    if show:
        keep.append(o)

coords = []
for o in keep:
    coords.extend(o.matrix_world @ v.co for v in o.data.vertices)
xs, ys, zs = [c.x for c in coords], [c.y for c in coords], [c.z for c in coords]
mn = Vector((min(xs), min(ys), min(zs)))
mx = Vector((max(xs), max(ys), max(zs)))
center = (mn + mx) * 0.5
size = mx - mn
print("combined min", tuple(mn), "max", tuple(mx), "size", tuple(size), "center", tuple(center))

dist = max(size) * 1.6
cam_loc = center + Vector((dist * 0.55, -dist, dist * 0.25))
bpy.ops.object.camera_add(location=cam_loc)
cam = bpy.context.object
cam.rotation_euler = (center - cam_loc).to_track_quat("-Z", "Y").to_euler()
cam.data.clip_start = 0.01
cam.data.clip_end = 10000
bpy.context.scene.camera = cam
bpy.ops.object.light_add(type="SUN", location=cam_loc)
bpy.context.object.data.energy = 6
bpy.context.scene.render.engine = "BLENDER_EEVEE_NEXT"
bpy.context.scene.render.resolution_x = 900
bpy.context.scene.render.resolution_y = 1100
bpy.context.scene.render.filepath = OUT
Path(OUT).parent.mkdir(parents=True, exist_ok=True)
bpy.ops.render.render(write_still=True)
print("Wrote", OUT)
