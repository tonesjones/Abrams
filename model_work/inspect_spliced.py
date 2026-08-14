"""Blender bounds check for a Source2Viewer glTF export of the spliced host.

Export first:
  tools\\s2v-cli\\Source2Viewer-CLI.exe -i model_work\\abrams_spliced.vmdl_c -d --gltf_export_format gltf --gltf_export_animations
"""
import sys
from pathlib import Path

import bpy
from mathutils import Vector

path = r"C:\TestCode\Abrams\model_work\abrams_spliced.gltf"
if not Path(path).exists():
    print("missing", path)
    print("export a glTF from abrams_spliced.vmdl_c with Source2Viewer-CLI first")
    sys.exit(1)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=path)

def bounds(obj, deformed=False):
    if deformed and obj.modifiers:
        deps = bpy.context.evaluated_depsgraph_get()
        ev = obj.evaluated_get(deps)
        mesh = ev.to_mesh()
        coords = [obj.matrix_world @ v.co for v in mesh.vertices]
        ev.to_mesh_clear()
    else:
        coords = [obj.matrix_world @ v.co for v in obj.data.vertices]
    xs, ys, zs = [c.x for c in coords], [c.y for c in coords], [c.z for c in coords]
    mn = Vector((min(xs), min(ys), min(zs)))
    mx = Vector((max(xs), max(ys), max(zs)))
    return mn, mx, mx - mn, (mn + mx) * 0.5

print("=== OBJECTS ===")
for o in bpy.data.objects:
    if o.type != "MESH":
        if o.type == "ARMATURE":
            print(f"ARMATURE {o.name} bones={len(o.data.bones)} loc={tuple(o.location)} scale={tuple(o.scale)}")
        continue
    print(f"MESH {o.name} verts={len(o.data.vertices)} loc={tuple(o.location)} scale={tuple(o.scale)} parent={o.parent} mods={[m.type for m in o.modifiers]} groups={len(o.vertex_groups)}")
    for label, deformed in [("raw", False), ("deformed", True)]:
        try:
            mn, mx, size, c = bounds(o, deformed)
            print(f"  {label} min={tuple(round(x,4) for x in mn)} max={tuple(round(x,4) for x in mx)} size={tuple(round(x,4) for x in size)} center={tuple(round(x,4) for x in c)}")
        except Exception as e:
            print(f"  {label} ERR {e}")
    # sample groups
    if o.vertex_groups:
        names = [g.name for g in o.vertex_groups]
        print("  groups sample", names[:8], "...", names[-4:] if len(names)>8 else "")
        # weight histogram: how many verts have head as top group
        head = None
        for g in o.vertex_groups:
            if g.name == "head" or g.name.endswith("_head"):
                head = g.index
                break
        if head is not None:
            top_head = 0
            for v in o.data.vertices:
                if not v.groups:
                    continue
                top = max(v.groups, key=lambda g: g.weight)
                if top.group == head:
                    top_head += 1
            print(f"  verts with top group head: {top_head}/{len(o.data.vertices)}")
print("DONE")
