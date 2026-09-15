"""Render stock animation samples and record deformation bounds (offline only)."""
from pathlib import Path
import json
import sys
import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(HERE / 'sulley_head_donor.blend'))
compiled = '--compiled' in sys.argv
if compiled:
    # Keep the source materials/lights but test the actual exported game mesh.
    for obj in list(bpy.data.objects):
        if obj.type in ('MESH', 'ARMATURE'): bpy.data.objects.remove(obj, do_unlink=True)
    for action in list(bpy.data.actions): bpy.data.actions.remove(action)
    bpy.ops.import_scene.gltf(filepath=str(HERE / 'compiled.gltf'))
    new_arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    new_arm.name = 'Abrams_stock_rig'
    for obj in list(bpy.data.objects):
        if obj.type != 'MESH': continue
        if obj.name.startswith('Icosphere'):
            bpy.data.objects.remove(obj, do_unlink=True)
        elif len(obj.data.vertices) in (3546, 508):
            kind = 'face' if len(obj.data.vertices) == 508 else 'body'
            obj.name = kind
            obj.data.materials.clear()
            if kind == 'face':
                template = bpy.data.materials.get('models/heroes_wip/abrams/materials/sulley_head_donor_face')
                if template:
                    obj.data.materials.append(template.copy())
                    continue
            material = bpy.data.materials.new('Compiled preview ' + kind)
            material.use_nodes = True
            shader = material.node_tree.nodes.get('Principled BSDF')
            texture = material.node_tree.nodes.new('ShaderNodeTexImage')
            texture.image = bpy.data.images.load(str(HERE / ('sulley_head_donor_color.png' if kind == 'face' else '../import_head/textures/Image_0.png')), check_existing=False)
            material.node_tree.links.new(texture.outputs['Color'], shader.inputs['Base Color'])
            shader.inputs['Roughness'].default_value = .8
            if kind == 'body':
                normal_image = material.node_tree.nodes.new('ShaderNodeTexImage')
                normal_image.image = bpy.data.images.load(str(HERE.parent / 'import_head/textures/Image_1.png'), check_existing=False)
                normal_image.image.colorspace_settings.name = 'Non-Color'
                normal = material.node_tree.nodes.new('ShaderNodeNormalMap')
                material.node_tree.links.new(normal_image.outputs['Color'], normal.inputs['Color'])
                material.node_tree.links.new(normal.outputs['Normal'], shader.inputs['Normal'])
            obj.data.materials.append(material)
        else:
            # Preserve gun/book geometry as context; preview uses neutral material.
            obj.hide_render = False
arm = bpy.data.objects['Abrams_stock_rig']
scene = bpy.context.scene
scene.render.resolution_x = 640
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
out = HERE / ('compiled_previews' if compiled else 'animation_previews')
out.mkdir(exist_ok=True)
bpy.ops.object.camera_add(location=(3.7, -7, 3.3))
cam = bpy.context.object
cam.rotation_euler = (Vector((0, 0, 1.45)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.type = 'ORTHO'
cam.data.ortho_scale = 3.8
scene.camera = cam
arm.animation_data_create()
report = []
for name in ['primary_stand_idle', 'primary_run_n', 'primary_stand_aim', 'melee_quick_1', 'slide_forward', 'ability_charge', 'ability_leap_smash']:
    action = bpy.data.actions.get(name)
    if not action: raise ValueError(f'Missing stock clip {name}')
    arm.animation_data.action = action
    if action.slots: arm.animation_data.action_slot = action.slots[0]
    start, end = action.frame_range
    samples = []
    for fraction in (0, .25, .5, .75, 1):
        frame = round(start + (end - start) * fraction)
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        obj = bpy.data.objects['body'].evaluated_get(bpy.context.evaluated_depsgraph_get())
        points = [obj.matrix_world @ v.co for v in obj.data.vertices]
        samples.append({'frame': frame, 'min': [min(p[i] for p in points) for i in range(3)],
                        'max': [max(p[i] for p in points) for i in range(3)]})
        if not compiled:
            stock = max((o for o in bpy.data.objects if o.type == 'MESH'), key=lambda o: len(o.data.vertices))
            stock_ev = stock.evaluated_get(bpy.context.evaluated_depsgraph_get())
            stock_points = [stock_ev.matrix_world @ v.co for v in stock_ev.data.vertices]
            samples[-1]['stock_min'] = [min(p[i] for p in stock_points) for i in range(3)]
            samples[-1]['stock_max'] = [max(p[i] for p in stock_points) for i in range(3)]
        if fraction == .5:
            scene.render.filepath = str(out / (name + '.png'))
            bpy.ops.render.render(write_still=True)
    report.append({'clip': name, 'samples': samples})
(HERE / ('compiled_animation_report.json' if compiled else 'animation_report.json')).write_text(json.dumps(report, indent=2))
print('Rendered seven stock clips; in-game validation is still required.')
