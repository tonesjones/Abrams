"""Create the V3 donor VMDL and isolated Source 2 materials."""
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
from make_clean_vmdl import HEADER, render_mesh_block

CONTENT = PROJECT / 'tools/Reduced_CSDK_12/content/citadel_addons/sulley_head_donor'
MODEL = CONTENT / 'models/heroes_wip/abrams'
MATERIALS = MODEL / 'materials'
MATERIALS.mkdir(parents=True, exist_ok=True)

# The accepted body material stays exactly as V2.  V3's face uses only the
# downloaded donor's embedded color texture; no procedural detail textures.
assets = [('body', PROJECT / 'model_work/import_head/textures/Image_0.png', PROJECT / 'model_work/import_head/textures/Image_1.png'),
          ('face', HERE / 'sulley_head_donor_color.png', None)]
for kind, color, normal in assets:
    name = f'sulley_head_donor_{kind}'
    shutil.copyfile(color, MATERIALS / f'{name}.png')
    normal_ref = '[0.5 0.5 1.0 0.0]'
    if normal:
        shutil.copyfile(normal, MATERIALS / f'{name}_normal.png')
        normal_ref = f'models/heroes_wip/abrams/materials/{name}_normal.png'
    (MATERIALS / f'{name}.vmat').write_text(f'''"Layer0"
{{
    "shader" "pbr.vfx"
    "F_USE_NPR_LIGHTING" "1"
    "F_USE_STATUS_EFFECTS_PROXY" "1"
    "F_WRITE_DEPTH_BEFORE_ALPHA_BLENDING" "1"
    "TextureColor1" "models/heroes_wip/abrams/materials/{name}.png"
    "TextureNormal1" "{normal_ref}"
    "TextureRoughness1" "[0.82 0.82 0.82 0.0]"
    "TextureMetalness1" "[0.0 0.0 0.0 0.0]"
    "TextureAmbientOcclusion1" "[1.0 1.0 1.0 0.0]"
}}
''')
text = HEADER + '{\n\trootNode =\n\t{\n\t\t_class = "RootNode"\n\t\tchildren =\n\t\t[\n'
text += render_mesh_block([('body', 'models/heroes_wip/abrams/sulley_body.fbx'),
                           ('face', 'models/heroes_wip/abrams/sulley_face.fbx')])
text += '\n\t\t]\n\t}\n}\n'
(MODEL / 'sulley_donor.vmdl').write_text(text)
print(MODEL / 'sulley_donor.vmdl')
