"""Rebuild standalone page v0.3 from preserved v0.2 and geometry v0.2."""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
text = (ROOT / 'experiments/cleanroom-femur-study-v0.2.html').read_text()
model = json.loads((ROOT / 'assets/cleanroom/femur-shape-parameters.v0.2.json').read_text())


def replace(old, new):
    global text
    if text.count(old) != 1:
        raise ValueError('Unexpected source count for: ' + old[:80])
    text = text.replace(old, new)


text = text.replace('形状試作 0.2', '形状試作 0.3').replace('独自造形テスト 0.2', '独自造形テスト 0.3')
text = text.replace('/cleanroom-femur-study-v0.2.html', '/cleanroom-femur-study-v0.3.html')
text = text.replace('/docs/CLEANROOM_FEMUR_STUDY_V0.1.md', '/docs/CLEANROOM_FEMUR_SURFACE_V0.2.md')
text = text.replace('FORM STUDY 01', 'FORM STUDY 02')
replace('</style>\n<div class="app">', '''.framings{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px}.framings button{font:inherit;font-size:12px;min-height:40px;border:1px solid #dae5e8;border-radius:12px;background:white;color:#456874}.framings button[aria-pressed=true]{background:#e5f2ef;color:#226b5b;border-color:#94c3b6}@media(max-width:720px){.views{grid-template-columns:repeat(3,1fr)}.app{padding-bottom:max(96px,env(safe-area-inset-bottom))}}
</style>
<div class="app">''')
replace('<button data-view="oblique" aria-pressed="false">斜め</button>', '<button data-view="oblique" aria-pressed="false">斜め</button><button data-view="medial" aria-pressed="false">内側</button><button data-view="posteromedial" aria-pressed="false">後内側</button>')
replace('</div><button id="reset" class="reset">', '</div><div class="framings" aria-label="表示範囲"><button data-framing="whole" aria-pressed="true">全体を見る</button><button data-framing="surface" aria-pressed="false">骨面を拡大</button></div><button id="reset" class="reset">')
replace('<button data-feature="4" aria-pressed="false">小転子</button>', '<button data-feature="4" aria-pressed="false">小転子</button><button data-feature="5" aria-pressed="false">転子窩（模式）</button>')
replace('骨頭・頸部・大転子・小転子を、単純化した形で確認する試作です。</p>', '大転子の縁と、内側の凹みを追加した形状試作です。</p>')
replace('形・寸法は未監査です。筋の付着点、細かな骨面、骨盤はまだ作成していません。計測や施術の判断には使えません。', '形・寸法は未監査です。凹みは模式表現で、着色は筋の停止面を示しません。骨盤・筋は未作成です。計測や施術の判断には使えません。')
pattern = r'const MODEL=[\s\S]*?;\nconst FEATURES='
text, count = re.subn(pattern, 'const MODEL=' + json.dumps(model, ensure_ascii=False, separators=(',', ':')) + ';\nconst FEATURES=', text, count=1)
if count != 1:
    raise ValueError('MODEL not found')
replace("['右大腿骨・近位部','骨頭・頸部・大転子・小転子を、単純化した形で確認する試作です。']", "['右大腿骨・近位部','大転子の縁と、内側の凹みを追加した形状試作です。']")
replace("['大転子','近位部の外側にある、大きな突出です。細かな付着面はまだ表現していません。']", "['大転子','近位部の外側にある突出です。今回は上内側の縁を模式的に加えています。筋の停止面は未作成です。']")
replace("後ろや斜めの向きで形を確認できます。']];", "後ろや斜めの向きで形を確認できます。'],['転子窩（模式）','大転子の内側・頸部との境界付近に凹みを設けた試作です。後内側から拡大しています。幅・深さ・位置は未監査です。']];")
replace('function field(p){let d=1e9;for(const s of MODEL.primitives){const v=distance(p,s),h=Math.max(0,MODEL.blend-Math.abs(d-v))/MODEL.blend;d=Math.min(d,v)-h*h*MODEL.blend*.25}return Math.max(d,MODEL.cutZ-p[2])}', 'function solid(p){let d=1e9;for(const s of MODEL.primitives){const v=distance(p,s),h=Math.max(0,MODEL.blend-Math.abs(d-v))/MODEL.blend;d=Math.min(d,v)-h*h*MODEL.blend*.25}return d}\nfunction field(p){let d=solid(p);for(const c of MODEL.cavities){const v=-distance(p,c),h=Math.max(0,c.blend-Math.abs(d-v))/c.blend;d=Math.max(d,v)+h*h*c.blend*.25}return Math.max(d,MODEL.cutZ-p[2])}')
replace('function part(p){let d=1e9,id=0;', 'function part(p){const body=solid(p);for(const c of MODEL.cavities){const v=distance(p,c);if(Math.abs(v)<.65&&-v>body-.25&&body<-.05)return c.part}let d=1e9,id=0;')
replace("mode='back';", "mode='back',framing='whole';")
replace('uniform float uAspect;uniform mediump', 'uniform float uAspect;uniform vec3 uCenter;uniform mediump')
replace('aPosition-vec3(25.,0.,-70.)', 'aPosition-uCenter')
replace('uZoom:zoom*fit,uAspect:aspect,uSelected:selected}', "uZoom:zoom*fit*(framing==='surface'?2.3:1),uAspect:aspect,uSelected:selected}")
replace('gl.drawElements(gl.TRIANGLES,mesh.indices.length,gl.UNSIGNED_SHORT,0)', "gl.uniform3fv(gl.getUniformLocation(program,'uCenter'),framing==='surface'?[43,-8,-18]:[25,0,-70]);gl.drawElements(gl.TRIANGLES,mesh.indices.length,gl.UNSIGNED_SHORT,0)")
replace("oblique:[-.65,.2,'斜めから']", "oblique:[-.65,.2,'斜めから'],medial:[Math.PI/2,.18,'内側から'],posteromedial:[.85,.24,'後内側から']")
replace("document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>setView(b.dataset.view));", "function setFraming(name){framing=name;document.querySelectorAll('[data-framing]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.framing===name)));requestDraw()}\ndocument.querySelectorAll('[data-framing]').forEach(b=>b.onclick=()=>setFraming(b.dataset.framing));document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>setView(b.dataset.view));")
replace("document.querySelector('#reset').onclick=()=>{zoom=1;setView('back')}", "document.querySelector('#reset').onclick=()=>{zoom=1;setFraming('whole');setView('back')}")
replace('selected=Number(b.dataset.feature);', "selected=Number(b.dataset.feature);if(selected===5){zoom=1;setView('posteromedial');setFraming('surface')}")
replace("if(e.key==='0'){zoom=1;setView('back');return}", "if(e.key==='0'){zoom=1;setFraming('whole');setView('back');return}")
replace('Body Map original implicit form study 0.1', 'Body Map original implicit form study 0.2')
replace("body-map-original-femur-study-v0.1.gltf", "body-map-original-femur-study-v0.2.gltf")
replace("note:'Arbitrary illustrative proportions. Not a measured specimen. No clinical or measurement use.'", "note:'Original illustrative surface study with schematic trochanteric fossa. Arbitrary proportions, not measured anatomy. No clinical or measurement use.'")
(ROOT / 'experiments/cleanroom-femur-study-v0.3.html').write_text(text)
