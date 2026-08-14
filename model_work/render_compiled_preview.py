import bpy
from mathutils import Vector

GLTF = r"C:\TestCode\Abrams\tools\Reduced_CSDK_12\game\citadel_addons\sully_abrams\models\heroes_wip\abrams\abrams.gltf"
OUT_DIR = r"C:\TestCode\Abrams\model_work\sully_export"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLTF)
bpy.context.view_layer.update()

meshes = [o for o in bpy.data.objects if o.type == "MESH"]
meshes.sort(key=lambda o: len(o.data.vertices))

world = bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.15, 0.15, 0.18, 1)

# Render each mesh isolated
for i, o in enumerate(meshes):
    for other in meshes:
        other.hide_render = other is not o
    mat = bpy.data.materials.new(f"m{i}")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.15, 0.75, 0.8, 1)
    mat.use_backface_culling = False
    o.data.materials.clear()
    o.data.materials.append(mat)
    dims = o.dimensions
    loc = o.matrix_world.translation
    print(f"render {i} verts={len(o.data.vertices)} dims={tuple(dims)}")
    center = loc + Vector((0, 0, dims.z * 0.3))
    dist = max(dims) * 2.2 + 0.5
    cam_loc = center + Vector((dist * 0.2, -dist, dist * 0.15))
    bpy.ops.object.camera_add(location=cam_loc)
    cam = bpy.context.object
    cam.rotation_euler = (center - cam_loc).to_track_quat("-Z", "Y").to_euler()
    cam.data.clip_start = 0.01
    cam.data.clip_end = 10000
    bpy.context.scene.camera = cam
    bpy.ops.object.light_add(type="SUN", location=cam_loc)
    bpy.context.object.data.energy = 6
    bpy.context.scene.render.engine = "BLENDER_EEVEE_NEXT"
    bpy.context.scene.render.resolution_x = 700
    bpy.context.scene.render.resolution_y = 700
    out = f"{OUT_DIR}\\mesh_{i}_{len(o.data.vertices)}v.png"
    bpy.context.scene.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print("Wrote", out)
    # cleanup cam/light
    bpy.data.objects.remove(cam, do_unlink=True)
