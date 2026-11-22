# Ragdoll Lab models. Run with:
#   blender --background --factory-startup --python build_models.py -- <out.glb> [preview.png]
# Everything is written in the game's own coordinates (three.js: Y up, -Z forward, metres,
# origin at the hand for weapons) and converted to Blender's Z-up at the end of each part.
import bpy, bmesh, math, sys
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = argv[0] if argv else 'ragdoll-lab.glb'
PREVIEW = argv[1] if len(argv) > 1 else None

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
COLL = scene.collection
C = Matrix.Rotation(math.radians(90), 4, 'X')  # three.js (x, y, z) -> Blender (x, -z, y)
PI = math.pi
CUR = None  # parent empty of the model being built

# ---------------------------------------------------------------- materials
def lin(h):
    c = [((h >> 16) & 255) / 255, ((h >> 8) & 255) / 255, (h & 255) / 255]
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c)

def mat(name, hexc, metal=0.0, rough=0.6, emit=None, estr=1.0):
    m = bpy.data.materials.new(name)
    try: m.use_nodes = True
    except Exception: pass
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    col = lin(hexc)
    bsdf.inputs['Base Color'].default_value = (*col, 1)
    bsdf.inputs['Metallic'].default_value = metal
    bsdf.inputs['Roughness'].default_value = rough
    if emit is not None:
        bsdf.inputs['Emission Color'].default_value = (*lin(emit), 1)
        bsdf.inputs['Emission Strength'].default_value = estr
    m.diffuse_color = (*lin(emit if emit is not None and estr > 1 else hexc), 1)
    m.metallic = metal; m.roughness = rough
    return m

GUN = mat('Gunmetal', 0x2b3038, 0.65, 0.38)
GUND = mat('GunmetalDark', 0x1a1d22, 0.55, 0.5)
STEELD = mat('SteelDark', 0x4a5058, 0.8, 0.35)
POLY = mat('Polymer', 0x23262b, 0.0, 0.75)
GRIPM = mat('Grip', 0x1d1f24, 0.0, 0.88)
WOOD = mat('Wood', 0x8a5a2b, 0.0, 0.58)
WOODD = mat('WoodDark', 0x5a3518, 0.0, 0.7)
BLACK = mat('Bore', 0x050505, 0.0, 0.95)
STEEL = mat('Steel', 0xdfe6ee, 0.95, 0.16)
CHROME = mat('Chrome', 0xcccccc, 0.95, 0.2)
GOLD = mat('Gold', 0xc9a227, 0.85, 0.3)
LEATHER = mat('Leather', 0x3a2414, 0.0, 0.85)
OLIVE = mat('Olive', 0x4f5d32, 0.15, 0.7)
OLIVE2 = mat('OliveLight', 0x5d6b3a, 0.1, 0.65)
REDP = mat('RedPaint', 0x8a2a1c, 0.35, 0.45)
NOSE = mat('NoseRed', 0xc0392b, 0.2, 0.45)
YELLOW = mat('Yellow', 0xe8b923, 0.1, 0.5)
BRASS = mat('Brass', 0xc9a227, 0.75, 0.32)
NAVY = mat('Navy', 0x2c3a52, 0.6, 0.35)
GLOW = mat('Glow', 0x99ccff, 0.0, 0.3, 0x3399ff, 3.0)
GLOWW = mat('GlowWhite', 0xffffff, 0.0, 0.2, 0x88ccff, 4.0)
ICE = mat('Ice', 0x8fe3ff, 0.0, 0.25, 0x2a8fbf, 1.5)
ICEB = mat('IceBright', 0xdff6ff, 0.0, 0.2, 0x8fe3ff, 4.0)
WHITE = mat('Shell', 0xe8eef5, 0.25, 0.3)
BAT = mat('BatWood', 0xc8975a, 0.0, 0.5)
STRING = mat('String', 0xdddddd, 0.0, 0.6)
LENS = mat('Lens', 0x1a3a5a, 0.9, 0.08)
ORANGE = mat('SightDot', 0xffb020, 0.0, 0.4, 0xff8a00, 2.0)
PILOT = mat('Pilot', 0x3399ff, 0.0, 0.3, 0x3399ff, 4.0)
LEDM = mat('LED', 0x330000, 0.0, 0.4)
GAUGE = mat('GaugeFace', 0xf2f2ea, 0.0, 0.5)
SPOON = mat('Spoon', 0x8a9099, 0.8, 0.35)
PAINT = mat('Paint', 0xc0392b, 0.4, 0.5)  # barrel/bomb body: the game swaps in its own colour

# ---------------------------------------------------------------- geometry helpers (three.js space)
def xf(pos=(0, 0, 0), rot=(0, 0, 0)):
    R = Matrix.Rotation(rot[0], 4, 'X') @ Matrix.Rotation(rot[1], 4, 'Y') @ Matrix.Rotation(rot[2], 4, 'Z')
    return C @ Matrix.Translation(pos) @ R

def finish(bm, name, m, pos=(0, 0, 0), rot=(0, 0, 0), smooth=35, bevel=0.0, segs=2):
    bmesh.ops.transform(bm, matrix=xf(pos, rot), verts=bm.verts)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-7, edges=bm.edges)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); COLL.objects.link(ob); ob.parent = CUR
    me.materials.append(m)
    if smooth is not None:
        for p in me.polygons: p.use_smooth = True
        me.set_sharp_from_angle(angle=math.radians(smooth))
    if bevel:
        b = ob.modifiers.new('Bevel', 'BEVEL'); b.width = bevel; b.segments = segs
        b.limit_method = 'ANGLE'; b.angle_limit = math.radians(30); b.harden_normals = True
    return ob

def box(sx, sy, sz):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts); return bm

def cyl(r1, r2, length, segs=16):  # along Z; r1 at -Z, r2 at +Z
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs, radius1=r1, radius2=r2, depth=length)
    return bm

def sphere(r, u=24, v=16):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=r); return bm

def torus(R, r, n=32, m=10, arc=2 * PI):  # ring in the XY plane
    bm = bmesh.new(); closed = arc >= 2 * PI - 1e-6; N = n if closed else n + 1; rings = []
    for i in range(N):
        a = arc * i / n; ring = []
        for j in range(m):
            b = 2 * PI * j / m; d = R + r * math.cos(b)
            ring.append(bm.verts.new((d * math.cos(a), d * math.sin(a), r * math.sin(b))))
        rings.append(ring)
    for i in range(N if closed else N - 1):
        A, B = rings[i], rings[(i + 1) % N]
        for j in range(m): bm.faces.new((A[j], A[(j + 1) % m], B[(j + 1) % m], B[j]))
    if not closed: bm.faces.new(rings[0]); bm.faces.new(rings[-1])
    return bm

def lathe(prof, segs=24, closed=False):  # prof = [(radius, z)], spun around Z
    bm = bmesh.new(); rings = []
    for r, t in prof:
        rings.append([bm.verts.new((r * math.cos(2 * PI * k / segs), r * math.sin(2 * PI * k / segs), t)) for k in range(segs)])
    L = len(prof)
    for i in (range(L) if closed else range(L - 1)):
        A, B = rings[i], rings[(i + 1) % L]
        for k in range(segs):
            bm.faces.new((A[k], A[(k + 1) % segs], B[(k + 1) % segs], B[k]))
    return bm

def prism(pts, width, plane='zy'):
    """Extrude a 2D outline. 'zy': side view (a=z, b=y), thickness along x.
    'xy': front view (a=x, b=y), thickness along z. 'xz': top view (a=x, b=z), thickness along y."""
    def P(a, b, c):
        return (c, b, a) if plane == 'zy' else (a, b, c) if plane == 'xy' else (a, c, b)
    bm = bmesh.new()
    bot = [bm.verts.new(P(a, b, -width / 2)) for a, b in pts]
    top = [bm.verts.new(P(a, b, width / 2)) for a, b in pts]
    bm.faces.new(bot); bm.faces.new(top[::-1]); n = len(pts)
    for i in range(n): bm.faces.new((bot[i], bot[(i + 1) % n], top[(i + 1) % n], top[i]))
    return bm

def sweep(pts, rads, m=10, caps=True, up=(0, 1, 0)):
    """Tube along a path. rads[i] = r or (r_side, r_up)."""
    bm = bmesh.new(); pts = [Vector(p) for p in pts]; rings = []
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        u = Vector(up)
        if abs(t.dot(u)) > 0.95: u = Vector((1, 0, 0))
        n = (u - t * t.dot(u)).normalized(); b = t.cross(n)
        rx, ry = rads[i] if isinstance(rads[i], tuple) else (rads[i], rads[i])
        rings.append([bm.verts.new(p + n * (ry * math.cos(2 * PI * j / m)) + b * (rx * math.sin(2 * PI * j / m))) for j in range(m)])
    for i in range(len(rings) - 1):
        A, B = rings[i], rings[i + 1]
        for j in range(m): bm.faces.new((A[j], A[(j + 1) % m], B[(j + 1) % m], B[j]))
    if caps: bm.faces.new(rings[0]); bm.faces.new(rings[-1][::-1])
    return bm

def rod(name, m, a, b, r, segs=8):
    return finish(sweep([a, b], [r, r], m=segs), name, m)

def model(name):
    global CUR
    CUR = bpy.data.objects.new(name, None); COLL.objects.link(CUR)
    return CUR

# shared bits
def pistol_grip(n, z0, y0, m=GRIPM, w=0.034, rake=1.0):
    pts = [(-0.018, 0.0), (0.03, 0.0), (0.03 + 0.02 * rake, -0.1), (0.024 + 0.02 * rake, -0.108), (-0.016 + 0.02 * rake, -0.108), (-0.019 + 0.018 * rake, -0.1)]
    finish(prism([(z0 + a, y0 + b) for a, b in pts], w), n + '_Grip', m, bevel=0.004)
    # textured side panels, slightly proud of the grip
    panel = [(-0.012, -0.012), (0.024, -0.012), (0.024 + 0.017 * rake, -0.092), (-0.013 + 0.016 * rake, -0.092)]
    finish(prism([(z0 + a, y0 + b) for a, b in panel], w + 0.003), n + '_GripPanel', GUND, bevel=0.002)

def trigger(n, z, y, m=GUN):
    finish(torus(0.017, 0.0028, 28, 8), n + '_Guard', m, (0, y - 0.004, z), (0, PI / 2, 0))
    finish(box(0.006, 0.02, 0.005), n + '_Trigger', GUN, (0, y - 0.006, z + 0.002), (0.35, 0, 0), bevel=0.0015)

# ---------------------------------------------------------------- weapons
def pistol():
    n = 'Pistol'; model('W_' + n)
    finish(prism([(0.04, 0.012), (0.04, 0.05), (0.032, 0.057), (-0.152, 0.057), (-0.176, 0.05), (-0.178, 0.012)], 0.034), n + '_Slide', GUN, bevel=0.002)
    for i in range(6):
        finish(box(0.0355, 0.03, 0.0025), f'{n}_Serration{i}', GUND, (0, 0.037, 0.008 + i * 0.005), smooth=None)
    finish(box(0.004, 0.013, 0.036), n + '_Port', BLACK, (0.016, 0.047, -0.04), smooth=None)
    finish(prism([(0.03, 0.013), (0.03, -0.006), (-0.02, -0.012), (-0.162, -0.006), (-0.166, 0.013)], 0.03), n + '_Frame', POLY, bevel=0.002)
    for i in range(3):
        finish(box(0.031, 0.003, 0.008), f'{n}_Rail{i}', GUND, (0, -0.008, -0.1 - i * 0.017), smooth=None)
    pistol_grip(n, 0.0, 0.002, POLY, 0.033, 1.1)
    finish(box(0.035, 0.009, 0.05), n + '_MagBase', GUN, (0, -0.108, 0.023), (0.22, 0, 0), bevel=0.002)
    trigger(n, -0.03, -0.006, POLY)
    finish(cyl(0.0085, 0.0085, 0.006, 16), n + '_Muzzle', GUN, (0, 0.03, -0.179))
    finish(cyl(0.0055, 0.0055, 0.008, 12), n + '_Bore', BLACK, (0, 0.03, -0.18))
    finish(box(0.006, 0.007, 0.008), n + '_FrontSight', GUN, (0, 0.06, -0.163), bevel=0.001)
    finish(sphere(0.0022, 8, 6), n + '_Dot', ORANGE, (0, 0.0615, -0.158))
    for x in (-0.007, 0.007):
        finish(box(0.006, 0.008, 0.006), f'{n}_RearSight{x}', GUN, (x, 0.06, 0.03), bevel=0.001)
    finish(box(0.009, 0.016, 0.008), n + '_Hammer', GUN, (0, 0.05, 0.044), (-0.45, 0, 0), bevel=0.0015)

def shotgun():
    n = 'Shotgun'; model('W_' + n)
    finish(prism([(0.06, 0.026), (0.12, 0.02), (0.32, 0.002), (0.33, -0.103), (0.24, -0.086), (0.14, -0.062), (0.09, -0.062), (0.06, -0.032)], 0.043), n + '_Stock', WOOD, bevel=0.007, segs=3)
    finish(box(0.046, 0.112, 0.016), n + '_ButtPad', GRIPM, (0, -0.051, 0.333), (0.09, 0, 0), bevel=0.004)
    finish(prism([(0.065, 0.045), (-0.16, 0.045), (-0.16, -0.03), (0.0, -0.03), (0.065, -0.012)], 0.05), n + '_Receiver', GUN, bevel=0.003)
    finish(box(0.003, 0.022, 0.06), n + '_Port', BLACK, (0.0255, 0.015, -0.06), smooth=None)
    finish(cyl(0.019, 0.019, 0.475, 20), n + '_Barrel', GUN, (0, 0.025, -0.3975))
    finish(cyl(0.013, 0.013, 0.01, 16), n + '_Bore', BLACK, (0, 0.025, -0.632))
    finish(sphere(0.0045, 10, 8), n + '_Bead', BRASS, (0, 0.046, -0.618))
    finish(cyl(0.015, 0.015, 0.425, 16), n + '_MagTube', GUN, (0, -0.013, -0.3725))
    finish(cyl(0.0165, 0.0165, 0.016, 16), n + '_MagCap', GUND, (0, -0.013, -0.585))
    finish(box(0.06, 0.052, 0.17), n + '_Pump', WOOD, (0, -0.013, -0.33), bevel=0.012, segs=3)
    for i in range(5):
        finish(box(0.0615, 0.0535, 0.0045), f'{n}_PumpGroove{i}', WOODD, (0, -0.013, -0.27 - i * 0.03), bevel=0.005)
    trigger(n, 0.012, -0.03)

def smg():
    n = 'SMG'; model('W_' + n)
    finish(prism([(0.07, 0.05), (-0.25, 0.05), (-0.25, -0.01), (-0.18, -0.03), (0.07, -0.03)], 0.05), n + '_Receiver', GUN, bevel=0.003)
    finish(box(0.024, 0.008, 0.22), n + '_RailBase', GUND, (0, 0.054, -0.1), smooth=None)
    for i in range(10):
        finish(box(0.03, 0.005, 0.007), f'{n}_Rail{i}', GUND, (0, 0.059, 0.0 - i * 0.022), smooth=None)
    finish(cyl(0.017, 0.017, 0.1, 18), n + '_Shroud', GUN, (0, 0.012, -0.3))
    for i in range(3):
        finish(box(0.036, 0.007, 0.016), f'{n}_Slot{i}', BLACK, (0, 0.012, -0.27 - i * 0.025), smooth=None)
    finish(cyl(0.008, 0.008, 0.006, 12), n + '_Bore', BLACK, (0, 0.012, -0.35))
    finish(box(0.03, 0.15, 0.04), n + '_Mag', GUND, (0, -0.1, -0.12), (-0.12, 0, 0), bevel=0.003)
    finish(box(0.034, 0.012, 0.046), n + '_MagBase', GUN, (0, -0.1745, -0.111), (-0.12, 0, 0), bevel=0.002)
    pistol_grip(n, 0.02, -0.03, GRIPM, 0.034, 1.0)
    trigger(n, -0.025, -0.034)
    for y in (0.03, -0.018):
        finish(cyl(0.006, 0.006, 0.18, 10), f'{n}_StockRod{y}', GUN, (0, y, 0.16))
    finish(box(0.042, 0.09, 0.016), n + '_ButtPlate', GRIPM, (0, 0.006, 0.255), bevel=0.005)
    finish(box(0.005, 0.016, 0.006), n + '_FrontSight', GUN, (0, 0.064, -0.235), bevel=0.001)
    for x in (-0.007, 0.007):
        finish(box(0.006, 0.012, 0.008), f'{n}_RearSight{x}', GUN, (x, 0.062, 0.05), bevel=0.001)
    finish(cyl(0.005, 0.005, 0.022, 10), n + '_Charging', CHROME, (0.034, 0.035, -0.15), (0, PI / 2, 0))

def rocket_launcher():
    n = 'Rocket Launcher'; model('W_' + n); Y = 0.07
    finish(lathe([(0.068, -0.62), (0.068, 0.32)], 28), n + '_Tube', OLIVE, (0, Y, 0))
    finish(lathe([(0.058, 0.33), (0.058, -0.63)], 28), n + '_TubeInner', BLACK, (0, Y, 0))
    finish(lathe([(0.062, -0.6), (0.08, -0.6), (0.089, -0.68), (0.079, -0.68), (0.06, -0.625)], 28, closed=True), n + '_Bell', GUN, (0, Y, 0))
    finish(lathe([(0.062, 0.3), (0.08, 0.3), (0.085, 0.36), (0.075, 0.36), (0.06, 0.33)], 28, closed=True), n + '_RearRing', GUN, (0, Y, 0))
    finish(cyl(0.06, 0.06, 0.003, 24), n + '_FrontDark', BLACK, (0, Y, -0.6))
    finish(cyl(0.06, 0.06, 0.003, 24), n + '_RearDark', BLACK, (0, Y, 0.3))
    for z in (-0.5, 0.22):
        finish(cyl(0.0695, 0.0695, 0.028, 28), f'{n}_Band{z}', YELLOW, (0, Y, z))
    finish(box(0.03, 0.022, 0.13), n + '_GripMount', GUN, (0, 0.0, -0.02), bevel=0.003)
    pistol_grip(n, 0.0, -0.005, GRIPM, 0.034, 1.0)
    trigger(n, -0.04, -0.008)
    finish(box(0.036, 0.1, 0.044), n + '_FrontGrip', GRIPM, (0, -0.04, -0.3), bevel=0.009, segs=3)
    finish(box(0.03, 0.02, 0.05), n + '_FrontMount', GUN, (0, 0.0, -0.3), bevel=0.003)
    finish(box(0.032, 0.05, 0.09), n + '_Sight', GUN, (-0.082, 0.13, -0.2), bevel=0.005)
    finish(box(0.04, 0.016, 0.04), n + '_SightArm', GUN, (-0.058, 0.115, -0.2), bevel=0.003)
    finish(cyl(0.013, 0.013, 0.006, 16), n + '_Lens', LENS, (-0.082, 0.138, -0.247))
    finish(cyl(0.013, 0.013, 0.006, 16), n + '_LensBack', LENS, (-0.082, 0.138, -0.153))
    finish(box(0.05, 0.03, 0.16), n + '_ShoulderPad', GRIPM, (0, 0.0, 0.18), bevel=0.008)

def rocket():
    n = 'Rocket'; model('W_' + n)  # projectile: nose points +Z
    finish(cyl(0.045, 0.045, 0.4, 20), n + '_Body', OLIVE2)
    prof = [(0.045 * math.sqrt(max(0.0, 1 - t ** 1.7)), 0.2 + 0.16 * t) for t in [i / 10 for i in range(11)]]
    finish(lathe([(0, 0.2)] + prof, 20), n + '_Nose', NOSE)
    finish(cyl(0.0465, 0.0465, 0.018, 20), n + '_Band', YELLOW, (0, 0, 0.12))
    for k in range(4):
        finish(prism([(-0.21, 0.04), (-0.12, 0.04), (-0.185, 0.09), (-0.225, 0.09)], 0.006), f'{n}_Fin{k}', GUND, (0, 0, 0), (0, 0, k * PI / 2), bevel=0.0015)
    finish(lathe([(0.03, -0.2), (0.037, -0.24), (0.031, -0.24), (0.024, -0.205)], 20, closed=True), n + '_Nozzle', GUND)

def grenade():
    n = 'Grenade'; model('W_' + n)
    bm = sphere(0.055, 32, 24)
    for v in bm.verts:  # egg shape with pineapple grooves
        x, y, z = v.co
        y *= 1.2
        th = math.atan2(z, x)
        g = max(math.exp(-(math.sin(4 * th) / 0.18) ** 2), math.exp(-(math.sin(PI * y / 0.026) / 0.25) ** 2)) if abs(y) < 0.052 else 0
        k = 1 - 0.07 * g
        v.co = Vector((x * k, y * k, z * k))
    finish(bm, n + '_Body', mat('GrenadeBody', 0x4a5a2a, 0.1, 0.8), smooth=60)
    finish(cyl(0.02, 0.02, 0.028, 18), n + '_Fuse', GUN, (0, 0.074, 0), (-PI / 2, 0, 0), bevel=0.002)
    finish(cyl(0.014, 0.016, 0.012, 16), n + '_Neck', GUN, (0, 0.058, 0), (-PI / 2, 0, 0))
    finish(prism([(0.0, 0.086), (-0.032, 0.083), (-0.06, 0.03), (-0.059, -0.004), (-0.054, -0.004), (-0.055, 0.03), (-0.029, 0.079), (0.0, 0.081)], 0.013, 'xy'), n + '_Spoon', SPOON, smooth=None)
    finish(torus(0.016, 0.0028, 24, 8), n + '_PinRing', CHROME, (0.034, 0.08, 0))
    finish(cyl(0.0025, 0.0025, 0.03, 8), n + '_Pin', CHROME, (0.015, 0.077, 0), (0, PI / 2, 0))
    finish(sphere(0.009, 12, 8), 'LED', LEDM, (0, 0.02, 0.052))

def crossbow():
    n = 'Crossbow'; model('W_' + n)
    finish(prism([(0.13, 0.028), (0.136, -0.05), (0.09, -0.046), (0.078, -0.122), (0.04, -0.122), (0.024, -0.03), (-0.4, -0.03), (-0.42, 0.0), (-0.4, 0.028)], 0.05), n + '_Stock', WOOD, bevel=0.006, segs=3)
    finish(box(0.016, 0.006, 0.44), n + '_RailGroove', GUND, (0, 0.03, -0.19), smooth=None)
    finish(box(0.08, 0.062, 0.05), n + '_Riser', GUN, (0, 0.03, -0.42), bevel=0.006)
    arc = [(-0.942 + 1.884 * i / 24) for i in range(25)]
    pts = [(0.3 * math.sin(a), 0.03, -0.12 - 0.3 * math.cos(a)) for a in arc]
    rads = [(0.0075, 0.019 - 0.008 * abs(a) / 0.942) for a in arc]
    finish(sweep(pts, rads, m=12), n + '_Limbs', GUND)
    for sx in (-1, 1):
        tip = (sx * 0.243, 0.03, -0.296)
        finish(cyl(0.012, 0.012, 0.022, 14), f'{n}_Cam{sx}', GUN, tip, (-PI / 2, 0, 0))
        rod(f'{n}_String{sx}', STRING, tip, (0, 0.03, -0.05), 0.0018, 6)
    finish(torus(0.045, 0.006, 24, 8, PI), n + '_Stirrup', GUN, (0, -0.03, -0.445), (0, 0, PI))
    trigger(n, 0.004, -0.032)
    finish(cyl(0.014, 0.014, 0.13, 18), n + '_Scope', GUND, (0, 0.078, -0.12))
    for z in (-0.188, -0.052):
        finish(cyl(0.017, 0.017, 0.014, 18), f'{n}_ScopeBell{z}', GUN, (0, 0.078, z))
        finish(cyl(0.012, 0.012, 0.016, 14), f'{n}_ScopeLens{z}', LENS, (0, 0.078, z))
    for z in (-0.16, -0.08):
        finish(box(0.012, 0.03, 0.014), f'{n}_ScopeMount{z}', GUN, (0, 0.05, z), smooth=None)

def blade_mesh(z0, z1, ztip, hw0, hw1, t):
    bm = bmesh.new(); st = []
    for i in range(9):
        k = i / 8; z = z0 + (z1 - z0) * k; w = hw0 + (hw1 - hw0) * k
        st.append([bm.verts.new(v) for v in ((-w, 0, z), (0, t, z), (w, 0, z), (0, -t, z))])
    for i in range(8):
        A, B = st[i], st[i + 1]
        for j in range(4): bm.faces.new((A[j], A[(j + 1) % 4], B[(j + 1) % 4], B[j]))
    bm.faces.new(st[0])
    tip = bm.verts.new((0, 0, ztip)); L = st[-1]
    for j in range(4): bm.faces.new((L[j], L[(j + 1) % 4], tip))
    return bm

def sword():
    n = 'Sword'; model('W_' + n)
    finish(blade_mesh(-0.115, -0.92, -1.01, 0.025, 0.021, 0.0045), n + '_Blade', STEEL, smooth=25)
    finish(box(0.018, 0.0092, 0.62), n + '_Fuller', mat('Fuller', 0xb8c2cc, 0.95, 0.25), (0, 0, -0.45), smooth=None)
    xs = [-0.1 + 0.2 * i / 16 for i in range(17)]
    finish(sweep([(x, 0, -0.1 - 0.028 * (x / 0.1) ** 2) for x in xs], [(0.012, 0.011)] * 17, m=12), n + '_Guard', GOLD)
    for sx in (-1, 1):
        finish(sphere(0.016, 14, 10), f'{n}_GuardEnd{sx}', GOLD, (sx * 0.1, 0, -0.128))
    finish(box(0.04, 0.03, 0.04), n + '_GuardCentre', GOLD, (0, 0, -0.1), bevel=0.007, segs=3)
    prof = [(0.0, -0.08), (0.016, -0.08)] + [(0.0175 + 0.0018 * abs(math.sin(PI * i / 3)), -0.078 + 0.185 * i / 24) for i in range(25)] + [(0.016, 0.108), (0.0, 0.108)]
    finish(lathe(prof, 18), n + '_Grip', LEATHER)
    finish(sphere(0.025, 18, 12), n + '_Pommel', GOLD, (0, 0, 0.132))
    finish(cyl(0.008, 0.0, 0.02, 10), n + '_Peen', GOLD, (0, 0, 0.162))

def bat():
    n = 'Baseball Bat'; model('W_' + n)
    prof = [(0.0, 0.12), (0.022, 0.12), (0.029, 0.112), (0.027, 0.1), (0.019, 0.094), (0.019, 0.0), (0.021, -0.1), (0.03, -0.25), (0.042, -0.45), (0.045, -0.6), (0.045, -0.72), (0.041, -0.75), (0.025, -0.759), (0.0, -0.762)]
    finish(lathe(prof, 24), n + '_Body', BAT, smooth=50)
    tape = [(0.0, 0.092), (0.0205, 0.092)] + [(0.0205 + 0.0007 * (i % 2), 0.09 - 0.16 * i / 20) for i in range(21)] + [(0.0, -0.07)]
    finish(lathe(tape, 20), n + '_Tape', GRIPM, smooth=60)

def sledgehammer():
    n = 'Sledgehammer'; model('W_' + n)
    finish(lathe([(0.0, 0.12), (0.023, 0.12), (0.024, 0.1), (0.02, 0.05), (0.019, -0.5), (0.022, -0.76), (0.0, -0.76)], 18), n + '_Handle', WOOD)
    wrap = [(0.0, 0.112), (0.0255, 0.112)] + [(0.0225 + 0.001 * (i % 2), 0.11 - 0.16 * i / 16) for i in range(17)] + [(0.0, -0.05)]
    finish(lathe(wrap, 18), n + '_Wrap', GRIPM, smooth=60)
    finish(box(0.25, 0.14, 0.14), n + '_Head', STEELD, (0, 0, -0.82), bevel=0.018, segs=3)
    for sx in (-1, 1):
        finish(cyl(0.074, 0.07, 0.03, 8), f'{n}_Face{sx}', GUND, (sx * 0.14, 0, -0.82), (0, sx * PI / 2, PI / 8), bevel=0.004)
    finish(box(0.05, 0.05, 0.04), n + '_Collar', GUN, (0, 0, -0.735), bevel=0.004)

def flamethrower():
    n = 'Flamethrower'; model('W_' + n)
    finish(prism([(0.06, 0.06), (-0.38, 0.06), (-0.4, 0.035), (-0.4, -0.015), (0.06, -0.02)], 0.06), n + '_Body', REDP, bevel=0.005)
    caps = [(0.06 * math.sin(PI / 2 * i / 6), -0.3 - 0.05 * math.cos(PI / 2 * i / 6)) for i in range(7)]
    tank = caps + [(0.06 * math.sin(PI / 2 * i / 6), -0.02 + 0.05 * math.cos(PI / 2 * i / 6)) for i in range(6, -1, -1)]
    finish(lathe(tank, 24), n + '_Tank', BRASS, (0, -0.078, 0))
    for z in (-0.07, -0.25):
        finish(cyl(0.0625, 0.0625, 0.014, 24), f'{n}_Strap{z}', GUND, (0, -0.078, z))
    finish(cyl(0.016, 0.016, 0.01, 16), n + '_GaugeBody', GUN, (0.06, -0.078, -0.16), (0, PI / 2, 0))
    finish(cyl(0.012, 0.012, 0.002, 16), n + '_GaugeFace', GAUGE, (0.066, -0.078, -0.16), (0, PI / 2, 0))
    finish(box(0.001, 0.016, 0.002), n + '_Needle', BLACK, (0.0675, -0.074, -0.157), (0.6, 0, 0), smooth=None)
    finish(lathe([(0.022, -0.38), (0.03, -0.5), (0.034, -0.52), (0.026, -0.52), (0.018, -0.4)], 20, closed=True), n + '_Nozzle', GUN, (0, 0.025, 0))
    for i in range(3):
        finish(cyl(0.031 + i * 0.002, 0.031 + i * 0.002, 0.006, 20), f'{n}_Vent{i}', GUND, (0, 0.025, -0.41 - i * 0.03))
    finish(cyl(0.006, 0.006, 0.06, 10), n + '_PilotTube', GUN, (0, -0.006, -0.47))
    finish(sphere(0.006, 10, 8), n + '_Pilot', PILOT, (0, -0.006, -0.503))
    finish(sweep([(0, -0.06, -0.33), (0, -0.07, -0.36), (0, -0.05, -0.39), (0, -0.02, -0.39)], [0.009] * 4, m=10), n + '_Hose', GRIPM)
    finish(sweep([(0, 0.058, -0.05), (0, 0.11, -0.08), (0, 0.112, -0.17), (0, 0.11, -0.25), (0, 0.058, -0.28)], [0.01] * 5, m=10), n + '_Handle', GUN)
    pistol_grip(n, 0.02, -0.02, GRIPM, 0.034, 1.0)
    trigger(n, -0.025, -0.024)

def lightning_gun():
    n = 'Lightning Gun'; model('W_' + n)
    finish(prism([(0.07, 0.04), (0.045, 0.06), (-0.2, 0.06), (-0.23, 0.042), (-0.23, -0.02), (0.07, -0.025)], 0.06), n + '_Body', NAVY, bevel=0.006)
    for sx in (-1, 1):
        finish(cyl(0.012, 0.012, 0.14, 16), f'{n}_Cell{sx}', GLOW, (sx * 0.036, 0.03, -0.08))
        for z in (-0.153, -0.007):
            finish(cyl(0.0135, 0.0135, 0.008, 16), f'{n}_CellCap{sx}{z}', GUN, (sx * 0.036, 0.03, z))
    for i in range(3):
        finish(torus(0.04, 0.008, 32, 10), f'{n}_Coil{i}', GLOW, (0, 0.02, -0.26 - i * 0.055))
    finish(cyl(0.013, 0.013, 0.2, 16), n + '_Rod', CHROME, (0, 0.02, -0.32))
    for k in range(3):
        a = k * 2 * PI / 3 + PI / 2
        p0 = (0.03 * math.cos(a), 0.02 + 0.03 * math.sin(a), -0.23); p1 = (0.022 * math.cos(a), 0.02 + 0.022 * math.sin(a), -0.425)
        rod(f'{n}_Prong{k}', CHROME, p0, p1, 0.0035, 8)
    finish(sphere(0.02, 18, 12), n + '_Tip', GLOWW, (0, 0.02, -0.43))
    for i in range(3):
        finish(box(0.004, 0.022, 0.045), f'{n}_Fin{i}', GUND, (0, 0.07, -0.04 - i * 0.055), bevel=0.0015)
    pistol_grip(n, 0.02, -0.025, GRIPM, 0.034, 1.0)
    trigger(n, -0.025, -0.029)

def freeze_ray():
    n = 'Freeze Ray'; model('W_' + n)
    finish(box(0.066, 0.076, 0.3), n + '_Body', WHITE, (0, 0.012, -0.08), bevel=0.025, segs=4)
    finish(box(0.068, 0.012, 0.24), n + '_Stripe', ICE, (0, 0.03, -0.08), bevel=0.004)
    finish(cyl(0.03, 0.03, 0.04, 20), n + '_Neck', GUN, (0, 0.02, -0.245))
    finish(lathe([(0.03, -0.25), (0.072, -0.38), (0.077, -0.38), (0.035, -0.25)], 28, closed=True), n + '_Dish', WHITE, (0, 0.02, 0))
    finish(lathe([(0.0, -0.3), (0.069, -0.376), (0.0, -0.31)], 28, closed=True), n + '_DishInner', ICE, (0, 0.02, 0))
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.02)
    bmesh.ops.scale(bm, vec=(1, 1, 1.6), verts=bm.verts)
    finish(bm, n + '_Crystal', ICEB, (0, 0.02, -0.34), smooth=None)
    caps = [(0.035 * math.sin(PI / 2 * i / 5), -0.18 - 0.03 * math.cos(PI / 2 * i / 5)) for i in range(6)]
    tank = caps + [(0.035 * math.sin(PI / 2 * i / 5), -0.02 + 0.03 * math.cos(PI / 2 * i / 5)) for i in range(5, -1, -1)]
    finish(lathe(tank, 20), n + '_Tank', ICE, (0, -0.06, 0))
    for z in (-0.04, -0.16):
        finish(cyl(0.037, 0.037, 0.01, 20), f'{n}_TankBand{z}', GUN, (0, -0.06, z))
    for sx in (-1, 1):
        finish(prism([(-0.02, 0.04), (-0.16, 0.04), (-0.19, 0.02), (-0.05, 0.02)], 0.004), f'{n}_Fin{sx}', ICE, (sx * 0.036, 0, 0), (0, 0, sx * 0.5), bevel=0.001)
    pistol_grip(n, 0.02, -0.026, GRIPM, 0.034, 1.0)
    trigger(n, -0.025, -0.03)

# ---------------------------------------------------------------- props
def barrel():
    model('P_Barrel')
    prof = [(0.0, 0.43), (0.27, 0.43), (0.28, 0.437), (0.292, 0.45), (0.3, 0.448), (0.3, 0.17), (0.308, 0.16), (0.308, 0.14), (0.3, 0.13),
            (0.3, -0.13), (0.308, -0.14), (0.308, -0.16), (0.3, -0.17), (0.3, -0.448), (0.292, -0.45), (0.28, -0.437), (0.27, -0.43), (0.0, -0.43)]
    finish(lathe(prof, 36), 'Barrel_Body', PAINT, rot=(-PI / 2, 0, 0), smooth=40)
    t = model('P_BarrelTrim')
    finish(cyl(0.03, 0.03, 0.014, 16), 'Barrel_Bung1', GUN, (0.15, 0.436, 0.0), (-PI / 2, 0, 0), bevel=0.002)
    finish(cyl(0.02, 0.02, 0.012, 16), 'Barrel_Bung2', GUN, (-0.17, 0.435, 0.06), (-PI / 2, 0, 0), bevel=0.002)
    finish(torus(0.296, 0.006, 48, 8), 'Barrel_TopRim', GUND, (0, 0.448, 0), (PI / 2, 0, 0))
    finish(torus(0.296, 0.006, 48, 8), 'Barrel_BottomRim', GUND, (0, -0.448, 0), (PI / 2, 0, 0))

def bomb():
    model('P_BombCap')
    finish(lathe([(0.0, 0.3), (0.05, 0.3), (0.062, 0.292), (0.07, 0.275), (0.07, 0.2), (0.0, 0.2)], 24), 'Bomb_Cap', GUND, rot=(-PI / 2, 0, 0), smooth=40)
    finish(torus(0.07, 0.006, 24, 8), 'Bomb_CapRing', GUN, (0, 0.235, 0), (PI / 2, 0, 0))

# ---------------------------------------------------------------- ragdoll: one skinned mesh + armature
# Modelled on the default 1.8 m figure (the game's npcLayout() with no body changes). One bone per
# physics part; the game moves each bone with its part and scales it to the ragdoll's body shape.
RAG_PARTS = {  # part: centre (x, y) in metres, from npcLayout()
    'torso': (0, 1.18), 'head': (0, 1.595), 'uArmL': (-0.24, 1.29), 'lArmL': (-0.24, 0.985), 'uArmR': (0.24, 1.29), 'lArmR': (0.24, 0.985),
    'uLegL': (-0.09, 0.672), 'lLegL': (-0.09, 0.225), 'uLegR': (0.09, 0.672), 'lLegR': (0.09, 0.225),
}
def ss(a, b, x):  # smoothstep from a (0) to b (1); a may be greater than b
    t = max(0.0, min(1.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)

def ring_se(cx, cy, cz, hx, hz, n=28, e=2.6):  # superellipse ring in the XZ plane at height cy
    out = []
    for k in range(n):
        a = 2 * PI * k / n; c, s_ = math.cos(a), math.sin(a)
        out.append((cx + hx * math.copysign(abs(c) ** (2 / e), c), cy, cz + hz * math.copysign(abs(s_) ** (2 / e), s_)))
    return out

def loft(rings, cap=True):
    bm = bmesh.new(); R = [[bm.verts.new(p) for p in r] for r in rings]; n = len(rings[0])
    for i in range(len(R) - 1):
        for k in range(n): bm.faces.new((R[i][k], R[i][(k + 1) % n], R[i + 1][(k + 1) % n], R[i + 1][k]))
    if cap:
        for r in (R[0], R[-1]):
            c = bm.verts.new(sum((v.co for v in r), Vector()) / n)
            for k in range(n): bm.faces.new((r[k], r[(k + 1) % n], c))
    return bm

def lathe_y(prof, cx, cz, segs=20):  # spin (radius, y) around a vertical axis through (cx, cz)
    return loft([[(cx + r * math.cos(2 * PI * k / segs), y, cz + r * math.sin(2 * PI * k / segs)) for k in range(segs)] for r, y in prof], cap=False)

def ragdoll():
    global CUR
    mats = [mat('R_Shirt', 0x2f7fe0, 0.0, 0.8), mat('R_Pants', 0x2b3a55, 0.0, 0.85), mat('R_Skin', 0xf1c7a5, 0.0, 0.7), mat('R_Shoes', 0x1b1b1b, 0.0, 0.6)]
    SH, PA, SK, SO = range(4)
    master = bmesh.new(); weights = []
    def add(bm, wfn, mi=None, mfn=None):
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        vmap = {}
        for v in bm.verts:
            p = v.co.copy(); vmap[v] = master.verts.new(C @ p); weights.append(wfn(p))
        for f in bm.faces:
            nf = master.faces.new([vmap[v] for v in f.verts]); nf.smooth = True
            nf.material_index = mfn(sum((v.co for v in f.verts), Vector()) / len(f.verts)) if mfn else mi
        bm.free()
    one = lambda part: (lambda p: {part: 1.0})
    def blend(main, other, w):
        w = max(0.0, min(1.0, w)); return {main: 1 - w, other: w} if w > 1e-4 else {main: 1.0}
    # torso: shirt on top, trousers round the hips
    secs = [(0.905, 0.15, 0.085, 0), (0.92, 0.168, 0.095, 0), (0.98, 0.168, 0.095, 0), (1.05, 0.152, 0.088, 0), (1.15, 0.165, 0.095, 0.005),
            (1.25, 0.176, 0.1, 0.008), (1.35, 0.18, 0.098, 0.004), (1.41, 0.175, 0.09, 0), (1.445, 0.15, 0.075, 0), (1.465, 0.09, 0.055, -0.005)]
    add(loft([ring_se(0, y, z, hx, hz, 32) for y, hx, hz, z in secs]), one('torso'), mfn=lambda c: PA if c.y < 0.975 else SH)
    # neck, stretching between torso and head
    add(lathe_y([(0.0, 1.43), (0.046, 1.43), (0.045, 1.48), (0.043, 1.53), (0.0, 1.53)], 0, -0.005, 16), lambda p: blend('torso', 'head', ss(1.465, 1.5, p.y)), SK)
    # head with ears and a nose (the game adds the face, hair and hats)
    add(_moved(sphere(0.12, 32, 20), (0, 1.595, 0)), one('head'), SK)
    for sx in (-1, 1):
        e = sphere(0.03, 12, 8); bmesh.ops.scale(e, vec=(0.45, 1, 0.75), verts=e.verts)
        add(_moved(e, (sx * 0.118, 1.585, -0.005)), one('head'), SK)
    add(_moved(sphere(0.016, 12, 8), (0, 1.578, 0.115)), one('head'), SK)
    for sx, s in ((-1, 'L'), (1, 'R')):
        x = sx * 0.24
        # upper arm (sleeve) with a rounded shoulder, blending into the torso and the forearm
        add(lathe_y([(0, 1.465), (0.03, 1.457), (0.045, 1.44), (0.052, 1.41), (0.05, 1.3), (0.047, 1.2), (0.045, 1.14), (0.035, 1.12), (0, 1.115)], x, 0),
            lambda p, s=s: blend('uArm' + s, 'torso', 0.5 * ss(1.40, 1.46, p.y)) if p.y > 1.3 else blend('uArm' + s, 'lArm' + s, 0.5 * ss(1.17, 1.12, p.y)), SH)
        # forearm and hand
        add(lathe_y([(0, 1.155), (0.03, 1.152), (0.043, 1.14), (0.042, 1.05), (0.036, 0.88), (0.03, 0.85), (0, 0.845)], x, 0),
            lambda p, s=s: blend('lArm' + s, 'uArm' + s, 0.5 * ss(1.11, 1.15, p.y)), SK)
        hand = [(0.845, 0.016, 0.03), (0.82, 0.019, 0.036), (0.78, 0.018, 0.035), (0.755, 0.014, 0.028), (0.745, 0.006, 0.015)]
        add(loft([ring_se(x, y, 0.005, hx, hz, 16) for y, hx, hz in hand]), one('lArm' + s), SK)
        add(sweep([(x - sx * 0.006, 0.82, 0.03), (x - sx * 0.008, 0.8, 0.045), (x - sx * 0.008, 0.785, 0.05)], [0.009, 0.008, 0.007], m=8), one('lArm' + s), SK)
        # thigh and shin (trousers)
        lx = sx * 0.09
        add(lathe_y([(0, 0.94), (0.05, 0.935), (0.07, 0.91), (0.074, 0.86), (0.068, 0.7), (0.06, 0.5), (0.057, 0.46), (0.045, 0.44), (0, 0.435)], lx, 0, 22),
            lambda p, s=s: blend('uLeg' + s, 'torso', 0.6 * ss(0.86, 0.93, p.y)) if p.y > 0.7 else blend('uLeg' + s, 'lLeg' + s, 0.5 * ss(0.48, 0.43, p.y)), PA)
        add(lathe_y([(0, 0.475), (0.045, 0.47), (0.058, 0.455), (0.058, 0.38), (0.052, 0.25), (0.044, 0.12), (0.042, 0.07), (0, 0.06)], lx, 0, 22),
            lambda p, s=s: blend('lLeg' + s, 'uLeg' + s, 0.5 * ss(0.42, 0.47, p.y)), PA)
        # shoe
        shoe = [(-0.075, 0.035, 0.05, 0.028), (-0.06, 0.035, 0.058, 0.036), (0.0, 0.035, 0.06, 0.037), (0.07, 0.03, 0.062, 0.03),
                (0.12, 0.026, 0.055, 0.024), (0.15, 0.024, 0.04, 0.017), (0.158, 0.024, 0.02, 0.01)]
        rings = []
        for z, cy, hx, hy in shoe:
            r = []
            for k in range(20):
                a = 2 * PI * k / 20; c, s_ = math.cos(a), math.sin(a)
                r.append((lx + hx * math.copysign(abs(c) ** (2 / 3), c), cy + hy * math.copysign(abs(s_) ** (2 / 3), s_), z + 0.0))
            rings.append(r)
        add(loft(rings), one('lLeg' + s), SO)
    me = bpy.data.meshes.new('R_BodyMesh'); master.to_mesh(me); master.free()
    for m in mats: me.materials.append(m)
    # armature: one bone per physics part, pointing up through the part's centre
    arm_data = bpy.data.armatures.new('R_Armature'); arm = bpy.data.objects.new('R_Ragdoll', arm_data); COLL.objects.link(arm)
    bpy.context.view_layer.objects.active = arm; arm.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    for name, (x, y) in RAG_PARTS.items():
        b = arm_data.edit_bones.new(name); b.head = C @ Vector((x, y, 0)); b.tail = C @ Vector((x, y + 0.06, 0))
    bpy.ops.object.mode_set(mode='OBJECT')
    ob = bpy.data.objects.new('R_BodyMesh', me); COLL.objects.link(ob); ob.parent = arm
    groups = {name: ob.vertex_groups.new(name=name) for name in RAG_PARTS}
    for i, w in enumerate(weights):
        for part, val in w.items(): groups[part].add([i], val, 'REPLACE')
    md = ob.modifiers.new('Armature', 'ARMATURE'); md.object = arm
    me.set_sharp_from_angle(angle=math.radians(60))
    CUR = None

def _moved(bm, pos):
    bmesh.ops.translate(bm, vec=pos, verts=bm.verts); return bm

# ---------------------------------------------------------------- props
# Each prop: a '<Name>_Body' mesh that becomes the prop's own (paintable) mesh, sized exactly like its
# physics shape, plus trim pieces with their own materials. Centred on the physics centre.
BODY = mat('PropBody', 0xc39056, 0.0, 0.7)  # placeholder: the game keeps each prop's own material
CRATE_DARK = mat('CrateFrame', 0x7a4f26, 0.0, 0.75)
TAPE = mat('Tape', 0xd8c08a, 0.0, 0.4)
BOLT = mat('Bolt', 0x3a4048, 0.8, 0.35)
PIP = mat('Pip', 0x111111, 0.0, 0.4)
RUBBER = mat('Rubber', 0x1a1a1a, 0.0, 0.9)
HUBM = mat('Hub', 0xffb020, 0.4, 0.4)
MELON_DARK = mat('MelonStripe', 0x24561f, 0.0, 0.55)
STEM = mat('Stem', 0x6b4a2e, 0.0, 0.8)
PIN_RED = mat('PinStripe', 0xc0392b, 0.1, 0.35)
GRANITE = mat('Granite', 0x8b8f94, 0.05, 0.6)
GRANITE_D = mat('GraniteBand', 0x4c5056, 0.05, 0.5)

def crate():
    model('P_Crate')
    finish(box(0.47, 0.47, 0.47), 'Crate_Body', BODY, bevel=0.004)
    e = 0.22
    for ax in range(3):  # twelve edge beams
        for a in (-e, e):
            for b in (-e, e):
                size = [0.06, 0.06, 0.06]; size[ax] = 0.5
                pos = {0: (0, a, b), 1: (a, 0, b), 2: (a, b, 0)}[ax]
                finish(box(*size), f'Crate_Edge{ax}{a}{b}', CRATE_DARK, pos, bevel=0.006)
    for sg in (-1, 1):  # a diagonal brace on every face
        finish(box(0.055, 0.54, 0.022), f'Crate_BraceZ{sg}', CRATE_DARK, (0, 0, sg * 0.24), (0, 0, sg * PI / 4), bevel=0.004)
        finish(box(0.022, 0.54, 0.055), f'Crate_BraceX{sg}', CRATE_DARK, (sg * 0.24, 0, 0), (sg * PI / 4, 0, 0), bevel=0.004)
        finish(box(0.54, 0.022, 0.055), f'Crate_BraceY{sg}', CRATE_DARK, (0, sg * 0.24, 0), (0, sg * PI / 4, 0), bevel=0.004)

def small_box():
    model('P_SmallBox')
    finish(box(0.25, 0.25, 0.25), 'SmallBox_Body', BODY, bevel=0.008)
    finish(box(0.06, 0.004, 0.252), 'SmallBox_TapeTop', TAPE, (0, 0.1255, 0), smooth=None)
    for z in (-1, 1):
        finish(box(0.06, 0.07, 0.004), f'SmallBox_Tape{z}', TAPE, (0, 0.09, z * 0.1255), smooth=None)
    finish(box(0.002, 0.003, 0.25), 'SmallBox_Seam', BOLT, (0, 0.1262, 0), smooth=None)

def plank():
    model('P_Plank'); finish(box(0.35, 0.08, 2.2), 'Plank_Body', BODY, bevel=0.01)

def block():
    model('P_Block'); finish(box(0.2, 0.2, 0.6), 'Block_Body', BODY, bevel=0.008)

def brick():
    model('P_Brick'); finish(box(0.5, 0.25, 0.25), 'Brick_Body', BODY, bevel=0.012)

def steel_block():
    model('P_SteelBlock')
    finish(box(0.6, 0.6, 0.6), 'SteelBlock_Body', BODY, bevel=0.02, segs=3)
    k = 0
    for ax in range(3):
        for sgn in (-1, 1):
            for a in (-0.23, 0.23):
                for b in (-0.23, 0.23):
                    pos = [a, b]; pos.insert(ax, sgn * 0.301)
                    rot = [(0, PI / 2, 0), (-PI / 2, 0, 0), (0, 0, 0)][ax]
                    finish(cyl(0.022, 0.022, 0.012, 6), f'SteelBlock_Bolt{k}', BOLT, tuple(pos), rot, bevel=0.002); k += 1

def domino():
    model('P_Domino')
    finish(box(0.28, 0.5, 0.07), 'Domino_Body', BODY, bevel=0.018, segs=3)
    pips = {3: [(-0.07, 0.07), (0, 0.125), (0.07, 0.18)], 5: [(-0.07, -0.07), (0.07, -0.07), (0, -0.125), (-0.07, -0.18), (0.07, -0.18)]}
    k = 0
    for zs in (-1, 1):
        finish(box(0.2, 0.008, 0.004), f'Domino_Line{zs}', PIP, (0, 0, zs * 0.0352), smooth=None)
        for (x, y) in pips[3] + pips[5]:
            e = sphere(0.022, 10, 5); bmesh.ops.scale(e, vec=(1, 1, 0.25), verts=e.verts)
            finish(e, f'Domino_Pip{k}', PIP, (x, y, zs * 0.034)); k += 1

def cart():
    model('P_CartBed')
    finish(box(1.0, 0.18, 1.5), 'CartBed_Body', BODY, bevel=0.012)
    for x in (-1, 1):
        finish(box(0.06, 0.16, 1.5), f'CartBed_Rail{x}', CRATE_DARK, (x * 0.47, 0.17, 0), bevel=0.008)
    for z in (-1, 1):
        finish(box(0.88, 0.16, 0.06), f'CartBed_End{z}', CRATE_DARK, (0, 0.17, z * 0.72), bevel=0.008)
    for x in (-1, 1):
        finish(box(0.02, 0.12, 0.04), f'CartBed_Bracket{x}', BOLT, (x * 0.51, -0.06, 0.55), smooth=None)
        finish(box(0.02, 0.12, 0.04), f'CartBed_BracketB{x}', BOLT, (x * 0.51, -0.06, -0.55), smooth=None)
        rod(f'CartBed_Arm{x}', BOLT, (x * 0.3, 0.15, -0.75), (x * 0.25, 0.4, -1.15), 0.018)
    rod('CartBed_Handle', RUBBER, (-0.3, 0.4, -1.15), (0.3, 0.4, -1.15), 0.024, 12)

def wheel():
    model('P_Wheel')
    t = torus(0.172, 0.048, 36, 12); bmesh.ops.scale(t, vec=(1, 1, 1.25), verts=t.verts)
    finish(t, 'Wheel_Body', BODY, rot=(0, PI / 2, 0))
    finish(cyl(0.13, 0.13, 0.07, 24), 'Wheel_Rim', HUBM, rot=(0, PI / 2, 0), bevel=0.006)
    finish(cyl(0.045, 0.045, 0.13, 12), 'Wheel_Hub', BOLT, rot=(0, PI / 2, 0), bevel=0.004)

def melon():
    model('P_Melon')
    m = sphere(0.18, 28, 18); bmesh.ops.scale(m, vec=(1, 0.94, 1), verts=m.verts)
    finish(m, 'Melon_Body', BODY, smooth=60)
    for k in range(10):
        a = 2 * PI * k / 10
        pts = [(0.1815 * math.sin(t) * math.cos(a), 0.94 * 0.1815 * math.cos(t), 0.1815 * math.sin(t) * math.sin(a)) for t in [0.15 + (PI - 0.3) * i / 14 for i in range(15)]]
        finish(sweep(pts, [(0.016, 0.003)] * 15, m=6, up=(math.cos(a), 0, math.sin(a))), f'Melon_Stripe{k}', MELON_DARK, smooth=60)
    finish(cyl(0.008, 0.005, 0.03, 8), 'Melon_Stem', STEM, (0, 0.175, 0), (-PI / 2, 0, 0))

def pin():
    model('P_Pin')
    prof = [(0.0, -0.225), (0.034, -0.225), (0.05, -0.17), (0.061, -0.09), (0.056, -0.02), (0.04, 0.05), (0.027, 0.1), (0.031, 0.14), (0.036, 0.17), (0.03, 0.205), (0.015, 0.222), (0.0, 0.225)]
    finish(lathe_y(prof, 0, 0, 24), 'Pin_Body', BODY, smooth=60)
    for y, r in ((0.075, 0.0345), (0.09, 0.0305)):
        finish(lathe_y([(r, y - 0.005), (r, y + 0.005)], 0, 0, 24), f'Pin_Stripe{y}', PIN_RED)

def bowling_ball():
    model('P_BowlingBall')
    for k, (th, ph) in enumerate(((0.35, 0.0), (0.55, 0.35), (0.55, -0.35))):
        n = Vector((math.sin(th) * math.sin(ph), math.cos(th), math.sin(th) * math.cos(ph)))
        q = Vector((0, 0, 1)).rotation_difference(n).to_euler('XYZ')
        finish(cyl(0.017 if k else 0.02, 0.017 if k else 0.02, 0.012, 14), f'BowlingBall_Hole{k}', BLACK, tuple(n * 0.197), tuple(q))

def curling():
    model('P_Curling')
    sweep_pts = [(0, 0.11, 0.06), (0, 0.17, 0.06), (0, 0.19, 0.03), (0, 0.192, -0.02), (0, 0.192, -0.14)]
    finish(sweep(sweep_pts, [0.018] * 5, m=12), 'Curling_Body', BODY)
    finish(lathe_y([(0.0, -0.11), (0.2, -0.11), (0.25, -0.095), (0.275, -0.06), (0.28, -0.02), (0.275, 0.04), (0.25, 0.08), (0.2, 0.105), (0.0, 0.11)], 0, 0, 36), 'Curling_Stone', GRANITE, smooth=50)
    finish(lathe_y([(0.2805, -0.035), (0.2805, 0.005)], 0, 0, 36), 'Curling_Band', GRANITE_D)
    finish(cyl(0.03, 0.03, 0.03, 12), 'Curling_Bolt', BOLT, (0, 0.115, 0.06), (-PI / 2, 0, 0))

# ---------------------------------------------------------------- map pieces (origin noted per piece)
BARK = mat('Bark', 0x6b4a2e, 0.0, 0.9)
NEEDLES = mat('Needles', 0x2f7a3a, 0.0, 0.85)
NEEDLES_D = mat('NeedlesDark', 0x2f5e4a, 0.0, 0.85)
SNOW = mat('Snow', 0xf4f8ff, 0.0, 0.95)
ROCK = mat('Rock', 0x8d8f8a, 0.0, 0.9)
TABLE_TOP = mat('TableTop', 0xa0784c, 0.0, 0.6)
TABLE_LEG = mat('TableLeg', 0x6e4c2b, 0.0, 0.7)
RACK_POST = mat('RackPost', 0xd9822b, 0.3, 0.5)
RACK_BEAM = mat('RackBeam', 0xc2452d, 0.3, 0.5)
RACK_DECK = mat('RackDeck', 0x6b7480, 0.7, 0.4)
LAMP_SHADE = mat('LampShade', 0x2f4a3a, 0.4, 0.5)
BULB = mat('Bulb', 0xfff2cc, 0.0, 0.3, 0xffe2b0, 6.0)
DOME = mat('DomePanel', 0xd8dde3, 0.2, 0.45)
DOME_RIB = mat('DomeRib', 0x7c8590, 0.8, 0.35)
GLASS = mat('DomeGlass', 0x16314d, 0.6, 0.1, 0x0b2a4a, 0.6)
CONCRETE = mat('Concrete', 0x9a9ea3, 0.0, 0.9)
HAZARD = mat('Hazard', 0xf2c230, 0.1, 0.5)
MOON = mat('MoonRock', 0x7d7d7d, 0.0, 0.95)
PIPE_BLUE = mat('HalfPipe', 0x5b8bd9, 0.1, 0.55)
PIPE_SIDE = mat('HalfPipeSide', 0x3f69ad, 0.1, 0.65)

def foliage_tier(R, base, h, lobes=9, seed=0):
    bm = bmesh.new(); n = lobes * 4
    rim = [bm.verts.new((R * (1 + 0.14 * math.sin(lobes * 2 * PI * k / n + seed)) * math.cos(2 * PI * k / n),
                         base - 0.18 * (1 + math.sin(lobes * 2 * PI * k / n + seed)) / 2,
                         R * (1 + 0.14 * math.sin(lobes * 2 * PI * k / n + seed)) * math.sin(2 * PI * k / n))) for k in range(n)]
    mid = [bm.verts.new((0.55 * R * math.cos(2 * PI * (k + 0.5) / n), base + 0.45 * h, 0.55 * R * math.sin(2 * PI * (k + 0.5) / n))) for k in range(n)]
    top = bm.verts.new((0, base + h, 0)); under = bm.verts.new((0, base + 0.12, 0))
    for k in range(n):
        bm.faces.new((rim[k], rim[(k + 1) % n], mid[k])); bm.faces.new((mid[k], rim[(k + 1) % n], mid[(k + 1) % n]))
        bm.faces.new((mid[k], mid[(k + 1) % n], top)); bm.faces.new((rim[(k + 1) % n], rim[k], under))
    return bm

def pine(name, snowy):
    model(name)  # origin on the ground at the trunk; scale 1 = the game's tree(s = 1)
    finish(lathe_y([(0.0, 0.0), (0.24, 0.0), (0.2, 0.6), (0.17, 2.0), (0.12, 3.6), (0.0, 3.8)], 0, 0, 10), name + '_Trunk', BARK, smooth=50)
    for i in range(3):
        R = 1.6 - i * 0.4
        finish(foliage_tier(R, 1.5 + i * 1.0, 1.8, 9, i * 1.3), f'{name}_Tier{i}', NEEDLES_D if snowy else NEEDLES, smooth=None)
        if snowy:
            finish(foliage_tier(R * 0.5, 2.6 + i * 1.0, 0.72, 9, i * 1.3), f'{name}_Snow{i}', SNOW, smooth=None)

def rock(name, seed):
    model(name)  # radius 1, centred
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    for v in bm.verts:
        x, y, z = v.co
        d = 1 + 0.16 * math.sin(3.1 * x + seed) * math.cos(2.3 * z - seed) + 0.1 * math.sin(5.7 * y + 2 * seed) + 0.06 * math.cos(7.3 * x + 4.1 * z + seed)
        v.co = Vector((x * d, y * d * 0.85, z * d))
    finish(bm, name + '_Body', ROCK, smooth=None)

def table():
    model('M_Table')  # centred on the 2.6 x 0.8 x 1.2 physics box
    finish(box(2.6, 0.08, 1.2), 'Table_Top', TABLE_TOP, (0, 0.36, 0), bevel=0.012)
    for x in (-1.2, 1.2):
        for z in (-0.5, 0.5):
            finish(box(0.1, 0.72, 0.1), f'Table_Leg{x}{z}', TABLE_LEG, (x, -0.04, z), bevel=0.008)
    for z in (-0.52, 0.52):
        finish(box(2.3, 0.1, 0.04), f'Table_Apron{z}', TABLE_LEG, (0, 0.27, z), bevel=0.005)
    finish(box(2.3, 0.05, 0.05), 'Table_Stretcher', TABLE_LEG, (0, -0.25, 0), bevel=0.005)
    for x in (-1.2, 1.2):
        finish(box(0.05, 0.05, 0.95), f'Table_Side{x}', TABLE_LEG, (x, -0.25, 0), bevel=0.005)

def rack():
    model('M_Rack')  # origin on the floor at the rack's centre (posts at x +-2.4, z +-0.6; shelves at 1.1, 2.3, 3.5)
    for x in (-2.4, 2.4):
        for z in (-0.6, 0.6):
            finish(box(0.12, 4.2, 0.12), f'Rack_Post{x}{z}', RACK_POST, (x, 2.1, z), bevel=0.006)
            for i in range(20):
                finish(box(0.004, 0.035, 0.03), f'Rack_Hole{x}{z}{i}', BLACK, (x + (0.061 if x > 0 else -0.061), 0.4 + i * 0.19, z), smooth=None)
        for y0, y1 in ((0.3, 1.0), (1.2, 2.2), (2.4, 3.4)):  # side bracing
            rod(f'Rack_Brace{x}{y0}', RACK_POST, (x, y0, -0.55), (x, y1, 0.55), 0.018, 6)
            rod(f'Rack_BraceB{x}{y0}', RACK_POST, (x, y0, 0.55), (x, y1, -0.55), 0.018, 6)
    for h in (1.1, 2.3, 3.5):
        for z in (-0.64, 0.64):
            finish(box(4.68, 0.12, 0.06), f'Rack_Beam{h}{z}', RACK_BEAM, (0, h - 0.01, z), bevel=0.006)
        finish(box(4.7, 0.03, 1.3), f'Rack_Deck{h}', RACK_DECK, (0, h + 0.035, 0), bevel=0.004)
        for i in range(12):
            finish(box(0.02, 0.025, 1.24), f'Rack_Wire{h}{i}', RACK_DECK, (-2.2 + i * 0.4, h + 0.008, 0), smooth=None)

def lamp():
    model('M_Lamp')  # origin at the bulb
    rod('Lamp_Cable', RUBBER, (0, 0.2, 0), (0, 1.6, 0), 0.01, 6)
    finish(lathe_y([(0.03, 0.22), (0.08, 0.2), (0.32, -0.02), (0.36, -0.06), (0.35, -0.07), (0.3, -0.03), (0.07, 0.18), (0.0, 0.19)], 0, 0, 24), 'Lamp_Shade', LAMP_SHADE)
    finish(sphere(0.09, 16, 10), 'Lamp_Bulb', BULB, (0, 0.03, 0))

def dome():
    model('M_Dome')  # origin at the sphere centre; the ground is at y = 0.8 (the game sinks it 0.8 m)
    R = 5.0; ys = [0.8 + (R - 0.8) * (1 - math.cos(PI / 2 * i / 16)) for i in range(17)]
    finish(lathe_y([(math.sqrt(max(0.0, R * R - y * y)), y) for y in ys], 0, 0, 48), 'Dome_Shell', DOME, smooth=50)
    for k in range(16):  # ribs
        a = 2 * PI * k / 16
        pts = [((R + 0.03) * math.sqrt(max(0.0, 1 - (y / R) ** 2)) * math.cos(a), y, (R + 0.03) * math.sqrt(max(0.0, 1 - (y / R) ** 2)) * math.sin(a)) for y in ys]
        finish(sweep(pts, [0.06] * len(pts), m=6), f'Dome_Rib{k}', DOME_RIB)
    for y in (2.0, 3.4, 4.4):  # rings
        r = math.sqrt(R * R - y * y) + 0.03
        finish(torus(r, 0.05, 64, 6), f'Dome_Ring{y}', DOME_RIB, (0, y, 0), (PI / 2, 0, 0))
    yb = [2.15 + 1.1 * i / 4 for i in range(5)]  # window band
    finish(lathe_y([(math.sqrt(R * R - y * y) + 0.012, y) for y in yb], 0, 0, 48), 'Dome_Windows', GLASS, smooth=50)
    finish(torus(math.sqrt(R * R - 0.81) + 0.05, 0.18, 64, 8), 'Dome_Base', CONCRETE, (0, 0.85, 0), (PI / 2, 0, 0))

def airlock():
    model('M_Airlock')  # centred on the 1.6 x 2.2 x 0.4 physics box
    finish(box(1.3, 2.0, 0.3), 'Airlock_Door', DOME, (0, -0.05, 0.05), bevel=0.02)
    finish(box(0.02, 1.95, 0.32), 'Airlock_Seam', BLACK, (0, -0.05, 0.05), smooth=None)
    for x in (-0.75, 0.75):
        finish(box(0.15, 2.3, 0.45), f'Airlock_Jamb{x}', DOME_RIB, (x, 0.0, 0), bevel=0.015)
    finish(box(1.65, 0.18, 0.45), 'Airlock_Lintel', DOME_RIB, (0, 1.1, 0), bevel=0.015)
    for i in range(6):
        finish(box(0.12, 0.06, 0.02), f'Airlock_Stripe{i}', HAZARD if i % 2 == 0 else BLACK, (-0.33 + i * 0.13, 1.1, 0.23), smooth=None)
    finish(cyl(0.12, 0.12, 0.33, 24), 'Airlock_Window', GLASS, (0, 0.5, 0.05))
    finish(torus(0.12, 0.02, 24, 8), 'Airlock_WindowRim', DOME_RIB, (0, 0.5, 0.215))
    finish(sphere(0.04, 12, 8), 'Airlock_Light', mat('AirlockLight', 0xff4030, 0.0, 0.3, 0xff2010, 5.0), (0.75, 1.25, 0.24))

def crater(rad):
    name = f'M_Crater{rad}'; model(name)  # origin at the crater centre on the ground
    prof = [(rad - 1.6, -0.12), (rad - 1.5, -0.085), (rad + 1.5, 0.86), (rad + 1.85, 0.8), (rad + 2.3, 0.35), (rad + 2.7, 0.0), (rad + 2.7, -0.12)]
    segs = max(48, int(rad * 10))
    bm = lathe_y(prof + [prof[0]], 0, 0, segs)
    for v in bm.verts:  # lumpy rim
        x, y, z = v.co; a = math.atan2(z, x)
        if y > 0.0: v.co.y = y * (1 + 0.12 * math.sin(5 * a + rad) + 0.06 * math.sin(13 * a))
    finish(bm, name + '_Rim', MOON, smooth=40)

def half_pipe():
    model('M_HalfPipe')  # origin on the ground at the half-pipe's centre; runs 14 m along z
    pts = [(-7.6, 0.0), (-7.6, 5.1), (-6.85, 5.1)]
    for i in range(1, 25):
        th = PI / 2 * (1 - i / 24); pts.append((-(2 + 4.85 * math.sin(th)), 5.05 - 4.85 * math.cos(th)))
    pts += [(-2.0, 0.25), (2.0, 0.25)]
    for i in range(0, 24):
        th = PI / 2 * i / 24; pts.append((2 + 4.85 * math.sin(th), 5.05 - 4.85 * math.cos(th)))
    pts += [(6.85, 5.1), (7.6, 5.1), (7.6, 0.0)]
    finish(prism(pts, 14.0, 'xy'), 'HalfPipe_Body', PIPE_BLUE, smooth=20)
    for x in (-6.85, 6.85):
        finish(cyl(0.07, 0.07, 14.1, 16), f'HalfPipe_Coping{x}', CHROME, (x, 5.12, 0))
    for z in (-7.01, 7.01):  # coloured side panels
        finish(prism(pts, 0.02, 'xy'), f'HalfPipe_Side{z}', PIPE_SIDE, (0, 0, z), smooth=None)

for f in (pistol, shotgun, smg, rocket_launcher, rocket, grenade, crossbow, sword, bat, sledgehammer, flamethrower, lightning_gun, freeze_ray, barrel, bomb, ragdoll,
          crate, small_box, plank, block, brick, steel_block, domino, cart, wheel, melon, pin, bowling_ball, curling,
          lambda: pine('M_Pine', False), lambda: pine('M_PineSnow', True), lambda: rock('M_Rock1', 0.3), lambda: rock('M_Rock2', 1.7), lambda: rock('M_Rock3', 3.1),
          table, rack, lamp, dome, airlock, lambda: crater(6), lambda: crater(7), lambda: crater(10), half_pipe):
    f()

# Join each new model's pieces by material, so a rack is a handful of meshes instead of hundreds.
# A prop's '_Body' stays separate (the game swaps it in as the prop's own mesh).
def merge_children(root):
    groups = {}
    for c in list(root.children):
        if c.type != 'MESH' or c.name.endswith('_Body'): continue
        for md in list(c.modifiers):
            with bpy.context.temp_override(object=c, active_object=c, selected_objects=[c]):
                bpy.ops.object.modifier_apply(modifier=md.name)
        groups.setdefault(c.data.materials[0].name, []).append(c)
    for mname, objs in groups.items():
        if len(objs) > 1:
            with bpy.context.temp_override(object=objs[0], active_object=objs[0], selected_objects=objs, selected_editable_objects=objs):
                bpy.ops.object.join()
        objs[0].name = f'{root.name}_{mname}'
for r in [o for o in COLL.objects if o.parent is None and (o.name.startswith('M_') or (o.name.startswith('P_') and o.name not in ('P_Barrel', 'P_BarrelTrim', 'P_BombCap')))]:
    merge_children(r)

# ---------------------------------------------------------------- export
roots = [o for o in COLL.objects if o.parent is None]
dg = bpy.context.evaluated_depsgraph_get()
for r in roots:
    tris = 0
    for c in r.children:
        ev = c.evaluated_get(dg); me = ev.to_mesh(); me.calc_loop_triangles(); tris += len(me.loop_triangles); ev.to_mesh_clear()
    print(f'MODEL {r.name}: {len(r.children)} parts, {tris} tris')
kw = dict(filepath=OUT, export_format='GLB', export_apply=True, export_yup=True, use_selection=False)
try:
    bpy.ops.export_scene.gltf(**kw, export_cameras=False, export_lights=False)
except TypeError:
    bpy.ops.export_scene.gltf(**kw)
print('EXPORTED', OUT)

# ---------------------------------------------------------------- preview sheet (side view of everything)
if PREVIEW:
    order = ['W_Pistol', 'W_SMG', 'W_Grenade', 'W_Shotgun', 'W_Crossbow', 'W_Rocket', 'W_Rocket Launcher', 'W_Flamethrower', 'W_Lightning Gun',
             'W_Freeze Ray', 'W_Sword', 'W_Baseball Bat', 'W_Sledgehammer', 'P_Barrel', 'P_BombCap']
    pos = {}
    cols = 3; cw, ch = 1.25, 0.62
    for i, name in enumerate(order):
        c, r = i % cols, i // cols
        pos[name] = (c * cw, -r * ch)
    for o in roots:
        if o.name not in pos: continue
        x, z = pos[o.name]
        if o.name.startswith('W_'):
            o.rotation_euler = (0, 0, -PI / 2 if o.name != 'W_Rocket' else PI / 2)  # point right
            o.location = (x, 0, z)
        else:
            o.scale = (0.5, 0.5, 0.5); o.location = (x - 0.25 + (0.4 if o.name == 'P_BombCap' else 0), 0, z)
    t = bpy.data.objects['P_BarrelTrim']; t.scale = (0.5, 0.5, 0.5); t.location = bpy.data.objects['P_Barrel'].location
    rag_objs = [bpy.data.objects['R_Ragdoll'], bpy.data.objects['R_BodyMesh']]
    for o in COLL.objects:  # only the weapons sheet in this picture
        top = o
        while top.parent: top = top.parent
        if top.name not in pos and top.name != 'P_BarrelTrim': o.hide_render = True
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); COLL.objects.link(cam)
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = cols * cw + 0.2
    cam.location = ((cols - 1) * cw / 2, -5, -(len(order) // cols - 1) * ch / 2); cam.rotation_euler = (PI / 2, 0, 0)
    scene.camera = cam
    scene.render.engine = 'BLENDER_WORKBENCH'
    sh = scene.display.shading
    sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_specular_highlight = True
    try: sh.show_cavity = True; sh.cavity_type = 'BOTH'
    except Exception: pass
    sh.background_type = 'VIEWPORT'; sh.background_color = (0.07, 0.09, 0.12)
    scene.render.resolution_x = 1500; scene.render.resolution_y = int(1500 * (len(order) // cols) * ch / (cols * cw + 0.2))
    scene.render.filepath = PREVIEW
    bpy.ops.render.render(write_still=True)
    print('PREVIEW', PREVIEW)
    # second picture: the ragdoll, front three-quarter view, with one arm and leg posed to show the skinning
    for o in COLL.objects: o.hide_render = True
    for o in rag_objs: o.hide_render = False
    pb = bpy.data.objects['R_Ragdoll'].pose.bones
    pb['lArmR'].rotation_mode = 'XYZ'; pb['lArmR'].rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()
    cam.data.type = 'PERSP'; cam.data.lens = 50
    cam.location = (2.2, -4.2, 1.25); cam.rotation_euler = (math.radians(88), 0, math.radians(28))
    scene.render.resolution_x = 900; scene.render.resolution_y = 1100
    scene.render.filepath = PREVIEW.replace('.png', '_ragdoll.png')
    bpy.ops.render.render(write_still=True)
    print('PREVIEW', scene.render.filepath)
    # third picture: the props, three-quarter view
    props_order = ['P_Crate', 'P_SmallBox', 'P_SteelBlock', 'P_Domino', 'P_Brick', 'P_Block', 'P_Melon', 'P_Pin', 'P_Curling', 'P_Wheel', 'P_CartBed', 'P_Plank', 'M_Rock1', 'M_Table']
    for o in COLL.objects: o.hide_render = True
    for i, name in enumerate(props_order):
        r = bpy.data.objects[name]; c, row = i % 5, i // 5
        r.location = (c * 1.3, row * 1.6, 0); r.rotation_euler = (0, 0, 0.5)
        if name == 'M_Rock1': r.scale = (0.4, 0.4, 0.4)
        if name == 'M_Table': r.scale = (0.4, 0.4, 0.4)
        for o in [r] + list(r.children): o.hide_render = False
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 7.5
    cam.location = (2.6 + 6, 1.6 - 8, 6); cam.rotation_euler = (math.radians(55), 0, math.radians(37))
    scene.render.resolution_x = 1400; scene.render.resolution_y = 1000
    scene.render.filepath = PREVIEW.replace('.png', '_props.png')
    bpy.ops.render.render(write_still=True)
    print('PREVIEW', scene.render.filepath)
