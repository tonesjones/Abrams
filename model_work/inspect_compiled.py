"""Print mesh bounds and armature info from the compiled Isolation B glTF."""
import bpy
from mathutils import Vector

path = r"C:\TestCode\Abrams\tools\Reduced_CSDK_12\game\citadel_addons\sully_abrams\models\heroes_wip\abrams\abrams.gltf"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=path)

def bounds(obj):
    coords = [obj.matrix_world @ v.co for v in obj.data.vertices]
    xs, ys, zs = [c.x for c in coords], [c.y for c in coords], [c.z for c in coords]
    mn = Vector((min(xs), min(ys), min(zs)))
    mx = Vector((max(xs), max(ys), max(zs)))
    return (mn + mx) * 0.5, mx - mn, mn, mx

print("=== OBJECTS ===")
for o in bpy.data.objects:
    print(f"{o.type:10} {o.name!r} loc={tuple(o.location)} parent={o.parent}")
    if o.type == "MESH":
        c, s, mn, mx = bounds(o)
        print(f"           verts={len(o.data.vertices)} center={tuple(c)} size={tuple(s)}")
        print(f"           min={tuple(mn)} max={tuple(mx)}")
        print(f"           groups={len(o.vertex_groups)} {[g.name for g in o.vertex_groups][:12]}")
        print(f"           mats={[m.name if m else None for m in o.data.materials]}")
    if o.type == "ARMATURE":
        print(f"           bones={len(o.data.bones)}")
        for b in list(o.data.bones)[:8]:
            print(f"           bone {b.name} head={tuple(b.head_local)} tail={tuple(b.tail_local)}")
print("DONE")
