from pathlib import Path
import hashlib
r=Path(__file__).resolve().parents[2]
base=(r/'experiments/cleanroom-bone-review-v0.1.html').read_text()
assert hashlib.sha256(base.encode()).hexdigest()=='6fd6844c958f74cbefff24fd4333bfb1b22b544e2fc0fb19c7eee1024b004745'
old=(r/'tools/cleanroom/bone-review-shapes-v0.1.js').read_text()
new=(r/'tools/cleanroom/bone-review-shapes-v0.2.js').read_text()
assert base.count(old)==1
previous="\nconst PREVIOUS=(()=>{\n"+old+"\nreturn {skull:buildSkullNew,lumbar:buildLumbarNew,orbitD,nasalD};})();\n"
s=base.replace(old,new+previous).replace('単体レビュー 0.1','単体レビュー 0.2').replace('全身0.2の形','前回の単体0.1')
a=s.index(" else if(target==='skull'){skull();");b=s.index(' pool[key]=',a)
s=s[:a]+" else {if(target==='skull')PREVIOUS.skull();else PREVIOUS.lumbar()}\n"+s[b:]
a=s.index(" if(target==='skull'&&revision==='old'");b=s.index(' return {n,c,ao};',a)
s=s[:a]+" if(target==='skull'&&revision==='old'&&o.name==='頭蓋・顔面連続面'){let eye=Math.min(PREVIOUS.orbitD(c,-1),PREVIOUS.orbitD(c,1));if(Math.abs(eye)<.18&&c[1]<8)ao=.38+.55*Math.max(0,Math.min(1,(c[1]-1)/7));if(Math.abs(PREVIOUS.nasalD(c))<.18&&c[1]<8)ao=.45}\n"+s[b:]
s=s.replace("zoom:1,jaw:true,teeth:true}","zoom:1,jaw:true,teeth:true,center:null,focus:null}")
s=s.replace("const box=frame[viewState.target],scale=", "const box=frame[viewState.target],center=canvas===$('interactive')&&viewState.center?viewState.center:box.c,scale=").replace('V.sub(p,box.c)','V.sub(p,center)')
s=s.replace("viewState.target=target;viewState.revision=revision;viewState.zoom=1;", "if(target!==viewState.target){viewState.center=null;viewState.focus=null;viewState.zoom=1}viewState.target=target;viewState.revision=revision;")
s=s.replace("function pose(name){const p=", "function pose(name){viewState.center=null;viewState.focus=null;const p=")
s=s.replace("$('headControls').hidden=!skull;", "$('headControls').hidden=!skull;$('focusSkull').hidden=!skull;$('focusLumbar').hidden=skull;")
s=s.replace('前頭部〜後頭部の輪郭／眼窩の縁と奥行き／鼻の開口／側頭部と頬骨弓の間の空間／下顎体から下顎枝へのつながり','眼窩の内外側と奥行き／眼窩下の凹み／頬骨弓の曲がり／下顎頭と三角形の筋突起／下顎枝前縁のつながり')
s=s.replace('椎体の厚みと側面のくびれ／腎臓形に近い横断輪郭／三角形の椎孔／椎弓根と椎弓板／板状の棘突起／上下の関節突起','上関節面の内側・後方を向く凹み／下関節面の外側・前方を向くふくらみ／椎弓根下の切れ込み／板状の棘突起／乳頭突起の概形')
nav='''<nav id="focusSkull" aria-label="頭蓋の確認範囲"><button data-focus="orbit">眼窩へ寄る</button><button data-focus="arch">頬骨弓へ寄る</button><button data-focus="jaw">顎の突起へ寄る</button></nav><nav id="focusLumbar" aria-label="腰椎の確認範囲" hidden><button data-focus="facets">関節面へ寄る</button><button data-focus="spinous">棘突起へ寄る</button></nav>'''
s=s.replace('<h2>回して確認</h2>','<h2>回して確認</h2>'+nav)
s=s.replace('固定3図は回転操作の影響を受けません。','固定3図は回転操作の影響を受けません。寄った状態でも前回と切り替えて比較でき、「表示を戻す」で全体へ戻れます。')
s=s.replace('<footer>','<footer><a href="cleanroom-bone-review-v0.1.html">前回の単体0.1へ</a> · ')
s=s.replace('上面図だけから奥行きを確定することもできません。','上面図だけから奥行きを確定することもできません。今回は上顎（図157）・下顎（図176/177）の原図と腰椎の関節面の記述も照合しました。関節面の角度・寸法は実測値ではありません。')
focus='''
const FOCUS={skull:{orbit:{center:[3.1,4,-.5],yaw:-.15,pitch:.07,zoom:2.8},arch:{center:[5.8,1.2,-2.4],yaw:Math.PI/2,pitch:.1,zoom:2.6},jaw:{center:[5,1,-5.5],yaw:Math.PI/2,pitch:.04,zoom:2.5}},lumbar:{facets:{center:[0,-2.7,1],yaw:Math.PI-.5,pitch:.4,zoom:1.8},spinous:{center:[0,-4.8,-.2],yaw:Math.PI/2,pitch:.15,zoom:1.9}}};
function focusScene(key){const p=FOCUS[viewState.target][key];if(!p)return;viewState.focus=key;viewState.center=p.center.slice();viewState.yaw=p.yaw;viewState.pitch=p.pitch;viewState.zoom=p.zoom;drawScene($('interactive'),p.yaw,p.pitch,p.zoom)}
document.querySelectorAll('[data-focus]').forEach(b=>b.addEventListener('click',()=>focusScene(b.dataset.focus)));
'''
s=s.replace("window.addEventListener('resize',drawAll);activate('skull','new');",focus+"window.addEventListener('resize',drawAll);activate('skull','new');")
s=s.replace("drawScene($('side'),Math.PI/2,0,1)","drawScene($('side'),-Math.PI/2,0,1)").replace("side:[Math.PI/2,0]","side:[-Math.PI/2,0]").replace("yaw:Math.PI/2,pitch:.1","yaw:-Math.PI/2,pitch:.1").replace("yaw:Math.PI/2,pitch:.04","yaw:-Math.PI/2,pitch:.04")
(r/'experiments/cleanroom-bone-review-v0.2.html').write_text(s)
