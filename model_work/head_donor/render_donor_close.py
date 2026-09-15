from pathlib import Path
import bpy
from mathutils import Vector
HERE=Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(HERE/'sulley_donor_source.glb'))
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE_NEXT'; scene.render.resolution_x=900; scene.render.resolution_y=900; scene.render.image_settings.file_format='PNG'
scene.world=bpy.data.worlds.new('world'); scene.world.use_nodes=True; scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.03,.035,.05,1)
look=Vector((6.7,-14.4,3.0)); loc=Vector((6.7,-40,3.0))
bpy.ops.object.camera_add(location=loc); cam=bpy.context.object; cam.rotation_euler=(look-loc).to_track_quat('-Z','Y').to_euler(); cam.data.type='ORTHO';cam.data.ortho_scale=6.0;scene.camera=cam
for p,e in [((12,-25,10),900),((0,-20,8),500)]:
 bpy.ops.object.light_add(type='AREA',location=p);l=bpy.context.object;l.rotation_euler=(look-l.location).to_track_quat('-Z','Y').to_euler();l.data.energy=e;l.data.size=5
scene.render.filepath=str(HERE/'donor_face_close_raw.png');bpy.ops.render.render(write_still=True)
