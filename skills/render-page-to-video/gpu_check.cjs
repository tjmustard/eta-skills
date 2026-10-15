#!/usr/bin/env node
/* Is headed Chromium (via Playwright) really using the GPU for WebGL?
 *
 *   node gpu_check.cjs          # run from the directory where `npm i playwright` was done
 *
 * Exit code 0 = hardware, 2 = software or unknown. Read the printed lines too.
 *
 * Do NOT do this instead:
 *   await page.goto('chrome://gpu'); (await page.content()).match(WebGL-label regex)
 * chrome://gpu builds its report inside shadow DOM, so page.content() has no
 * "WebGL: ..." text and the match returns `undefined`. `undefined` there means
 * "the regex found nothing", not "no GPU". This script walks the shadow roots
 * and, independently, asks a WebGL context for its unmasked renderer.
 */
const { chromium } = require(require.resolve('playwright', { paths: [process.cwd()] }));

(async () => {
  const browser = await chromium.launch({ headless: false });
  console.log('chromium', browser.version());

  // 1) the chrome://gpu report, shadow DOM included
  const page = await browser.newPage();
  await page.goto('chrome://gpu');
  await page.waitForTimeout(4000);
  const lines = await page.evaluate(() => {
    const out = [];
    (function walk(n) {
      if (n.shadowRoot) walk(n.shadowRoot);
      for (const c of n.childNodes) {
        if (c.nodeType === 3) { const t = c.textContent.trim(); if (t) out.push(t); }
        else walk(c);
      }
    })(document);
    return out;
  });
  const want = /^(Canvas|Compositing|Rasterization|Video Decode|Vulkan|WebGL|WebGL2|WebGPU|OpenGL|GL_RENDERER):?$/;
  console.log('--- chrome://gpu (label: status)');
  for (let i = 0; i < lines.length - 1; i++) {
    if (want.test(lines[i])) {
      const j = lines[i + 1] === ':' ? i + 2 : i + 1;  // value can sit after a bare ':' cell
      console.log(`${lines[i].replace(/:$/, '')}: ${lines[j]}`);
    }
  }
  // The legend of the page also contains the sentence
  // "Software only. Hardware acceleration disabled": that is a key, not a status.

  // 2) what a WebGL context itself reports
  const probe = await browser.newPage();
  await probe.goto('about:blank');
  const renderer = await probe.evaluate(() => {
    const gl = document.createElement('canvas').getContext('webgl');
    if (!gl) return null;
    const e = gl.getExtension('WEBGL_debug_renderer_info');
    return e ? gl.getParameter(e.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER);
  });
  console.log('--- UNMASKED_RENDERER_WEBGL:', renderer);
  await browser.close();

  const software = !renderer || /swiftshader|llvmpipe|software|basic render/i.test(renderer);
  console.log(software
    ? 'VERDICT: SOFTWARE or no WebGL. A full render will take hours. Stop and report.'
    : 'VERDICT: hardware renderer reported.');
  process.exit(software ? 2 : 0);
})();
