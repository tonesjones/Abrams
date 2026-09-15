"""Verify the donor's bind pose, splice into stock, and pack one test VPK."""
import hashlib
import json
import struct
import subprocess
import sys
from pathlib import Path
import math

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
sys.path.insert(0, str(PROJECT / 'tools/SpliceHost'))
from splice import splice, kv_of, norm_bone, BODY_HOST_NAMES, FACE_HOST_NAMES
from resource_io import Block, read_resource, write_resource

HOST = HERE / 'stock/models/heroes_wip/abrams/abrams.vmdl_c'
GAME = PROJECT / 'tools/Reduced_CSDK_12/game/citadel_addons/sulley_fullbody'
DONOR = GAME / 'models/heroes_wip/abrams/sulley_donor.vmdl_c'
OUT = HERE / 'abrams_fullbody.vmdl_c'


def global_matrices(skeleton):
    result = []
    for i, (p, q, scale) in enumerate(zip(skeleton['m_bonePosParent'], skeleton['m_boneRotParent'], skeleton['m_boneScaleParent'])):
        x, y, z, w = q
        rotation = [[1-2*y*y-2*z*z, 2*x*y-2*z*w, 2*x*z+2*y*w],
                             [2*x*y+2*z*w, 1-2*x*x-2*z*z, 2*y*z-2*x*w],
                             [2*x*z-2*y*w, 2*y*z+2*x*w, 1-2*x*x-2*y*y]]
        matrix = [[rotation[r][c] * scale for c in range(3)] + [float(p[r])] for r in range(3)]
        matrix.append([0, 0, 0, 1])
        parent = int(skeleton['m_nParent'][i])
        if parent >= 0:
            matrix = [[sum(result[parent][r][k] * matrix[k][c] for k in range(4)) for c in range(4)] for r in range(4)]
        result.append(matrix)
    return dict(zip(skeleton['m_boneName'], result))


_, _, hb = read_resource(HOST)
_, _, db = read_resource(DONOR)
hd = kv_of(hb, b'DATA').value
dd = kv_of(db, b'DATA').value
hm = {norm_bone(n): m for n, m in global_matrices(hd['m_modelSkeleton']).items()}
dm = global_matrices(dd['m_modelSkeleton'])
errors = {}
for name, matrix in dm.items():
    if norm_bone(name) not in hm: raise ValueError(f'Unknown donor bone {name}')
    other = hm[norm_bone(name)]
    errors[name] = {'position_inches': math.dist([row[3] for row in matrix[:3]], [row[3] for row in other[:3]]),
                    'basis_max_error': max(abs(matrix[r][c] - other[r][c]) for r in range(3) for c in range(3))}
(HERE / 'bind_verification.json').write_text(json.dumps(errors, indent=2))
worst_position = max(e['position_inches'] for e in errors.values())
worst_basis = max(e['basis_max_error'] for e in errors.values())
print('Bind comparison: position inches', worst_position, 'basis error', worst_basis)
# Allow small export/compile roundoff (3.2 mm, <0.005 basis component),
# while rejecting unit, axis, parent-transform and bone-origin errors.
if worst_position > .125 or worst_basis > .005:
    raise ValueError('Donor bind pose differs from stock; do not package.')

# The existing splice assumes these remap indices. Validate before reusing it.
hc = kv_of(hb, b'CTRL').value
dc = kv_of(db, b'CTRL').value
assert [m['m_Name'] for m in dc['embedded_meshes']] == ['body', 'face']
for i in [0, 5, 9, 13]: assert hc['embedded_meshes'][i]['m_Name'] in BODY_HOST_NAMES
for i in [1, 4, 8, 12]: assert hc['embedded_meshes'][i]['m_Name'] in FACE_HOST_NAMES
splice(HOST, DONOR, OUT)
_, version, output_blocks = read_resource(OUT)


def references(blocks):
    raw = next(b.data for b in blocks if b.typ == b'RERL')
    offset, count = struct.unpack_from('<II', raw)
    result = []
    for i in range(count):
        pos = offset + i * 16
        resource_id, relative = struct.unpack_from('<Qq', raw, pos)
        start = pos + 8 + relative
        name = raw[start:raw.index(b'\0', start)].decode()
        result.append((resource_id, name))
    return result


# Preserve every stock resource ID and append only the new material references.
refs = references(hb)
for entry in references(db):
    if entry not in refs: refs.append(entry)
raw = bytearray(struct.pack('<II', 8, len(refs)) + bytes(16 * len(refs)))
for i, (resource_id, name) in enumerate(refs):
    pos = 8 + i * 16
    struct.pack_into('<Qq', raw, pos, resource_id, len(raw) - (pos + 8))
    raw.extend(name.encode() + b'\0')
for i, block in enumerate(output_blocks):
    if block.typ == b'RERL': output_blocks[i] = Block(b'RERL', bytes(raw))
write_resource(OUT, version, output_blocks)
_, _, checked = read_resource(OUT)
changed = []
for i, original in enumerate(hb):
    if original.data != checked[i].data:
        changed.append(original.typ.decode())
        assert original.typ in (b'CTRL', b'DATA', b'RERL'), original.typ
result_data = kv_of(checked, b'DATA').value
for key in hd:
    if key not in ('m_remappingTable', 'm_remappingTableStarts'):
        # KV3 objects carry flags; compare their serialized form.
        from resource_io import kv3_write_block
        assert kv3_write_block({key: hd[key]}) == kv3_write_block({key: result_data[key]}), key

release = PROJECT / 'release/fullbody'
release.mkdir(exist_ok=True)
vpk = release / 'pak69_sulley_fullbody_regenerated_dir.vpk'
empty = HERE / 'no_texture_overrides'
empty.mkdir(exist_ok=True)
command = [str(PROJECT / 'tools/VtexPacker/bin/Release/net8.0/VtexPacker.exe'), str(empty), str(vpk),
           'models/heroes_wip/abrams/abrams.vmdl_c', str(OUT)]
files = {'models/heroes_wip/abrams/abrams.vmdl_c': OUT}
portrait_root = HERE / 'portraits_compiled'
portrait_names = ['bull_card_psd', 'bull_card_gloat_psd', 'bull_card_critical_psd', 'bull_sm_psd', 'bull_vertical_psd']
for name in portrait_names:
    game_path = f'panorama/images/heroes/{name}.vtex_c'
    path = portrait_root / game_path
    if not path.is_file(): raise FileNotFoundError(f'Missing approved Sully portrait: {path}')
    command += [game_path, str(path)]
    files[game_path] = path
for path in sorted(GAME.rglob('*')):
    if path.suffix in ('.vmat_c', '.vtex_c'):
        game_path = path.relative_to(GAME).as_posix()
        # These default masks were verified in the installed citadel VPK.
        # Avoid overriding shared resources used by other heroes and mods.
        if game_path.startswith('materials/default/'): continue
        command += [game_path, str(path)]
        files[game_path] = path
subprocess.run(command, check=True, capture_output=True, text=True)
verification = subprocess.run([str(PROJECT / 'tools/s2v-cli/Source2Viewer-CLI.exe'), '-i', str(vpk), '--vpk_verify'],
                              check=True, capture_output=True, text=True)
(HERE / 'vpk_verify.log').write_text(verification.stdout + verification.stderr)
manifest = {'status': 'OFFLINE_CHECKED_IN_GAME_TEST_PENDING',
            'revision': 'fullbody_regenerated_with_restored_portraits',
            'baseline_user_feedback': 'Animations and crosshair placement confirmed working before the face revision.',
            'stock_sha256': hashlib.sha256(HOST.read_bytes()).hexdigest(),
            'vpk_sha256': hashlib.sha256(vpk.read_bytes()).hexdigest(),
            'bind_max_error_inches': worst_position, 'bind_max_basis_error': worst_basis,
            'modified_original_blocks': changed,
            'camera_and_attachments': 'Unchanged from stock DATA',
            'files': {n: hashlib.sha256(p.read_bytes()).hexdigest() for n, p in files.items()}}
(release / 'manifest.json').write_text(json.dumps(manifest, indent=2))
print('PACKAGED', vpk)
