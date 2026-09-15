"""Offline clearance under the model's stored camera values, NOT a runtime proof."""
from pathlib import Path
import json
import math
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(HERE / 'compiled.gltf'))
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
body = next(o for o in bpy.data.objects if o.type == 'MESH' and len(o.data.vertices) > 5000 and len(o.data.vertices) != 18942)
arm.animation_data_create()
report = {'status': 'OFFLINE_HYPOTHESIS_ONLY',
          'assumptions': ['Stored camera offsets are honored in-game.',
                          'Camera right is Blender +X; camera forward is Blender -Y.',
                          'No world collision, camera smoothing, or gameplay aim-layer blending.'],
          'samples': []}
for name in ['primary_stand_idle', 'primary_run_n']:
    action = bpy.data.actions[name]
    arm.animation_data.action = action
    arm.animation_data.action_slot = action.slots[0]
    for fraction in (0, .25, .5, .75, 1):
        bpy.context.scene.frame_set(round(action.frame_range[0] + fraction * (action.frame_range[1] - action.frame_range[0])))
        bpy.context.view_layer.update()
        deps = bpy.context.evaluated_depsgraph_get()
        tree = BVHTree.FromObject(body, deps)
        for mode, back in [('normal', 111), ('aim_distance', 75)]:
            camera = Vector((44 * .0254, back * .0254, 100 * .0254))
            results = []
            for pitch in (-45, 0, 45):
                theta = math.radians(pitch)
                direction = Vector((0, -math.cos(theta), math.sin(theta)))
                origin = body.matrix_world.inverted() @ camera
                ray = body.matrix_world.to_3x3().inverted() @ direction
                hit = tree.ray_cast(origin, ray, 100)[0]
                results.append({'pitch': pitch, 'center_ray_hits_body': hit is not None})
            report['samples'].append({'clip': name, 'frame_fraction': fraction, 'mode': mode, 'rays': results})
report['all_center_rays_clear'] = all(not r['center_ray_hits_body'] for s in report['samples'] for r in s['rays'])
(HERE / 'camera_report.json').write_text(json.dumps(report, indent=2))
print('Hypothetical center-ray clearance:', report['all_center_rays_clear'])
