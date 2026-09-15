"""Check the likeness edit against the user-accepted full-body baseline."""
from pathlib import Path
import json
import bpy

HERE = Path(__file__).resolve().parent


def snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    arm = bpy.data.objects['Abrams_stock_rig']
    obj = bpy.data.objects['body']
    names = {g.index: g.name for g in obj.vertex_groups}
    points = [v.co.copy() for v in obj.data.vertices]
    weights = [{names[g.group]: g.weight for g in v.groups} for v in obj.data.vertices]
    bones = {b.name: [list(row) for row in b.matrix_local] for b in arm.data.bones}
    return points, weights, bones


before, old_weights, old_bones = snapshot(HERE / 'accepted_baseline/sulley_fullbody.blend')
after, new_weights, new_bones = snapshot(HERE / 'sulley_fullbody.blend')
assert old_bones == new_bones, 'The stock rig changed.'
assert len(after) >= len(before)
outside = [i for i, w in enumerate(old_weights) if w.get('head', 0) == 0]
largest = max((before[i] - after[i]).length for i in outside)
assert largest < .000001, f'Body outside the head moved: {largest} meters.'
for i, old in enumerate(old_weights):
    assert old == new_weights[i], f'Skin weights changed at original vertex {i}.'
for w in new_weights[len(before):]:
    assert w == {'head': 1.0}, 'New fur is not bound only to the head.'
result = {'rig_identical': True, 'original_skin_weights_identical': True,
          'body_vertices_outside_head_checked': len(outside),
          'maximum_outside_head_movement_m': largest,
          'new_fur_vertices': len(after) - len(before),
          'new_fur_binding': 'head: 1.0'}
(HERE / 'face_revision_verification.json').write_text(json.dumps(result, indent=2))
print(result)
