from pathlib import Path
import bpy
from mathutils import Vector
HERE=Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(HERE/'sulley_donor_source.glb'))
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE_NEXT'; scene.render.resolution_x=800; scene.render.resolution_y=800; scene.render.image_settings.file_format='PNG'
bpy.ops.object.camera_add(location=(0,-18,11.5)); cam=bpy.context.object; cam.rotation_euler=(Vector((0,-6.6,11.5))-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.lens=58; scene.camera=cam
scene.render.filepath=str(HERE/'donor_face_source.png'); bpy.ops.render.render(write_still=True)
