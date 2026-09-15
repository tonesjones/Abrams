"""Short, tapered, skinned fur geometry on the face only; no particle runtime."""
import math
import random
import bmesh
import bpy
import numpy as np
from pathlib import Path
from mathutils import Vector


def add_face_fur(obj):
    mesh = obj.data
    mesh.calc_loop_triangles()
    uv = mesh.uv_layers.active.data
    head_index = obj.vertex_groups['head'].index
    rng = random.Random(19683)
    image = bpy.data.images.load(str(Path(__file__).resolve().parent.parent / 'import_head/textures/Image_0.png'), check_existing=True)
    pixels = np.empty(len(image.pixels), dtype=np.float32)
    image.pixels.foreach_get(pixels)
    width, height = image.size
    strands = []
    for tri in mesh.loop_triangles:
        verts = [mesh.vertices[i] for i in tri.vertices]
        head_weights = [sum(g.weight for g in v.groups if g.group == head_index) for v in verts]
        if min(head_weights) < .95: continue
        center = sum((v.co for v in verts), Vector()) / 3
        x, y, z = center
        # Keep eyes, brows, nose, lips, teeth and horns clean. Source mesh is
        # forward-facing along -Y; the rear head silhouette gets short fur too.
        fur_zone = (z < 2.60 or abs(x) > .155 or (z > 2.88 and abs(x) < .17))
        if not fur_zone or z < 2.46 or z > 2.925: continue
        edges = [verts[1].co - verts[0].co, verts[2].co - verts[0].co]
        area = edges[0].cross(edges[1]).length * .5
        amount = area * 22000
        count = int(amount) + (rng.random() < amount % 1)
        for _ in range(count):
            a = math.sqrt(rng.random())
            bary = (1-a, a*(1-rng.random()), 0)
            bary = (bary[0], bary[1], 1-bary[0]-bary[1])
            root = sum((v.co * w for v, w in zip(verts, bary)), Vector())
            normal = sum((v.normal * w for v, w in zip(verts, bary)), Vector()).normalized()
            if normal.length < .9: continue
            tex = sum((uv[loop].uv * w for loop, w in zip(tri.loops, bary)), Vector((0, 0)))
            tx, ty = int((tex.x % 1) * (width-1)), int((tex.y % 1) * (height-1))
            r, g, b = pixels[(ty * width + tx) * 4:(ty * width + tx) * 4 + 3]
            if g < .08 or r > g * .85: continue  # Horns, teeth and mouth are not fur.
            # Fur combs downward while emerging from the surface.
            direction = (normal * .8 + Vector((rng.uniform(-.1, .1), 0, -.45))).normalized()
            length = rng.uniform(.003, .009)
            strands.append((root, normal, direction, length, tex, tri.material_index))
    bm = bmesh.new()
    bm.from_mesh(mesh)
    deform = bm.verts.layers.deform.verify()
    uv_layer = bm.loops.layers.uv.active
    for root, normal, direction, length, tex, material in strands:
        side = normal.cross(Vector((0, 0, 1)))
        if side.length < .1: side = normal.cross(Vector((0, 1, 0)))
        side.normalize()
        second = normal.cross(side).normalized()
        width = length * .08
        positions = [root + side * width, root - side * width,
                     root + second * width, root + direction * length]
        vs = [bm.verts.new(p) for p in positions]
        for v in vs: v[deform][head_index] = 1.0
        for indices in [(0, 1, 3), (1, 2, 3), (2, 0, 3)]:
            face = bm.faces.new([vs[i] for i in indices])
            face.material_index = material
            face.smooth = True
            for loop, offset in zip(face.loops, [(0, 0), (.0001, 0), (0, .0001)]):
                loop[uv_layer].uv = tex + Vector(offset)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    print('Added face-only skinned fur strands:', len(strands))
