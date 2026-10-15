/* Frame capture: renders an animated web page one frame at a time against a
 * hand-stepped clock, so output is frame-exact and does not depend on machine
 * speed. Run it from the directory where `npm i playwright` was done.
 *
 *   node capture.mjs --page page/index.html --seek seek.js \
 *        [--css video.css] [--start '#startBtn'] [--ready "typeof THREE!=='undefined'"] \
 *        [--after-setup "setQuality('high', true)"] [--route '**\/three.min.js=vendor/three.min.js'] \
 *        [--timeline timeline.json] [--fps 30] [--w 1280] [--h 720] [--dsf 2] \
 *        [--from 0] [--to <end>] [--out frames] [--quality 94] [--seed N] [--headless] [--swiftshader]
 *
 * Page contract (the --seek script must provide it; see examples/seek.example.js):
 *   window.__setup()   stop the live loop, return {total, scenes, durs?}  (seconds)
 *   window.__starts    array of scene start times in seconds
 *   window.__seek(t, fps)  render exactly the picture for film time t, once
 *
 * Frames are written as f%06d.jpg numbered by ABSOLUTE film position
 * (frame = round(seconds * fps)). --from 55 at 30 fps therefore starts at
 * f001650.jpg, not f000000.jpg. Existing frames are skipped, so an interrupted
 * run resumes. The same rule means stale frames from an earlier page version or
 * different flags are silently reused: use a clean --out when anything changed.
 */
import fs from 'fs';
import path from 'path';
import { createRequire } from 'module';

// resolve playwright from the working directory, not from this script's folder
const { chromium } = createRequire(path.join(process.cwd(), 'noop.js'))('playwright');

const argv = process.argv.slice(2);
const flag = (k) => argv.includes('--' + k);
const arg = (k, d) => { const i = argv.indexOf('--' + k);
  if (i < 0) return d;
  const v = argv[i + 1];
  return v !== undefined && !v.startsWith('--') ? v : true; };
const args = (k) => argv.flatMap((a, i) => a === '--' + k ? [argv[i + 1]] : []);

const need = (k) => { const v = arg(k); if (!v || v === true) { console.error(`missing --${k}`); process.exit(1); } return v; };

const FPS  = +arg('fps', 30);
const W    = +arg('w', 1280);
const H    = +arg('h', 720);
const DSF  = +arg('dsf', 2);            // 2 => supersampled; downscale at encode
const Q    = +arg('quality', 94);
const OUT  = path.resolve(arg('out', 'frames'));
const PAGE = path.resolve(need('page'));
const SEEK = path.resolve(need('seek'));
const CSS  = arg('css') ? path.resolve(arg('css')) : null;
const TIMELINE = arg('timeline') ? path.resolve(arg('timeline')) : null;
const MIME = { '.js': 'application/javascript', '.css': 'text/css', '.json': 'application/json',
               '.woff2': 'font/woff2', '.woff': 'font/woff', '.ttf': 'font/ttf', '.png': 'image/png',
               '.jpg': 'image/jpeg', '.svg': 'image/svg+xml' };

fs.mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch({
  headless: flag('headless'),           // headed is the default: headless often falls back to software GL
  args: ['--no-sandbox', '--hide-scrollbars', '--disable-background-networking',
         '--mute-audio', '--force-color-profile=srgb', '--font-render-hinting=none',
         // only for a machine with no usable GPU; about 50x slower
         ...(flag('swiftshader')
             ? ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] : [])]
});
const ctx = await browser.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: DSF });

// serve local files for URL patterns so the render is offline and reproducible
for (const r of args('route')) {
  const eq = r.lastIndexOf('=');
  const pattern = r.slice(0, eq), file = path.resolve(r.slice(eq + 1));
  await ctx.route(pattern, route => route.fulfill({
    path: file, contentType: MIME[path.extname(file)] || 'application/octet-stream' }));
}

// A page that calls Math.random() unseeded gives a different layout on every
// page load, so two runs (or a resumed run) do not match. --seed N replaces
// Math.random with a seeded generator before any page script runs.
if (arg('seed') !== undefined) {
  await ctx.addInitScript((seed) => {
    let a = seed >>> 0;
    Math.random = () => {                    // mulberry32
      a = (a + 0x6D2B79F5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }, +arg('seed'));
}

const page = await ctx.newPage();
page.on('pageerror', e => console.error('PAGEERROR', e.message));
await page.goto('file://' + PAGE, { waitUntil: 'load' });
if (arg('ready')) await page.waitForFunction(arg('ready'));
try { await page.evaluate(() => document.fonts.ready); } catch (e) {}
await page.waitForTimeout(1200);

if (arg('start')) {
  await page.click(arg('start'));
  await page.waitForTimeout(900);
}
if (CSS) await page.addStyleTag({ path: CSS });
await page.addScriptTag({ path: SEEK });
const meta = await page.evaluate(() => window.__setup());
if (arg('after-setup')) await page.evaluate(arg('after-setup'));
await page.waitForTimeout(600);

// the page's scene durations and the timeline used for audio must agree
if (TIMELINE) {
  const tl = JSON.parse(fs.readFileSync(TIMELINE, 'utf8')).scenes.map(s => s.dur);
  if (!meta.durs) console.warn('WARNING: __setup() returned no durs; cannot compare with --timeline');
  else {
    const bad = tl.map((d, i) => [i + 1, d, meta.durs[i]]).filter(([, d, p]) => !(Math.abs(d - p) < 0.05));
    if (tl.length !== meta.durs.length || bad.length) {
      console.error(`TIMELINE MISMATCH: timeline has ${tl.length} scenes, page has ${meta.durs.length}.`,
        bad.slice(0, 5).map(([n, d, p]) => `scene ${n}: timeline ${d}s, page ${p}s`).join('; '));
      await browser.close(); process.exit(2);
    }
  }
}

const TOTAL  = meta.total;
const FROM   = Math.max(0, Math.round(+arg('from', 0) * FPS));
const TO     = Math.min(Math.round(TOTAL * FPS), Math.round(+arg('to', TOTAL) * FPS));
const NFRAME = TO - FROM;

console.log(`${meta.scenes} scenes, ${TOTAL.toFixed(1)}s -> frames ${FROM}..${TO - 1} `
          + `(${NFRAME}) at ${FPS}fps, ${W * DSF}x${H * DSF}`);

// warm every scene once so first-frame shader compiles do not show up in the film
for (let i = 0; i < meta.scenes; i++) {
  await page.evaluate(([j, f]) => window.__seek(window.__starts[j] + 0.4, f), [i, FPS]);
  await page.screenshot({ type: 'jpeg', quality: 60 });
}

const t0 = Date.now();
let done = 0;
for (let n = FROM; n < TO; n++) {
  const file = path.join(OUT, 'f' + String(n).padStart(6, '0') + '.jpg');
  if (fs.existsSync(file)) { done++; continue; }
  await page.evaluate(([gt, f]) => window.__seek(gt, f), [n / FPS, FPS]);
  await page.screenshot({ path: file, type: 'jpeg', quality: Q });
  done++;
  if (done % 60 === 0) {
    const el = (Date.now() - t0) / 1000, rate = done / el;
    process.stdout.write(`\r  ${done}/${NFRAME}  ${rate.toFixed(1)} fps  `
      + `eta ${Math.round((NFRAME - done) / rate / 60)} min   `);
  }
}
console.log(`\ndone in ${((Date.now() - t0) / 60000).toFixed(1)} min -> ${OUT}`);
await browser.close();
