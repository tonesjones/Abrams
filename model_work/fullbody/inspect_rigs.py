"""Inventory both source rigs without changing the original assets."""
import json
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parent
report = {}
inputs = [('abrams', ROOT / 'stock/abrams.gltf'), ('sulley', ROOT.parent / 'import_head/sully.glb')]
if (ROOT / 'donor.gltf').exists(): inputs.append(('compiled_donor', ROOT / 'donor.gltf'))
for label, path in inputs:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path))
    bpy.context.view_layer.update()
    arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    bones = {}
    for b in arm.data.bones:
        p = arm.pose.bones[b.name]
        bones[b.name] = {'parent': b.parent.name if b.parent else None,
                         'rest': list(arm.matrix_world @ b.head_local),
                         'posed': list(arm.matrix_world @ p.head),
                         'tail': list(arm.matrix_world @ b.tail_local)}
    meshes = []
    for o in bpy.data.objects:
        if o.type != 'MESH': continue
        ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get())
        points = [ev.matrix_world @ v.co for v in ev.data.vertices]
        meshes.append({'name': o.name, 'vertices': len(o.data.vertices),
                       'min': [min(p[i] for p in points) for i in range(3)],
                       'max': [max(p[i] for p in points) for i in range(3)],
                       'materials': [m.name if m else None for m in o.data.materials]})
    report[label] = {'armature': arm.name, 'matrix': [list(r) for r in arm.matrix_world],
                     'bones': bones, 'meshes': meshes, 'actions': [a.name for a in bpy.data.actions]}
(ROOT / 'rig_inventory.json').write_text(json.dumps(report, indent=2))
print('Wrote rig_inventory.json')
