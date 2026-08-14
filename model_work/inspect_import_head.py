"""Inspect the dropped Sketchfab GLB. Read-only besides writing a preview PNG."""
from __future__ import annotations

from pathlib import Path

import bpy
from mathutils import Vector

GLB = Path(r"C:\TestCode\Abrams\model_work\import_head\sully.glb")
PREVIEW = Path(r"C:\TestCode\Abrams\model_work\import_head\inspect_preview.png")


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def bounds(obj):
    coords = [obj.matrix_world @ v.co for v in obj.data.vertices]
    xs = [c.x for c in coords]
    ys = [c.y for c in coords]
    zs = [c.z for c in coords]
    mn = Vector((min(xs), min(ys), min(zs)))
    mx = Vector((max(xs), max(ys), max(zs)))
    return (mn + mx) * 0.5, mx - mn, mn, mx


def main():
    clear()
    bpy.ops.import_scene.gltf(filepath=str(GLB))
    print("FILE", GLB, "bytes", GLB.stat().st_size)
    print("OBJECTS", [(o.type, o.name, len(o.data.vertices) if o.type == "MESH" else "-") for o in bpy.data.objects])
    print("ARMATURES", [o.name for o in bpy.data.objects if o.type == "ARMATURE"])
    print("IMAGES", [(im.name, tuple(im.size), im.filepath) for im in bpy.data.images])
    print("MATERIALS", [m.name for m in bpy.data.materials])

    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    all_coords = []
    for o in meshes:
        center, size, mn, mx = bounds(o)
        tris = sum(len(p.vertices) - 2 for p in o.data.polygons)
        n_uv = len(o.data.uv_layers)
        n_vg = len(o.vertex_groups)
        mats = [slot.material.name if slot.material else None for slot in o.material_slots]
        print(
            f"MESH {o.name} verts={len(o.data.vertices)} tris={tris} "
            f"uv_layers={n_uv} groups={n_vg} mats={mats}"
        )
        print(f"  center={tuple(round(x, 4) for x in center)} size={tuple(round(x, 4) for x in size)}")
        print(f"  min={tuple(round(x, 4) for x in mn)} max={tuple(round(x, 4) for x in mx)}")
        print(f"  groups={[g.name for g in o.vertex_groups][:20]}")
        all_coords.extend([o.matrix_world @ v.co for v in o.data.vertices])

    if all_coords:
        xs = [c.x for c in all_coords]
        ys = [c.y for c in all_coords]
        zs = [c.z for c in all_coords]
        mn = Vector((min(xs), min(ys), min(zs)))
        mx = Vector((max(xs), max(ys), max(zs)))
        size = mx - mn
        center = (mn + mx) * 0.5
        print("WORLD_CENTER", tuple(round(x, 4) for x in center))
        print("WORLD_SIZE", tuple(round(x, 4) for x in size))
        print("WORLD_MIN", tuple(round(x, 4) for x in mn))
        print("WORLD_MAX", tuple(round(x, 4) for x in mx))

        # Eyes sit near the face; use them for a head close-up.
        eyes = next((o for o in meshes if "83" in o.name or "eye" in o.name.lower()), None)
        look = Vector(eyes.matrix_world.translation) if eyes else center
        dist = 80.0
        shots = {
            "inspect_preview.png": Vector((look.x - dist, look.y, look.z + 8)),
            "inspect_preview_front.png": Vector((look.x, look.y - dist, look.z + 4)),
            "inspect_preview_3q.png": Vector((look.x - dist * 0.7, look.y - dist * 0.7, look.z + 10)),
        }
        world = bpy.context.scene.world or bpy.data.worlds.new("W")
        bpy.context.scene.world = world
        world.use_nodes = True
        world.node_tree.nodes["Background"].inputs[0].default_value = (0.18, 0.18, 0.22, 1)
        bpy.ops.object.light_add(type="SUN", location=look + Vector((20, -40, 60)))
        bpy.context.object.data.energy = 5
        bpy.ops.object.light_add(type="AREA", location=look + Vector((30, -30, 40)))
        bpy.context.object.data.energy = 400
        bpy.context.scene.render.engine = "BLENDER_EEVEE_NEXT"
        bpy.context.scene.render.resolution_x = 900
        bpy.context.scene.render.resolution_y = 900
        for name, cam_loc in shots.items():
            bpy.ops.object.camera_add(location=cam_loc)
            cam = bpy.context.object
            cam.rotation_euler = (look - cam_loc).to_track_quat("-Z", "Y").to_euler()
            cam.data.clip_start = 0.1
            cam.data.clip_end = 4000
            bpy.context.scene.camera = cam
            path = PREVIEW.parent / name
            bpy.context.scene.render.filepath = str(path)
            bpy.ops.render.render(write_still=True)
            print("PREVIEW", path)

        arm = next((o for o in bpy.data.objects if o.type == "ARMATURE"), None)
        if arm:
            print("BONES", len(arm.data.bones))
            for b in arm.data.bones:
                if any(k in b.name.lower() for k in ("head", "neck", "jaw", "eye", "face", "horn")):
                    h = arm.matrix_world @ b.head_local
                    t = arm.matrix_world @ b.tail_local
                    print(f"  BONE {b.name} head={tuple(round(x, 3) for x in h)} tail={tuple(round(x, 3) for x in t)}")

        tex_dir = PREVIEW.parent / "textures"
        tex_dir.mkdir(exist_ok=True)
        for im in bpy.data.images:
            if im.size[0] < 8:
                continue
            dest = tex_dir / f"{im.name}.png"
            im.filepath_raw = str(dest)
            im.file_format = "PNG"
            im.save()
            print("TEX", dest, tuple(im.size))

    print("DONE")


if __name__ == "__main__":
    main()
