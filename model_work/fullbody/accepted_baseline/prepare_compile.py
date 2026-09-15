"""Create an isolated mesh-only donor and its two materials."""
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
from make_clean_vmdl import HEADER, render_mesh_block

CONTENT = PROJECT / 'tools/Reduced_CSDK_12/content/citadel_addons/sulley_fullbody'
MODEL = CONTENT / 'models/heroes_wip/abrams'
MATERIALS = MODEL / 'materials'
MATERIALS.mkdir(parents=True, exist_ok=True)
for kind, image in [('body', 'Image_0.png'), ('eyes', 'Image_2.png')]:
    name = 'sulley_fullbody_' + kind
    shutil.copyfile(HERE.parent / 'import_head/textures' / image, MATERIALS / (name + '.png'))
    material = f'''"Layer0"
{{
    "shader" "pbr.vfx"
    "F_USE_NPR_LIGHTING" "1"
    "F_USE_STATUS_EFFECTS_PROXY" "1"
    "F_WRITE_DEPTH_BEFORE_ALPHA_BLENDING" "1"
    "TextureColor1" "models/heroes_wip/abrams/materials/{name}.png"
    "TextureNormal1" "[0.5 0.5 1.0 0.0]"
    "TextureRoughness1" "[0.8 0.8 0.8 0.0]"
    "TextureMetalness1" "[0.0 0.0 0.0 0.0]"
    "TextureAmbientOcclusion1" "[1.0 1.0 1.0 0.0]"
}}
'''
    (MATERIALS / (name + '.vmat')).write_text(material)
meshes = [('body', 'models/heroes_wip/abrams/sulley_body.fbx'),
          ('face', 'models/heroes_wip/abrams/sulley_face.fbx')]
text = HEADER + '{\n\trootNode =\n\t{\n\t\t_class = "RootNode"\n\t\tchildren =\n\t\t[\n'
text += render_mesh_block(meshes)
text += '\n\t\t]\n\t}\n}\n'
(MODEL / 'sulley_donor.vmdl').write_text(text)
print(MODEL / 'sulley_donor.vmdl')
