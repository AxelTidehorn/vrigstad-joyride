// Joins the rendered shots and the soundtrack into media/teaser.mp4 (H.264 + AAC, 1920x1080, 30 fps).
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const ffmpeg = require('ffmpeg-static');
const shots = require('./shots');
const WORK = path.join(__dirname, '.work'), OUT = path.join(__dirname, '..', '..', 'media');

const all = path.join(WORK, 'all');
fs.rmSync(all, { recursive: true, force: true }); fs.mkdirSync(all, { recursive: true }); fs.mkdirSync(OUT, { recursive: true });
let k = 0;
for (const s of shots) for (let i = 0; i < s.n; i++) {
  const src = path.join(WORK, 'frames', s.name, String(i).padStart(4, '0') + '.jpg');
  if (!fs.existsSync(src)) throw new Error('missing frame ' + src + ' (run capture.js first)');
  fs.copyFileSync(src, path.join(all, String(k++).padStart(5, '0') + '.jpg'));
}
const out = path.join(OUT, 'teaser.mp4');
execFileSync(ffmpeg, ['-v', 'error', '-y', '-framerate', '30', '-i', path.join(all, '%05d.jpg'), '-i', path.join(WORK, 'audio.wav'),
  '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], { stdio: 'inherit' });
fs.rmSync(all, { recursive: true, force: true });
// short silent preview for the README (GitHub does not play repo videos inline): a few highlights, 640 px wide
const gif = path.join(OUT, 'teaser.gif'), cuts = [[4.2, 6.6], [15.5, 17.5], [18.5, 21], [22, 24.5], [28.3, 30.3], [45.2, 47.6]];
execFileSync(ffmpeg, ['-v', 'error', '-y', '-i', out, '-filter_complex',
  `select='${cuts.map(([a, b]) => `between(t,${a},${b})`).join('+')}',setpts=N/30/TB,fps=12,scale=640:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=4`,
  '-an', gif], { stdio: 'inherit' });
console.log(gif, (fs.statSync(gif).size / 1e6).toFixed(1) + ' MB');
console.log(out, k, 'frames', (k / 30).toFixed(1) + 's', (fs.statSync(out).size / 1e6).toFixed(1) + ' MB');
