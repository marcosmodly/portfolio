"""prep coding-gaming.json for use as the dark-theme hero.
- fix the Bodymovin export bug where the 'mensaje' chat-bubble layers ship
  with ip == op (lottie-web then never draws them): ip 0 / op 600 / st 0
- lift the handful of near-black shapes so they don't vanish on a dark page
  (lamp base, wrist band, hand crease, laptop base edge, plant veins, the
  pure-black chat bubble, and the backdrop blob's dark ends)
- the RGB laptop-screen gradient and the cyan lamp are left alone: they're the
  point of the 'gaming' variant and already read fine on dark.
Idempotent: safe to re-run on the committed file or a fresh raw export."""
import json, sys

SRC = sys.argv[1] if len(sys.argv) > 1 else 'coding-gaming.json'
DST = sys.argv[2] if len(sys.argv) > 2 else SRC


def key(*c):
    return tuple(round(x, 3) for x in c)


SOLID = {
    key(0.192, 0.165, 0.157): (0.80, 0.73, 0.66),   # wrist band
    key(0.267, 0.220, 0.208): (0.56, 0.47, 0.42),   # hand crease detail
    key(0.098, 0.161, 0.380): (0.40, 0.50, 0.86),   # laptop base edge
    key(0.412, 0.000, 0.349): (0.74, 0.47, 0.70),   # plant stem / veins
}

GRAD = {
    (key(0, 0, 0), key(0, 0, 0), key(0, 0, 0)):
        [(0.99, 0.91, 0.83), (0.98, 0.88, 0.80), (0.97, 0.85, 0.78)],   # black chat bubble
    (key(0.400, 0.400, 0.400), key(0.255, 0.255, 0.255), key(0.110, 0.110, 0.110)):
        [(0.67, 0.63, 0.59), (0.56, 0.52, 0.49), (0.45, 0.42, 0.40)],   # lamp base grey -> warm grey
    (key(0.078, 0.141, 0.867), key(0.663, 0.741, 0.969), key(0.114, 0.039, 0.467)):
        [(0.20, 0.33, 0.92), (0.71, 0.79, 0.99), (0.36, 0.28, 0.68)],   # backdrop blob
    (key(0.412, 0.337, 0.671), key(0.527, 0.498, 0.753), key(0.643, 0.659, 0.835)):
        [(0.52, 0.46, 0.77), (0.63, 0.61, 0.83), (0.75, 0.76, 0.91)],   # plant leaves
}

changed = {'fl': 0, 'st': 0, 'gf': 0, 'msg': 0}
warnings = []


def luma(r, g, b):
    return 0.299 * r + 0.587 * g + 0.114 * b


def remap_solid(item, kind):
    c = item['c']['k']
    k = key(c[0], c[1], c[2])
    if k in SOLID:
        c[0], c[1], c[2] = SOLID[k]
        changed[kind] += 1
    elif luma(*k) < 0.22 and item.get('o', {}).get('k', 100) > 40:
        warnings.append('%s left dark: %s' % (kind, k))


def remap_grad(item):
    g = item['g']['k']['k']
    p = item['g']['p']
    stops = tuple(key(g[i * 4 + 1], g[i * 4 + 2], g[i * 4 + 3]) for i in range(p))
    if stops in GRAD:
        for i, (r, gg, b) in enumerate(GRAD[stops]):
            g[i * 4 + 1], g[i * 4 + 2], g[i * 4 + 3] = r, gg, b
        changed['gf'] += 1
    else:
        dark = [s for s in stops if luma(*s) < 0.22]
        if dark:
            warnings.append('gradient left with dark stop(s) %s' % (dark,))


def walk(items):
    for item in items:
        ty = item.get('ty')
        if ty == 'gr':
            walk(item.get('it', []))
        elif ty == 'fl':
            remap_solid(item, 'fl')
        elif ty == 'st':
            remap_solid(item, 'st')
        elif ty == 'gf':
            remap_grad(item)


data = json.load(open(SRC))
for layer in data['layers']:
    if layer.get('ty') != 4:
        continue
    if 'mensaje' in layer.get('nm', ''):
        if layer.get('ip') == layer.get('op') or layer.get('hidden') is not None:
            layer['ip'], layer['op'], layer['st'] = 0, 600, 0
            layer.pop('hidden', None)
            changed['msg'] += 1
    walk(layer.get('shapes', []))

json.dump(data, open(DST, 'w'), separators=(',', ':'))
print('changed:', changed)
for w in warnings:
    print('WARNING:', w)
if not warnings:
    print('no dark colours left unmapped')
