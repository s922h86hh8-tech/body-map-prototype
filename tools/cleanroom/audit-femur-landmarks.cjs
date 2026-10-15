'use strict';
// A construction audit, not anatomical validation or a browser rendering test.
// Run from any directory: node tools/cleanroom/audit-femur-landmarks.cjs
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {createHash} = require('node:crypto');
const root = path.resolve(__dirname, '../..');
const files = {
  page: 'experiments/cleanroom-femur-study-v0.2.html',
  parameters: 'assets/cleanroom/femur-shape-parameters.v0.1.json'
};
const page = fs.readFileSync(path.join(root, files.page), 'utf8');
const parametersText = fs.readFileSync(path.join(root, files.parameters), 'utf8');
const model = JSON.parse(parametersText);
const extract = (pattern, label) => {
  const match = page.match(pattern);
  if (!match) throw Error('Cannot locate ' + label + '; audit needs review');
  return vm.runInNewContext('(' + match[1] + ')', {Math}, {timeout: 100});
};
const embedded = extract(/const MODEL=([\s\S]*?);\s*const FEATURES=/, 'MODEL');
for (const key of Object.keys(embedded)) {
  if (JSON.stringify(model[key]) !== JSON.stringify(embedded[key])) {
    throw Error('Page and parameter record differ: ' + key);
  }
}
const views = extract(/const views=([^;]+);/, 'views');
// Explicitly guard the equations used below against changes in the renderer.
for (const equation of [
  'p=vec3(c*p.x-s*p.y,s*p.x+c*p.y,p.z)',
  'p=vec3(p.x,cp*p.y-sp*p.z,sp*p.y+cp*p.z)',
  'gl_Position=vec4(p.x*uZoom/uAspect,p.z*uZoom,p.y*.17,1.)',
  'gl.enable(gl.DEPTH_TEST)'
]) if (!page.includes(equation)) throw Error('Projection changed; review audit derivation');
const sub = (a, b) => a.map((v, i) => v - b[i]);
const dot = (a, b) => a.reduce((s, v, i) => s + v * b[i], 0);
const length = v => Math.hypot(...v);
const round = v => Math.round(v * 1e8) / 1e8;
const primitives = Object.fromEntries(model.primitives.map(p => [p.name, p]));
const {head, neck, greater_trochanter: gt, lesser_trochanter: lt,
  proximal_shaft: shaft, intertrochanteric_crest: crest} = primitives;
const towardHead = sub(neck.a, neck.b), distalShaft = sub(shaft.b, shaft.a);
const constructionAngle = Math.acos(Math.max(-1, Math.min(1,
  dot(towardHead, distalShaft) / length(towardHead) / length(distalShaft)))) * 180 / Math.PI;
const axis = sub(neck.b, neck.a), delta = sub(head.c, neck.a);
const t = dot(delta, axis) / dot(axis, axis);
const closest = neck.a.map((v, i) => v + t * axis[i]);
const shaftFraction = (lt.c[2] - shaft.a[2]) / (shaft.b[2] - shaft.a[2]);
const shaftAtLesser = shaft.a.map((v, i) => v + shaftFraction * distalShaft[i]);
const directions = Object.fromEntries(Object.entries(views).map(([name, [yaw, pitch, label]]) => {
  // Depth test uses LESS. Negative depth is nearer; inverse depth gradient
  // therefore gives the anatomical direction from the model toward the viewer.
  const observer = [-Math.cos(pitch) * Math.sin(yaw),
    -Math.cos(pitch) * Math.cos(yaw), Math.sin(pitch)];
  const right = [Math.cos(yaw), -Math.sin(yaw), 0];
  return [name, {label, observerDirectionAnatomical: observer.map(round),
    headMinusGreaterTrochanterHorizontalDrawingUnits: round(dot(sub(head.c, gt.c), right))}];
}));
const report = {
  auditId: 'body-map-femur-construction-audit-v0.1',
  scope: 'Static construction, camera convention and explicitly represented landmarks only',
  anatomicalApproval: false,
  inputFiles: Object.fromEntries(Object.entries(files).map(([key, file]) => [key, {
    path: file, sha256: createHash('sha256').update(fs.readFileSync(path.join(root, file))).digest('hex')
  }])),
  parameterRecordMatchesPage: true,
  coordinateConvention: model.coordinateConvention,
  coarseRelations: {
    headMedialToGreaterTrochanterCenter: head.c[0] < gt.c[0],
    lesserTrochanterCenterMedialToLocalShaft: lt.c[0] < shaftAtLesser[0],
    lesserTrochanterCenterPosteriorToLocalShaft: lt.c[1] < shaftAtLesser[1],
    crestPrimitiveEndpointsPosteriorToHeadCoronalPlane: crest.a[1] < head.c[1] && crest.b[1] < head.c[1]
  },
  directions,
  constructionDiagnostics: {
    neckPrimitiveAndDistalShaftIncludedAngleDegrees: round(constructionAngle),
    headCenterToNeckPrimitiveLineDrawingUnits: round(length(sub(head.c, closest))),
    greaterTrochanterPrimitiveTopMinusHeadCenterZDrawingUnits: gt.c[2] + gt.r[2] - head.c[2],
    isValidatedNeckShaftAngle: false,
    physicalScaleValidated: false,
    interpretation: 'Primitive construction measurements only; clinical axes and a specimen scale are not established.'
  },
  explicitNamedPrimitives: Object.keys(primitives),
  absentExplicitDefinitions: ['fovea_capitis', 'trochanteric_fossa', 'intertrochanteric_line',
    'greater_trochanter_anterior_tip', 'greater_trochanter_posterior_tip',
    'greater_trochanter_superomedial_border', 'quadratus_femoris_attachment_surface',
    'piriformis_attachment_surface', 'conjoint_tendon_attachment_surface', 'distal_condylar_reference_axis'],
  highlights: 'Nearest primitive regions; not audited anatomical surfaces or muscle footprints',
  browserRenderTest: 'Not performed by this script',
  nextGate: 'Define and audit axes, greater-trochanter landmarks and attachment surfaces before adding deep muscles.'
};
console.log(JSON.stringify(report, null, 2));
