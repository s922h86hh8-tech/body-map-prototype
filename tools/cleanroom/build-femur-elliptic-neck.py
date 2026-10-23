"""Build page v0.4 / parameter v0.3 from preserved v0.3 inputs.
All ellipse scales and orientation are illustrative design choices, not measured anatomy.
"""
import hashlib,json,math,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[2]
source=ROOT/'experiments/cleanroom-femur-study-v0.3.html'
raw=source.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='744dd83db04d0735e395e4c5684ee130489ac4e8c69feac4651275f5eeef13e7'
model=json.loads((ROOT/'assets/cleanroom/femur-shape-parameters.v0.2.json').read_text())
neck=next(p for p in model['primitives'] if p['name']=='neck')
def unit(v):
 n=math.sqrt(sum(x*x for x in v));return [x/n for x in v]
axis=unit([b-a for a,b in zip(neck['a'],neck['b'])])
u=unit([float(i==2)-axis[i]*axis[2] for i in range(3)])
v=[axis[1]*u[2]-axis[2]*u[1],axis[2]*u[0]-axis[0]*u[2],axis[0]*u[1]-axis[1]*u[0]]
neck['crossSection']={'u':u,'v':v,'scaleU':1.12,'scaleV':1/1.12,
 'role':'Illustrative fixed ellipse; orientation and ratio are not anatomically validated'}
model['id']='body-map-original-femur-study-v0.3'
model['shapeRevision']='Illustrative elliptic neck; anatomical approval pending'
model['source']+=' Qualitative neck-shape review: Zhang 2021 DOI10.1111/os.12914. No measured ratio or source geometry imported.'
(ROOT/'assets/cleanroom/femur-shape-parameters.v0.3.json').write_text(json.dumps(model,ensure_ascii=False,indent=2)+'\n')
text=raw.decode()
text=text.replace('形状試作 0.3','形状試作 0.4').replace('独自造形テスト 0.3','独自造形テスト 0.4').replace('FORM STUDY 02','FORM STUDY 03')
text=text.replace('/cleanroom-femur-study-v0.3.html','/cleanroom-femur-study-v0.4.html')
text=text.replace('/docs/CLEANROOM_FEMUR_SURFACE_V0.2.md','/docs/CLEANROOM_FEMUR_ELLIPTIC_NECK_V0.3.md')
text,n=re.subn(r'const MODEL=[\s\S]*?;\nconst FEATURES=','const MODEL='+json.dumps(model,ensure_ascii=False,separators=(',',':'))+';\nconst FEATURES=',text,count=1)
assert n==1
old='return Math.sqrt(dx*dx+dy*dy+dz*dz)-(s.r0+(s.r1-s.r0)*t)'
new="""if(s.crossSection){const e=s.crossSection,du=dx*e.u[0]+dy*e.u[1]+dz*e.u[2],dv=dx*e.v[0]+dy*e.v[1]+dz*e.v[2],axial=(dx*ax+dy*ay+dz*az)/Math.hypot(ax,ay,az);return (Math.hypot(du/e.scaleU,dv/e.scaleV,axial)-(s.r0+(s.r1-s.r0)*t))*Math.min(1,e.scaleU,e.scaleV)}return Math.sqrt(dx*dx+dy*dy+dz*dz)-(s.r0+(s.r1-s.r0)*t)"""
assert text.count(old)==1
text=text.replace(old,new)
text=text.replace('大転子の縁と、内側の凹みを追加した形状試作です。','頸部の断面を楕円状にした比較試作です。')
text=text.replace("['頸部','骨頭と大腿骨体の間にある、くびれた部分です。']","['頸部','骨頭と大腿骨体の間のくびれです。今回は楕円状の断面を試しています。長短比と向きは未監査の設計値です。']")
text=text.replace('形・寸法は未監査です。凹みは模式表現で、着色は筋の停止面を示しません。','形・寸法は未監査です。頸部の長短比と向きは試作用の設計値です。着色は筋の停止面を示しません。')
text=text.replace('<details><summary>','<p class="note"><a href="cleanroom-femur-study-v0.3.html">円形断面の旧版 v0.3 と比較する</a></p>\n<details><summary>',1)
text=text.replace("Body Map original implicit form study 0.2","Body Map original implicit form study 0.3")
text=text.replace("body-map-original-femur-study-v0.2.gltf","body-map-original-femur-study-v0.3.gltf")
text=text.replace("Original illustrative surface study with schematic trochanteric fossa.","Original illustrative elliptic-neck study with schematic trochanteric fossa. Ellipse scales and orientation are unvalidated design choices.")
# Neck selection reveals the modified area; fossa close-up remains available.
text=text.replace("selected=Number(b.dataset.feature);if(selected===5)","selected=Number(b.dataset.feature);if(selected===2){zoom=1;setView('oblique');setFraming('surface')}if(selected===5)")
(ROOT/'experiments/cleanroom-femur-study-v0.4.html').write_text(text)

