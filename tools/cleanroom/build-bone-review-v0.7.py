from pathlib import Path
import hashlib
r=Path(__file__).resolve().parents[2]
s=(r/'experiments/cleanroom-bone-review-v0.6.html').read_text()
assert hashlib.sha256(s.encode()).hexdigest()=='585eb105ac2bd3530bb8ff503c0f91d942458b6a27602f0170ec2d6845d42107'
a=s.index('// Authored shapes for isolated review.');b=s.index('const SURFACE_FINISH=',a)
old=s[a:b];new=(r/'tools/cleanroom/bone-review-shapes-v0.7.js').read_text()
s=s[:a]+"const PREVIOUS_FACE=(()=>{\n"+old+"\nreturn {buildSkullNew,orbitD,nasalD};})();\n"+new+'\n'+s[b:]
a=s.index('function generate(');b=s.index('function prepare(',a)
s=s[:a]+'''function generate(target,revision){const key=target+':'+revision;if(pool[key])return pool[key];
 const raw=target+':raw'+(target==='skull'?revision:'');if(!pool[raw]){objects.length=0;if(target==='skull'){if(revision==='old')PREVIOUS_FACE.buildSkullNew();else buildSkullNew()}else buildLumbarNew();pool[raw]=objects.slice()}
 pool[key]=pool[raw].map(o=>({...o,verts:o.verts.map(p=>p.slice()),faces:o.faces}));
 for(const o of pool[key]){finishBoneSurface(o,target);prepare(o,target,revision)}return pool[key];
}
'''+s[b:]
s=s.replace("if(target==='skull'&&revision==='old'&&o.name==='頭蓋・顔面連続面'){let eye=Math.min(orbitD(c,-1),orbitD(c,1));", "if(target==='skull'&&revision==='old'&&o.name==='頭蓋・顔面連続面'){let eye=Math.min(PREVIOUS_FACE.orbitD(c,-1),PREVIOUS_FACE.orbitD(c,1));")
s=s.replace("if(Math.abs(nasalD(c))<.18&&c[1]<8)ao=.45}\n o.shade", "if(Math.abs(PREVIOUS_FACE.nasalD(c))<.18&&c[1]<8)ao=.45}\n o.shade") if False else s
# Separate cavity shading for previous face.
a=s.index("if(target==='skull'&&revision==='old'");b=s.index('\n',a)
s=s[:a]+s[a:b].replace('Math.abs(nasalD(c))','Math.abs(PREVIOUS_FACE.nasalD(c))')+s[b:]
s=s.replace('単体レビュー 0.6','単体レビュー 0.7').replace('前回の形0.5','前回の形0.6')
s=s.replace('人工的な面の継ぎ目とガタつきを抑えた版です。','眼窩の縁・頬骨から上顎への面・鼻の開口部を見直した形状試作です。')
s=s.replace('<footer>','<footer><a href="cleanroom-bone-review-v0.6.html">前回の単体0.6へ</a> · ',1)
(r/'experiments/cleanroom-bone-review-v0.7.html').write_text(s)
