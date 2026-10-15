'use strict';
// Run from a checkout with Playwright installed. A custom Chromium executable
// may be supplied in BODYMAP_CHROMIUM_PATH. No anatomy accuracy is tested here.
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const assert = require('node:assert/strict');
const {chromium} = require(process.env.BODYMAP_PLAYWRIGHT_MODULE || 'playwright');

(async () => {
  const browser = await chromium.launch({
    executablePath: process.env.BODYMAP_CHROMIUM_PATH || undefined,
    headless: true,
    args: ['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader']
  });
  try {
    const url = pathToFileURL(path.resolve(__dirname, '../../experiments/cleanroom-femur-study-v0.1.html')).href;
    const page = await browser.newPage({viewport: {width: 390, height: 844}, hasTouch: true});
    const errors = [], externalRequests = [];
    page.on('pageerror', e => errors.push(e.message));
    page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
    page.on('request', r => { if (!r.url().startsWith('file:')) externalRequests.push(r.url()); });
    await page.goto(url);
    await page.waitForFunction(() => document.body.dataset.ready === 'true');
    const geometry = await page.evaluate(() => {
      const {mesh} = window.__study, p = mesh.positions, t = mesh.indices;
      const edges = new Map(), parent = Array.from({length: p.length / 3}, (_, i) => i);
      const find = x => { while (parent[x] !== x) x = parent[x]; return x; };
      let volume = 0, zeroAreaTriangles = 0;
      for (let k = 0; k < t.length; k += 3) {
        const ids = [t[k], t[k + 1], t[k + 2]];
        const [a, b, c] = ids.map(i => Array.from(p.slice(3 * i, 3 * i + 3)));
        for (let j = 0; j < 3; j++) {
          const x = ids[j], y = ids[(j + 1) % 3], key = x < y ? x + ':' + y : y + ':' + x;
          edges.set(key, (edges.get(key) || 0) + 1); parent[find(x)] = find(y);
        }
        const u = b.map((x, i) => x - a[i]), v = c.map((x, i) => x - a[i]);
        if (Math.hypot(u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]) === 0) zeroAreaTriangles++;
        volume += (a[0]*(b[1]*c[2]-b[2]*c[1]) + a[1]*(b[2]*c[0]-b[0]*c[2]) + a[2]*(b[0]*c[1]-b[1]*c[0])) / 6;
      }
      const doc = window.__study.gltf();
      return {...window.__study.stats, finite: [...p, ...mesh.normals].every(Number.isFinite),
        badEdges: [...edges.values()].filter(x => x !== 2).length,
        components: new Set(parent.map((_, i) => find(i))).size,
        zeroAreaTriangles, positiveVolume: volume > 0,
        physicalScaleValidated: doc.asset.extras.physicalScaleValidated,
        anatomyAudit: doc.asset.extras.anatomyAudit};
    });
    assert.equal(geometry.badEdges, 0); assert.equal(geometry.components, 1);
    assert.equal(geometry.zeroAreaTriangles, 0); assert.equal(geometry.finite, true);
    assert.equal(geometry.positiveVolume, true); assert.equal(geometry.physicalScaleValidated, false);
    assert.equal(geometry.anatomyAudit, 'pending');
    const parameters = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../../assets/cleanroom/femur-shape-parameters.v0.1.json'), 'utf8'));
    const embedded = await page.evaluate(() => window.__study.model);
    for (const key of Object.keys(embedded)) assert.deepEqual(parameters[key], embedded[key]);
    for (const [label, expected] of [['前', '前から'], ['後ろ', '後ろから'], ['外側', '外側から'], ['斜め', '斜めから']]) {
      await page.getByRole('button', {name: label, exact: true}).click();
      assert.equal(await page.locator('#view-label').textContent(), expected);
    }
    await page.getByRole('button', {name: '向き・大きさを戻す'}).click();
    const session = await page.context().newCDPSession(page);
    const before = await page.evaluate(() => ({yaw, zoom}));
    await session.send('Input.dispatchTouchEvent', {type: 'touchStart', touchPoints: [{x: 160, y: 280, id: 1}]});
    await session.send('Input.dispatchTouchEvent', {type: 'touchMove', touchPoints: [{x: 220, y: 300, id: 1}]});
    await session.send('Input.dispatchTouchEvent', {type: 'touchEnd', touchPoints: []});
    assert.notEqual(await page.evaluate(() => yaw), before.yaw);
    await session.send('Input.dispatchTouchEvent', {type: 'touchStart', touchPoints: [{x: 140, y: 300, id: 1}, {x: 240, y: 300, id: 2}]});
    await session.send('Input.dispatchTouchEvent', {type: 'touchMove', touchPoints: [{x: 100, y: 300, id: 1}, {x: 280, y: 300, id: 2}]});
    await session.send('Input.dispatchTouchEvent', {type: 'touchEnd', touchPoints: []});
    assert.ok(await page.evaluate(() => zoom) > before.zoom);
    await page.getByRole('button', {name: '向き・大きさを戻す'}).click();
    assert.deepEqual(await page.evaluate(() => ({yaw, zoom})), {yaw: 0, zoom: 1});
    await page.getByRole('button', {name: '小転子', exact: true}).click();
    assert.equal(await page.locator('#feature-title').textContent(), '小転子');
    await page.locator('canvas').focus(); await page.keyboard.press('ArrowRight');
    assert.equal(await page.locator('#view-label').textContent(), '自由に回転');
    await page.locator('canvas').press('0');
    const download = page.waitForEvent('download'); await page.locator('#download').click();
    const file = await download, gltf = JSON.parse(fs.readFileSync(await file.path(), 'utf8'));
    assert.equal(gltf.asset.version, '2.0');
    const bytes = Buffer.from(gltf.buffers[0].uri.split(',')[1], 'base64');
    assert.equal(bytes.length, gltf.buffers[0].byteLength);
    assert.equal(gltf.accessors[0].count, geometry.vertices);
    assert.equal(gltf.accessors[2].count, geometry.triangles * 3);
    const pv = gltf.bufferViews[0], iv = gltf.bufferViews[2];
    const positions = new Float32Array(bytes.buffer, bytes.byteOffset + pv.byteOffset, geometry.vertices * 3);
    const indices = new Uint16Array(bytes.buffer, bytes.byteOffset + iv.byteOffset, geometry.triangles * 3);
    for (let k = 0; k < indices.length; k += 3) {
      const [a, b, c] = [indices[k], indices[k+1], indices[k+2]].map(i => Array.from(positions.slice(i*3, i*3+3)));
      const u = b.map((x, i) => x-a[i]), v = c.map((x, i) => x-a[i]);
      assert.ok(Math.hypot(u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]) > 0);
    }
    for (const [width, height] of [[320, 740], [390, 844], [1280, 900]]) {
      await page.setViewportSize({width, height});
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    }
    const fallback = await browser.newPage();
    await fallback.addInitScript(() => { HTMLCanvasElement.prototype.getContext = () => null; });
    await fallback.goto(url);
    assert.equal(await fallback.locator('#error').isVisible(), true);
    assert.equal(await fallback.locator('#download').isDisabled(), true);
    assert.deepEqual(errors, []); assert.deepEqual(externalRequests, []);
    console.log(JSON.stringify({status: 'passed', browser: await browser.version(), geometry,
      checks: ['parameter record matches display', 'front/back/lateral/oblique', 'touch rotation', 'two-finger zoom',
        'reset', 'feature selection', 'keyboard', 'glTF download and buffers', 'exported triangle area',
        '320/390/1280px overflow', 'WebGL unavailable fallback', 'no external requests'],
      anatomyAccuracy: 'not tested', iPhoneSafari: 'not tested'}, null, 2));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
