"""Comparable front and three-quarter close-ups of the actual mesh."""
from pathlib import Path
import sys
import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
baseline = '--baseline' in sys.argv
folder = HERE / 'accepted_baseline' if baseline else HERE
bpy.ops.wm.open_mainfile(filepath=str(folder / 'sulley_fullbody.blend'))
scene = bpy.context.scene
scene.render.resolution_x = 800
scene.render.resolution_y = 800
scene.render.resolution_percentage = 100
for name, location in [('front', (0, -4, 2.8)), ('threequarter', (2, -4, 2.85))]:
    bpy.ops.object.camera_add(location=location)
    camera = bpy.context.object
    camera.rotation_euler = (Vector((0, 0, 2.72)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = .85
    scene.camera = camera
    scene.render.filepath = str(folder / ('face_' + name + '.png'))
    bpy.ops.render.render(write_still=True)
