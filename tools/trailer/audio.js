// Synthesises the teaser's soundtrack to .work/audio.wav. Everything is generated here from oscillators and noise,
// so there is no third-party music or samples to license. Cues are timed from the shot list and .work/meta.json.
const fs = require('fs');
const path = require('path');
const shots = require('./shots');
const WORK = path.join(__dirname, '.work');
const meta = JSON.parse(fs.readFileSync(path.join(WORK, 'meta.json'), 'utf8'));

const SR = 44100, FPS = 30;
const at = {}; let total = 0;
for (const s of shots) { at[s.name] = total / FPS; total += s.n; }
const END = total / FPS, N = Math.ceil(END * SR);
const L = new Float32Array(N), R = new Float32Array(N);
const ev = (shot, key, fallback) => at[shot] + ((meta[shot] && meta[shot][key] != null ? meta[shot][key] : fallback) / FPS);

let seed = 12345; const rnd = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296 * 2 - 1; };
const TAU = Math.PI * 2;
// render a voice: fn(t, i) returns a sample for t seconds after t0
function voice(t0, dur, gain, pan, fn) {
  const a = Math.max(0, Math.floor(t0 * SR)), b = Math.min(N, Math.floor((t0 + dur) * SR)), gl = gain * Math.min(1, 1 - pan), gr = gain * Math.min(1, 1 + pan);
  for (let i = a; i < b; i++) { const s = fn((i - a) / SR, i - a); L[i] += s * gl; R[i] += s * gr; }
}
const lp = cutoff => { let y = 0; const k = 1 - Math.exp(-TAU * cutoff / SR); return x => (y += (x - y) * k); };
const saw = ph => 2 * (ph - Math.floor(ph + 0.5));
const sq = ph => (ph - Math.floor(ph)) < 0.5 ? 1 : -1;

const kick = (t, g = 1) => { let ph = 0; voice(t, 0.32, 0.9 * g, 0, x => { ph += (46 + 110 * Math.exp(-x * 34)) / SR; return Math.sin(TAU * ph) * Math.exp(-x * 11); }); };
const snare = (t, g = 1) => { const f = lp(1800); voice(t, 0.2, 0.42 * g, 0.05, x => { const n = rnd(); return (n - f(n)) * Math.exp(-x * 26) + Math.sin(TAU * 185 * x) * Math.exp(-x * 40) * 0.5; }); };
const hat = (t, g = 1, open = false) => { const f = lp(6500); voice(t, open ? 0.16 : 0.05, 0.16 * g, 0.3, x => { const n = rnd(); return (n - f(n)) * Math.exp(-x * (open ? 22 : 90)); }); };
const bass = (t, dur, hz, g = 1) => { const f = lp(320); let ph = 0; voice(t, dur, 0.34 * g, 0, x => { ph += hz / SR; return f(saw(ph) * 0.7 + sq(ph * 0.5) * 0.3) * Math.min(1, x * 400) * Math.exp(-x * 5) * Math.min(1, (dur - x) * 200); }); };
const pluck = (t, hz, g = 1, pan = 0) => { const f = lp(2400); let ph = 0; voice(t, 0.24, 0.11 * g, pan, x => { ph += hz / SR; return f(sq(ph) * 0.5 + saw(ph * 1.003) * 0.5) * Math.min(1, x * 600) * Math.exp(-x * 16); }); };
const pad = (t, dur, freqs, g = 1, attack = 1.5, release = 1) => { for (const [j, hz] of freqs.entries()) for (const det of [-0.0025, 0.0025]) {
  const f = hz * (1 + det), trem = 0.13 + j * 0.05; voice(t, dur, 0.05 * g, det > 0 ? 0.35 : -0.35, x => Math.sin(TAU * f * x) * Math.min(1, x / attack) * Math.min(1, (dur - x) / release) * (0.8 + 0.2 * Math.sin(TAU * trem * x))); } };
const impact = (t, g = 1) => { let ph = 0; const f = lp(700); voice(t, 1.6, 0.85 * g, 0, x => { ph += (34 + 30 * Math.exp(-x * 9)) / SR; return Math.sin(TAU * ph) * Math.exp(-x * 3.2) + f(rnd()) * Math.exp(-x * 7) * 0.7; }); };
const riser = (t, dur, g = 1) => { let y = 0; voice(t, dur, 0.2 * g, 0, x => { const k = x / dur, n = rnd(); y += (n - y) * (0.02 + 0.5 * k * k); return (n - y * (1 - k)) * k * k; }); };
const sweep = (t, dur, f0, f1, g = 1) => { let ph = 0; voice(t, dur, 0.3 * g, 0, x => { const k = x / dur; ph += (f0 * Math.pow(f1 / f0, k)) / SR; return Math.sin(TAU * ph) * (1 - k) * Math.min(1, x * 200); }); };
const brass = (t, dur, hz, g = 1, vib = 0, fall = 0) => { const f = lp(950); let ph = 0; voice(t, dur, 0.26 * g, -0.1, x => { const k = x / dur; ph += hz * (1 + vib * Math.sin(TAU * 5.5 * x) * k) * (1 - fall * k * k) / SR;
  return f(saw(ph)) * Math.min(1, x * 40) * Math.min(1, (dur - x) * 14); }); };
const stab = (t, freqs, g = 1) => { for (const hz of freqs) { const f = lp(1700); let ph = 0; voice(t, 0.16, 0.07 * g, 0.2, x => { ph += hz / SR; return f(sq(ph)) * Math.min(1, x * 500) * Math.exp(-x * 20); }); } };
const scratch = (t, dur, g = 1) => { const f = lp(3200); voice(t, dur, 0.13 * g, 0.1, x => { const n = rnd(); return (n - f(n)) * Math.pow(Math.abs(Math.sin(TAU * 6.5 * x)), 3) * Math.min(1, (dur - x) * 30); }); };
const ding = (t, g = 1) => { for (const hz of [880, 1108.73, 1318.5]) voice(t, 1.4, 0.07 * g, 0.2, x => Math.sin(TAU * hz * x) * Math.exp(-x * 3.4) * Math.min(1, x * 300)); };
const siren = (t, dur, g = 1) => { let ph = 0; const f = lp(1400); voice(t, dur, 0.1 * g, -0.25, x => { ph += (760 + 190 * Math.sin(TAU * 1.1 * x)) / SR; return f(saw(ph) * 0.5 + Math.sin(TAU * ph)) * Math.min(1, x / dur * 1.6) * Math.min(1, (dur - x) * 40); }); };

const BEAT = 0.5, A = 55;
const CH = [   // [bass root, arpeggio notes] per bar: Am, Am, F, G, Am, E
  [A, [440, 523.25, 659.25, 523.25]], [A, [440, 523.25, 659.25, 880]], [43.65, [440, 523.25, 698.46, 523.25]],
  [49, [392, 493.88, 587.33, 493.88]], [A, [440, 523.25, 659.25, 523.25]], [41.2, [415.3, 493.88, 659.25, 493.88]]];
// full groove from t0 for a number of beats, skipping anything that starts inside a muted span
function groove(t0, beats, muted = [], g = 1) {
  const off = t => muted.some(([a, b]) => t >= a - 1e-6 && t < b - 1e-6);
  for (let b = 0; b < beats; b++) { const t = t0 + b * BEAT, [root, arp] = CH[Math.floor(b / 4) % CH.length];
    if (off(t)) continue;
    kick(t, g); if (b % 2) snare(t, g);
    for (let e = 0; e < 2; e++) { const te = t + e * BEAT / 2; hat(te, e ? 1 : 0.6, e === 1 && b % 4 === 3); bass(te, BEAT / 2 - 0.01, root * (e ? 2 : 1), g); }
    for (let s = 0; s < 4; s++) pluck(t + s * BEAT / 4, arp[(b * 4 + s) % 4] * (s === 3 && b % 2 ? 2 : 1), g * (s % 2 ? 0.7 : 1), s % 2 ? 0.45 : -0.45); }
}

// --- A. open, aerial, Torget: a quiet drone, with a tick creeping in as the Volvo comes into view
const tSteal = ev('04_steal', '_', 22);
pad(0, tSteal + 0.2, [110, 164.81, 220, 261.63], 1, 2.5, 0.25);
pad(at['02_aerial'], tSteal + 0.2 - at['02_aerial'], [329.63, 493.88], 0.5, 3, 0.25);
for (let t = at['03_torget']; t < tSteal - 0.05; t += BEAT / 2) hat(t, 0.25 + 0.6 * (t - at['03_torget']) / (tSteal - at['03_torget']));

// --- B. the theft: a hit, then the pulse builds into the chase
impact(tSteal, 1);
const tChase = at['05_chase_front'];
for (let t = Math.ceil((tSteal + 0.3) / (BEAT / 2)) * (BEAT / 2), n = 0; t < tChase - 1e-6; t += BEAT / 2, n++) { const k = (t - tSteal) / (tChase - tSteal);
  bass(t, BEAT / 2 - 0.01, n % 2 ? 110 : 55, 0.35 + 0.65 * k); if (k > 0.3 && Math.abs(t / BEAT - Math.round(t / BEAT)) < 1e-6) kick(t, 0.5 + 0.5 * k); hat(t, 0.5 + 0.5 * k); }
riser(tChase - 2, 2, 1);
for (let s = 0; s < 4; s++) snare(tChase - 0.5 + s * 0.125, 0.5 + s * 0.15);

// --- C. the chase: full groove, dropping out under each title card
const tEpa = at['12_epa'], cards = ['06_card', '08_card', '10_card'].map(c => [at[c], at[c] + 1]);
groove(tChase, Math.round((tEpa - tChase) / BEAT), cards);
for (const [a, b] of cards) { impact(a, 0.8); riser(b - 0.5, 0.5, 0.7); }

// --- D. EPA-traktor: the music gives up and an oom-pah takes over at walking pace
sweep(tEpa, 0.45, 520, 55, 1);
for (let b = 1; b < 8; b++) { const t = tEpa + b * BEAT; if (b % 2) brass(t, 0.36, b % 4 === 1 ? 110 : 82.41, 1.1); else stab(t, [220, 277.18, 329.63], 1.3); }

// --- E. trisslott: scratching, then the sound of losing
const tScr = ev('13_triss', '_', 10), tRes = at['13_triss'] + ((meta['13_triss'] && meta['13_triss'].toasts && meta['13_triss'].toasts[1] ? meta['13_triss'].toasts[1][0] : 36) / FPS);
scratch(tScr, tRes - tScr, 1);
[[233.08, 0.4], [220, 0.4], [207.65, 0.4], [196, 1.3]].reduce((t, [hz, d], j) => { brass(t, d - 0.03, hz, 1, j === 3 ? 0.012 : 0, j === 3 ? 0.06 : 0); return t + d; }, tRes + 0.1);

// --- F. safehouse: heartbeat while lying low, a bell when the police give up
const tSafe = at['14_safe'], tClear = ev('14_safe', 'cleared', 119);
pad(tSafe, tClear - tSafe + 0.3, [110, 164.81, 207.65], 0.8, 1, 0.3);
for (let t = tSafe + 0.25; t < tClear - 0.3; t += 1) { kick(t, 0.5); kick(t + 0.2, 0.36); }
ding(tClear, 1);

// --- G. Gripen: sirens close in, then the bust
const tGrip = at['15_gripen'], tBust = ev('15_gripen', 'busted', 44);
siren(tGrip, tBust - tGrip, 1);
for (let t = tGrip, n = 0; t < tBust - 0.05; t += BEAT / 2, n++) { kick(t, 0.6 + 0.3 * (t - tGrip) / (tBust - tGrip)); hat(t + BEAT / 4, 0.8); }
impact(tBust, 1.1); sweep(tBust, 0.9, 620, 70, 0.8);

// --- H. title: the theme comes back for two bars and rings out
const tTitle = at['16_title'];
impact(tTitle, 1); groove(tTitle, 8); impact(tTitle + 4, 0.9);
pad(tTitle, END - tTitle, [110, 164.81, 220, 261.63, 329.63], 1.2, 0.4, 1.8);

// master: soft clip, normalise, short fades
let peak = 0; for (let i = 0; i < N; i++) { L[i] = Math.tanh(L[i] * 1.15); R[i] = Math.tanh(R[i] * 1.15); peak = Math.max(peak, Math.abs(L[i]), Math.abs(R[i])); }
const norm = 0.89 / (peak || 1), fade = Math.floor(0.5 * SR);
const out = Buffer.alloc(44 + N * 4);
out.write('RIFF', 0); out.writeUInt32LE(36 + N * 4, 4); out.write('WAVEfmt ', 8); out.writeUInt32LE(16, 16); out.writeUInt16LE(1, 20); out.writeUInt16LE(2, 22);
out.writeUInt32LE(SR, 24); out.writeUInt32LE(SR * 4, 28); out.writeUInt16LE(4, 32); out.writeUInt16LE(16, 34); out.write('data', 36); out.writeUInt32LE(N * 4, 40);
for (let i = 0; i < N; i++) { const g = norm * Math.min(1, i / 400, (N - i) / fade);
  out.writeInt16LE(Math.round(Math.max(-1, Math.min(1, L[i] * g)) * 32767), 44 + i * 4); out.writeInt16LE(Math.round(Math.max(-1, Math.min(1, R[i] * g)) * 32767), 46 + i * 4); }
fs.writeFileSync(path.join(WORK, 'audio.wav'), out);
console.log('audio.wav', END.toFixed(1) + 's', 'peak before normalise', peak.toFixed(2));
