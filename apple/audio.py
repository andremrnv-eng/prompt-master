import numpy as np, subprocess, sys, json
from scipy.signal import butter, sosfilt, fftconvolve
SR = 48000; DUR = 55.6; N = int(SR * DUR)
rng = np.random.default_rng(5)
HERE = sys.argv[1]

def t_(d): return np.arange(int(d * SR)) / SR
def bp(x, lo, hi, o=2): return sosfilt(butter(o, [lo, hi], 'band', fs=SR, output='sos'), x)
def lp(x, f, o=2): return sosfilt(butter(o, f, 'low', fs=SR, output='sos'), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, 'high', fs=SR, output='sos'), x)
def place(buf, x, at, g=1.0, pan=0.0):
    i = int(at * SR)
    if i >= len(buf): return
    x = x[:len(buf) - i]
    l = np.cos((pan + 1) * np.pi / 4); r = np.sin((pan + 1) * np.pi / 4)
    buf[i:i + len(x), 0] += x * g * l * 1.414; buf[i:i + len(x), 1] += x * g * r * 1.414
def env(n, a, d):
    t = np.arange(n) / SR; return np.minimum(t / max(a, 1e-4), 1) * np.exp(-t / d)
def mtof(m): return 440 * 2 ** ((m - 69) / 12)

# ---------- instruments
def pluck(f, dur=1.6, bright=1.0):
    t = t_(dur); y = np.zeros_like(t)
    for h in range(1, 9):
        if f * h > 12000: break
        y += (1 / h ** (1.3 / bright)) * np.sin(2 * np.pi * f * h * t + h) * np.exp(-t * (2.2 + h * 1.6))
    y *= np.minimum(t / .004, 1)
    return y * .5
def bell(f, dur=2.5):
    t = t_(dur); y = np.zeros_like(t)
    for r, a, d in [(1, 1, 1.4), (2.76, .45, .7), (5.4, .25, .35), (8.93, .12, .2)]:
        y += a * np.sin(2 * np.pi * f * r * t) * np.exp(-t / d)
    return y * np.minimum(t / .002, 1) * .35
def pad(freqs, dur, att=.8, rel=1.0):
    t = t_(dur); y = np.zeros_like(t)
    for f in freqs:
        for det in (-.12, .12):
            ff = f * 2 ** (det / 12)
            for h, a in [(1, 1), (2, .35), (3, .15), (4, .07)]:
                y += a * np.sin(2 * np.pi * ff * h * t + rng.random() * 6)
    e = np.minimum(t / att, 1) * np.minimum((dur - t) / rel, 1).clip(0, 1)
    return lp(y * e, 2200) * .05
def kick():
    t = t_(.45); f = 45 + 80 * np.exp(-t * 30); ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 9) * .9
def shaker():
    n = int(.07 * SR); return lp(hp(rng.standard_normal(n), 5000), 10000, 4) * env(n, .003, .018) * .16
def bass(f, dur):
    t = t_(dur); return (np.sin(2 * np.pi * f * t) + .25 * np.sin(4 * np.pi * f * t)) * np.minimum(t / .01, 1) * np.exp(-t * 1.2) * .45

# ---------- music
mus = np.zeros((N, 2))
def chord_notes(name):
    C = {'Am': [57, 60, 64], 'F': [53, 57, 60], 'E': [52, 56, 59], 'C': [48, 52, 55], 'G': [55, 59, 62], 'Dm': [50, 53, 57],
         'Am9': [57, 60, 64, 71], 'Fmaj7': [53, 57, 60, 64], 'Csus': [48, 55, 60, 62]}
    return C[name]
BEAT = .625; BAR = 2.5
# section A: 0 - 7.45 (minor, sparse)
for st, ch, ln in [(0, 'Am', 2.5), (2.5, 'F', 2.5), (5.0, 'E', 2.45)]:
    ns = chord_notes(ch); place(mus, pad([mtof(n) for n in ns], ln + .6, .6, .5), st, 1.0)
    place(mus, bass(mtof(ns[0] - 12), ln), st, .8)
    for k in range(int(ln / (BEAT / 2))):
        n = [ns[0], ns[2], ns[1] + 12, ns[2]][k % 4] + 12 * (k % 8 >= 4)
        place(mus, pluck(mtof(n), 1.2, .8), st + k * BEAT / 2, .18 if k % 2 else .26, pan=.3 * np.sin(k))
# tape stop on A tail handled by fade: apply fade 7.3-7.5
i0, i1 = int(7.3 * SR), int(7.5 * SR); mus[i0:i1] *= np.linspace(1, 0, i1 - i0)[:, None]; mus[i1:] = 0
# section B: 8.45 - 44.25 (major groove)
prog = ['C', 'G', 'Am', 'F']
b0 = 8.45; nb = int(np.ceil((44.25 - b0) / BAR))
for b in range(nb):
    st = b0 + b * BAR; ch = prog[b % 4]; ns = chord_notes(ch); ln = min(BAR, 44.3 - st)
    if ln <= 0: break
    place(mus, pad([mtof(n) for n in ns], ln + .5, .5, .4), st, .9)
    place(mus, bass(mtof(ns[0] - 12), BEAT * 1.5), st, .9); place(mus, bass(mtof(ns[0] - 12), BEAT), st + BEAT * 2, .7)
    place(mus, bass(mtof(ns[2] - 24), BEAT), st + BEAT * 3, .6)
    for k in range(8):
        tt = st + k * BEAT / 2
        if tt > 44.2: break
        n = [ns[0] + 12, ns[2] + 12, ns[1] + 12, ns[2] + 12, ns[0] + 24, ns[2] + 12, ns[1] + 12, ns[2]][k]
        place(mus, pluck(mtof(n), 1.0), tt, .2 if k % 2 else .27, pan=.35 * np.sin(k * 1.3))
    drums = b >= 1 and not (31.3 < st < 35.4)  # drop drums during macro close-up
    for k in range(4):
        tt = st + k * BEAT
        if tt > 44.2: break
        if drums and k in (0, 2): place(mus, kick(), tt, .55)
        if b >= 2:
            for j in range(4): place(mus, shaker(), tt + j * BEAT / 4, .55 if j % 2 else .3, pan=.4)
# section C: winter 44.25 - 49.12
place(mus, pad([mtof(n) for n in chord_notes('Am9')], 4.9, 1.0, .8), 44.25, 1.1)
for k, n in enumerate([81, 76, 79, 84, 81, 76, 79]):
    place(mus, bell(mtof(n), 2.0), 44.4 + k * .66, .22, pan=.5 * np.sin(k * 2))
# riser through flips
t = t_(1.05); rs = bp(rng.standard_normal(len(t)), 800, 6000) * (t / 1.05) ** 2 * .25; place(mus, rs, 48.05, 1.0)
# section D: spring 49.12 - end
for st, ch, ln in [(49.12, 'Fmaj7', 1.5), (50.62, 'G', 1.53), (52.15, 'Csus', 3.45)]:
    ns = chord_notes(ch); place(mus, pad([mtof(n) for n in ns], ln + (1.2 if ch == 'Csus' else .4), .3, 1.4 if ch == 'Csus' else .3), st, 1.0)
    place(mus, bass(mtof(ns[0] - 12), ln), st, .9)
    step = BEAT / 2
    for k in range(int(ln / step)):
        n = ns[k % len(ns)] + 12 + 12 * (k // len(ns) % 2)
        place(mus, pluck(mtof(n), 1.4), st + k * step, .24, pan=.4 * np.sin(k))
    if ch != 'Csus':
        for k in range(int(ln / BEAT)): place(mus, kick(), st + k * BEAT, .45)
place(mus, bell(mtof(84), 3.0), 52.15, .35); place(mus, bell(mtof(79), 3.0), 52.16, .25, pan=-.3)
# end fade
i0 = int(54.6 * SR); mus[i0:] *= np.linspace(1, 0, N - i0)[:, None] ** 1.5

# ---------- SFX
sfx = np.zeros((N, 2))
def noise(d): return rng.standard_normal(int(d * SR))
def whoosh(d=.6, lo=300, hi=3000, g=.5):
    n = int(d * SR); t = np.arange(n) / n; y = bp(noise(d), lo, hi) * np.sin(np.pi * t) ** 2; return y * g
def thud(g=1.0, f=70):
    t = t_(.35); y = np.sin(2 * np.pi * (f + 40 * np.exp(-t * 25)) * t) * np.exp(-t * 14) + lp(noise(.35), 900) * np.exp(-t * 25) * .5; return y * g
def crack():
    t = t_(.25); return (hp(noise(.25), 1500) * np.exp(-t * 30) + bp(noise(.25), 300, 1200) * np.exp(-t * 18)) * .6
def sawstroke():
    d = .32; t = t_(d); am = (np.abs(np.sin(2 * np.pi * 9 * t))) ** 1.5
    return bp(noise(d), 1800, 5200) * am * np.sin(np.pi * t / d) * .35
def tick(f=2200, g=.3):
    t = t_(.06); return np.sin(2 * np.pi * f * t) * np.exp(-t * 80) * g
def pop(f=600, g=.35):
    t = t_(.12); fr = f * (1 + 1.5 * t / .12); return np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 35) * g
def snip():
    a = hp(noise(.03), 3000) * env(int(.03 * SR), .001, .006); b = np.zeros(int(.09 * SR)); b[:len(a)] = a; b[int(.05 * SR):int(.05 * SR) + len(a)] += a * .8; return b * .7
def ping(f=1320, g=.25): return bell(f, 1.2) * g * 2
def paper():
    d = .22; t = t_(d); return bp(noise(d), 1500, 7000) * np.exp(-t * 14) * (1 + np.sin(2 * np.pi * 30 * t)) * .18
def type_click():
    t = t_(.05); return (hp(noise(.05), 2500) * np.exp(-t * 120) + np.sin(2 * np.pi * 180 * t) * np.exp(-t * 60) * .5) * .35
def knock(f=220):
    t = t_(.3); return (np.sin(2 * np.pi * f * t) + .5 * np.sin(2 * np.pi * f * 2.3 * t)) * np.exp(-t * 18) * .5

# scene 1
place(sfx, thud(.55, 55), .30)  # title slam
for k in range(6):
    hop = .55 + k * .42
    place(sfx, whoosh(.18, 900, 4000, .12), hop - .1, pan=.3)
    place(sfx, sawstroke(), hop + .1, .9, pan=.2 * (k % 2 * 2 - 1))
    place(sfx, tick(1700, .22), hop + .18)
place(sfx, thud(.8, 48), 1.85); t = t_(.8); place(sfx, np.sin(2 * np.pi * 110 * t) * np.sign(np.sin(2 * np.pi * 7 * t)) * np.exp(-t * 3) * .08, 1.9)
# chop + falls
place(sfx, crack(), 3.35, 1.2); place(sfx, whoosh(.7, 200, 2000, .5), 3.35)
for k, tt in enumerate([4.02, 4.12, 4.2, 4.33, 4.4, 4.52]): place(sfx, thud(.6, 60 + k * 6), tt, pan=(k % 3 - 1) * .5)
for k in range(12):
    tt = 4.62 + k * .11 + rng.random() * .05; place(sfx, pop(500 + k * 40, .22), tt, pan=np.sin(k) * .6)
place(sfx, pop(900, .4), 6.2); place(sfx, whoosh(.25, 1500, 6000, .3), 6.45)
# rewind
d = 1.0; t = t_(d); fr = 300 + 2400 * (t / d) ** 2; rw = np.sin(2 * np.pi * np.cumsum(fr) / SR) * .08 + bp(noise(d), 500, 5000) * .3
place(sfx, rw[::-1] * np.sin(np.pi * t / d), 7.45, 1.0)
for k in range(3): place(sfx, tick(1400 + k * 300, .3), 8.1 + k * .22)
for tt in (11.74, 18.55, 24.22): place(sfx, ping(1046, .2), tt)
# year 1
place(sfx, tick(2000, .3), 14.55); place(sfx, sawstroke(), 15.65, 1.0); place(sfx, crack(), 15.95, .7)
place(sfx, whoosh(.9, 200, 1500, .35), 16.0); place(sfx, thud(.8, 55), 16.97); place(sfx, whoosh(1.0, 400, 2500, .12), 16.15)
# year 2
place(sfx, ping(1568, .18), 19.5); place(sfx, ping(1397, .18), 21.95)
for k in range(5): place(sfx, whoosh(.35, 2000, 8000, .12), 22.75 + k * .22, pan=(k % 2 - .5))
# year 3
place(sfx, whoosh(.5, 600, 4000, .2), 26.95)
for k in range(5):
    place(sfx, tick(1900, .2), 26.9 + k * .1); place(sfx, snip(), 27.85 + k * .11, pan=(k % 2 * 2 - 1) * .4)
    place(sfx, thud(.35, 70), 28.7 + k * .11 + rng.random() * .08, pan=(k % 2 * 2 - 1) * .4)
place(sfx, tick(2400, .25), 28.05)
# rule pie
place(sfx, whoosh(.5, 400, 3000, .25), 29.05)
d = .83; t = t_(d); place(sfx, np.sin(2 * np.pi * np.cumsum(500 + 500 * t / d) / SR) * .05 * np.sin(np.pi * t / d), 30.12); place(sfx, ping(1760, .22), 30.95)
# macro
place(sfx, whoosh(1.1, 150, 2500, .6), 31.3); place(sfx, knock(180), 32.3); place(sfx, tick(2600, .25), 32.35)
for k in range(4): place(sfx, bp(noise(.22), 1200, 5000) * np.sin(np.pi * t_(.22) / .22) * .22, 33.85 + k * .22, pan=(k % 2 - .5))
place(sfx, whoosh(1.4, 200, 3000, .55), 35.2)
# young
place(sfx, tick(2000, .25), 38.45); place(sfx, snip(), 39.55); place(sfx, thud(.25, 90), 40.1); place(sfx, tick(2400, .2), 38.65)
for k in range(4): place(sfx, pop(700 + 60 * k, .25), 41.25 + k * .28)
for k in range(3): place(sfx, pop(900 + 60 * k, .22), 42.55 + k * .25)
place(sfx, tick(2400, .2), 41.55); place(sfx, tick(2600, .2), 42.25)
# winter
place(sfx, whoosh(.7, 300, 3000, .4), 44.2); place(sfx, paper(), 44.85); place(sfx, thud(.6, 50), 44.3)
place(sfx, bp(noise(.35), 2000, 6000) * np.sin(np.pi * t_(.35) / .35) * .25, 45.3)
d = 4.6; t = t_(d); wind = bp(noise(d), 300, 1500) * (.5 + .5 * np.sin(2 * np.pi * .4 * t)) * np.sin(np.pi * t / d) ** .5 * .12; place(sfx, wind, 44.4)
for tt in (48.08, 48.33, 48.58, 48.83): place(sfx, paper(), tt, 1.1)
place(sfx, ping(1318, .25), 49.0)
for k in range(8): place(sfx, pop(1200 + k * 80, .1), 49.4 + k * .18, pan=np.sin(k) * .5)
place(sfx, whoosh(.7, 300, 3000, .3), 50.55)
# spring finale
for k in range(10): place(sfx, bell(mtof(84 + [0, 4, 7, 12, 7][k % 5]), 1.2) * .25, 51.4 + k * .14, pan=np.sin(k * 1.7) * .6)
place(sfx, knock(150), 52.2); place(sfx, whoosh(.5, 300, 2500, .3), 51.95)
for k in range(16): place(sfx, type_click(), 52.85 + k * .075 + rng.random() * .01)
place(sfx, bell(mtof(91), 1.5) * .5, 54.1)

# ---------- voice + ducking
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', HERE + '/voice.wav', '-ar', str(SR), '-ac', '1', '-f', 'f32le', '-'], capture_output=True).stdout
voice = np.frombuffer(raw, dtype=np.float32).astype(np.float64)
v = np.zeros(N); v[:min(N, len(voice))] = voice[:N]
e = np.sqrt(np.convolve(v ** 2, np.ones(2400) / 2400, 'same')); e = e / (e.max() + 1e-9)
duck = np.clip(e * 3, 0, 1); duck = np.convolve(duck, np.ones(9600) / 9600, 'same')  # 200ms smoothing
mus *= (1 - .5 * duck)[:, None]
def norm(x, peak): return x / (np.abs(x).max() + 1e-9) * peak
mus = norm(mus, 10 ** (-11 / 20)); sfx = norm(sfx, 10 ** (-7 / 20))
mix = mus + sfx + np.stack([v, v], 1) * 0.95
mix = np.tanh(mix * 1.1) / np.tanh(1.1)
mix = norm(mix, 10 ** (-1 / 20))
for name, x in [('mix', mix), ('music', mus), ('sfx', sfx)]:
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '-', HERE + f'/{name}.wav'], input=x.astype(np.float32).tobytes())
print('done', mix.shape)
