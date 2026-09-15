import bpy, sys, json
from pathlib import Path

path = Path(sys.argv[-1])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(path))
out=[]
for o in bpy.context.scene.objects:
    if o.type == 'MESH':
        out.append({'name':o.name,'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'materials':[m.name if m else None for m in o.data.materials],'bounds_min':list(min((o.matrix_world@v.co for v in o.data.vertices),key=lambda x:x.x)) if False else None})
    elif o.type == 'ARMATURE':
        out.append({'name':o.name,'type':'ARMATURE','bones':len(o.data.bones),'actions':[a.name for a in bpy.data.actions]})
    else: out.append({'name':o.name,'type':o.type})
print(json.dumps({'objects':out,'images':[{'name':i.name,'size':[i.size[0],i.size[1]],'packed':bool(i.packed_file)} for i in bpy.data.images],'materials':[m.name for m in bpy.data.materials],'actions':[a.name for a in bpy.data.actions]},indent=2))
