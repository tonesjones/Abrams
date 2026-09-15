"""Render the actual compiled face mesh with the donor material control."""
from pathlib import Path
import bpy
from mathutils import Vector
HERE=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(HERE/'sulley_head_donor.blend'))
template=bpy.data.materials.get('models/heroes_wip/abrams/materials/sulley_head_donor_face').copy()
for obj in list(bpy.data.objects):
    if obj.type in {'MESH','ARMATURE'}: bpy.data.objects.remove(obj,do_unlink=True)
bpy.ops.import_scene.gltf(filepath=str(HERE/'compiled.gltf'))
face=next(obj for obj in bpy.data.objects if obj.type=='MESH' and len(obj.data.vertices)==508)
face.data.materials.clear();face.data.materials.append(template)
scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE_NEXT';scene.render.resolution_x=800;scene.render.resolution_y=800;scene.render.image_settings.file_format='PNG'
bpy.ops.object.camera_add(location=(0,-4,2.78));cam=bpy.context.object;cam.rotation_euler=(Vector((0,-.02,2.68))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=.95;scene.camera=cam;scene.render.filepath=str(HERE/'compiled_face_close.png');bpy.ops.render.render(write_still=True)
