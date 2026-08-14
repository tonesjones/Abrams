import bpy
from mathutils import Matrix, Vector
from pathlib import Path

BLEND = r"C:\TestCode\Abrams\model_work\sully_export\sully_cut.blend"
CONTENT = Path(r"C:\TestCode\Abrams\tools\Reduced_CSDK_12\content\citadel_addons\sully_abrams\models\heroes_wip\abrams")
PREVIEW = r"C:\TestCode\Abrams\model_work\sully_export\cut_preview.png"
# Measured stock face center after x39.37 scale
FACE_CENTER = Vector((-0.000004, 3.361, 102.962))

bpy.ops.wm.open_mainfile(filepath=BLEND)
head = bpy.data.objects.get("sully_face")
arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
body = next(o for o in bpy.data.objects if o.type == "MESH" and o != head)
print("head loc before", tuple(head.matrix_world.translation), "verts", len(head.data.vertices))

# Unparent, move to face, reparent keeping world transform
head.parent = None
head.matrix_world.translation = FACE_CENTER
# Better: keep current mesh local verts; they were built at FACE_CENTER in world
# already, then parenting yanked the object origin. Reset object matrix to identity
# at world origin so vertex positions (built in world inches) are correct.
head.matrix_world = Matrix.Identity(4)
print("head loc after reset", tuple(head.matrix_world.translation))
# vertices should already sit around FACE_CENTER if they were created in world space
coords = [head.matrix_world @ v.co for v in head.data.vertices]
center = sum(coords, Vector((0, 0, 0))) / len(coords)
print("vert center", tuple(center))
# If verts are near origin, translate them to FACE_CENTER
if center.length < 20:
    print("translating verts to face center")
    for v in head.data.vertices:
        v.co += FACE_CENTER
    coords = [head.matrix_world @ v.co for v in head.data.vertices]
    center = sum(coords, Vector((0, 0, 0))) / len(coords)
    print("vert center now", tuple(center))

head.parent = arm
head.matrix_parent_inverse = arm.matrix_world.inverted()
mod = head.modifiers.get("Armature") or head.modifiers.new("Armature", "ARMATURE")
mod.object = arm

def export_fbx(path, objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(
        filepath=str(path),
        use_selection=True,
        add_leaf_bones=False,
        bake_anim=False,
        mesh_smooth_type="FACE",
        path_mode="COPY",
        embed_textures=True,
        armature_nodetype="NULL",
        use_armature_deform_only=True,
    )
    print("Wrote", path)

export_fbx(CONTENT / "sully_face.fbx", [head, arm])
export_fbx(CONTENT / "abrams_body_nohead.fbx", [body, arm])

world = bpy.context.scene.world or bpy.data.worlds.new("W")
bpy.context.scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.2, 0.2, 0.24, 1)
cam_loc = Vector((28, -80, 110))
bpy.ops.object.camera_add(location=cam_loc)
cam = bpy.context.object
cam.rotation_euler = (Vector((0, 4, 104)) - cam_loc).to_track_quat("-Z", "Y").to_euler()
bpy.context.scene.camera = cam
bpy.ops.object.light_add(type="SUN", location=cam_loc)
bpy.context.object.data.energy = 6
bpy.context.scene.render.engine = "BLENDER_EEVEE_NEXT"
bpy.context.scene.render.resolution_x = 900
bpy.context.scene.render.resolution_y = 900
bpy.context.scene.render.filepath = PREVIEW
bpy.ops.render.render(write_still=True)
print("Wrote", PREVIEW)
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
