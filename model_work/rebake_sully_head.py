"""Re-bake Sully head from the saved blend: teal fur + spots, no portrait smear."""
from pathlib import Path
import bpy
from mathutils import Vector

BLEND = r"C:\TestCode\Abrams\model_work\sully_export\sully_cut.blend"
OUT = Path(r"C:\TestCode\Abrams\sully_textures\abrams_head_color_png_ce8a55ec.png")
ALT = Path(r"C:\TestCode\Abrams\sully_textures\abrams_head_basecolor_png_f84c4214.png")
PREVIEW = r"C:\TestCode\Abrams\model_work\sully_export\sully_face_preview.png"

bpy.ops.wm.open_mainfile(filepath=BLEND)
head = bpy.data.objects.get("sully_face")
if not head:
    raise SystemExit("no sully_face")

# Rebuild a clean fur shader on the first material (no portrait).
mat = head.data.materials[0]
mat.use_nodes = True
nt = mat.node_tree
nodes, links = nt.nodes, nt.links
nodes.clear()
out = nodes.new("ShaderNodeOutputMaterial")
bsdf = nodes.new("ShaderNodeBsdfPrincipled")
tex_coord = nodes.new("ShaderNodeTexCoord")
mapping = nodes.new("ShaderNodeMapping")
mapping.inputs["Scale"].default_value = (2.6, 2.6, 2.6)
links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])
vor = nodes.new("ShaderNodeTexVoronoi")
vor.inputs["Scale"].default_value = 2.8
links.new(mapping.outputs["Vector"], vor.inputs["Vector"])
ramp = nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position = 0.36
ramp.color_ramp.elements[0].color = (0.40, 0.14, 0.58, 1)
ramp.color_ramp.elements[1].position = 0.50
ramp.color_ramp.elements[1].color = (0.11, 0.64, 0.74, 1)
links.new(vor.outputs["Distance"], ramp.inputs["Fac"])
links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value = 0.88
links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

bpy.context.scene.render.engine = "CYCLES"
bpy.context.scene.cycles.device = "CPU"
bpy.context.scene.cycles.samples = 8
bpy.context.scene.render.bake.use_pass_direct = False
bpy.context.scene.render.bake.use_pass_indirect = False
bpy.context.scene.render.bake.use_pass_color = True
img = bpy.data.images.new("sully_head_bake2", 2048, 2048, alpha=False)
for m in head.data.materials:
    if not m or not m.use_nodes:
        continue
    n = m.node_tree.nodes.new("ShaderNodeTexImage")
    n.image = img
    m.node_tree.nodes.active = n

bpy.ops.object.select_all(action="DESELECT")
head.select_set(True)
bpy.context.view_layer.objects.active = head
bpy.ops.object.bake(type="DIFFUSE", pass_filter={"COLOR"})
img.filepath_raw = str(OUT)
img.file_format = "PNG"
img.save()
import shutil
shutil.copyfile(OUT, ALT)
print("rebaked", OUT)

# close-up preview
coords = [head.matrix_world @ v.co for v in head.data.vertices]
center = sum(coords, Vector((0, 0, 0))) / len(coords)
cam_loc = Vector((center.x + 4, center.y - 28, center.z + 2))
bpy.ops.object.camera_add(location=cam_loc)
cam = bpy.context.object
cam.rotation_euler = (center - cam_loc).to_track_quat("-Z", "Y").to_euler()
bpy.context.scene.camera = cam
bpy.ops.object.light_add(type="SUN", location=cam_loc)
bpy.context.object.data.energy = 5
bpy.context.scene.render.engine = "BLENDER_EEVEE_NEXT"
bpy.context.scene.render.resolution_x = 900
bpy.context.scene.render.resolution_y = 900
bpy.context.scene.render.filepath = PREVIEW
bpy.ops.render.render(write_still=True)
print("preview", PREVIEW)
