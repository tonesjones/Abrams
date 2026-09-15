from pathlib import Path
import bpy
from mathutils import Vector
HERE=Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=str(HERE/'sulley_donor_source.glb'))
src=next(o for o in bpy.context.scene.objects if o.type=='MESH' and len(o.data.vertices)>1000); dg=bpy.context.evaluated_depsgraph_get(); ev=src.evaluated_get(dg)
me=bpy.data.meshes.new_from_object(ev,preserve_all_data_layers=True,depsgraph=dg); o=bpy.data.objects.new('head',me);bpy.context.collection.objects.link(o);o.matrix_world=ev.matrix_world.copy();o.data.materials.append(src.data.materials[0])
ns={g.index:g.name for g in src.vertex_groups};[o.vertex_groups.new(name=g.name) for g in src.vertex_groups]
for v in src.data.vertices:
 for g in v.groups:o.vertex_groups[g.group].add([v.index],g.weight,'REPLACE')
def keep(v):return sum(g.weight for g in v.groups if any(k in ns[g.group] for k in ('Head','Eye','Eyelid','Brow','Lip','Jaw','Teeth','Neck')))>=.5
bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT');bpy.ops.object.mode_set(mode='OBJECT');[setattr(v,'select',not keep(v)) for v in o.data.vertices];bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.delete(type='VERT');bpy.ops.object.mode_set(mode='OBJECT')
for x in list(bpy.context.scene.objects):
 if x!=o:bpy.data.objects.remove(x,do_unlink=True)
ps=[o.matrix_world@v.co for v in o.data.vertices];c=sum(ps,Vector())/len(ps); ext=max(max(p[i] for p in ps)-min(p[i] for p in ps) for i in range(3));sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE_NEXT';sc.render.resolution_x=900;sc.render.resolution_y=900;sc.render.image_settings.file_format='PNG'
for loc,power in [(c+Vector((ext,-ext*2,ext)),900),(c+Vector((-ext,-ext,ext*.3)),500)]:
 bpy.ops.object.light_add(type='AREA',location=loc);lamp=bpy.context.object;lamp.rotation_euler=(c-loc).to_track_quat('-Z','Y').to_euler();lamp.data.energy=power;lamp.data.size=ext
bpy.ops.object.camera_add(location=c+Vector((0,-ext*4,0)));cam=bpy.context.object;cam.rotation_euler=(c-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=ext*1.2;sc.camera=cam;sc.render.filepath=str(HERE/'donor_evaluated_head.png');bpy.ops.render.render(write_still=True)
