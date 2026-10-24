from pathlib import Path
import hashlib
r=Path(__file__).resolve().parents[2]
s=(r/'experiments/cleanroom-bone-review-v0.5.html').read_text()
assert hashlib.sha256(s.encode()).hexdigest()=='1754ab3b90bcc232b311e37849e6c7d0d4e959eaa4cae8f0ee3948a896d79949'
a=s.index('const PREVIOUS=(()=>{');b=s.index('const pool={',a)
s=s[:a]+(r/'tools/cleanroom/bone-surface-finish-v0.6.js').read_text()+'\n'+s[b:]
a=s.index('function generate(');b=s.index('function prepare(',a)
s=s[:a]+'''function generate(target,revision){const key=target+':'+revision;if(pool[key])return pool[key];
 const raw=target+':raw';if(!pool[raw]){objects.length=0;if(target==='skull')buildSkullNew();else buildLumbarNew();pool[raw]=objects.slice()}
 pool[key]=pool[raw].map(o=>({...o,verts:o.verts.map(p=>p.slice()),faces:o.faces}));
 for(const o of pool[key]){if(revision==='new')finishBoneSurface(o,target);prepare(o,target,revision)}return pool[key];
}
'''+s[b:]
s=s.replace('PREVIOUS.orbitD','orbitD').replace('PREVIOUS.nasalD','nasalD')
needle='o.smooth=ns.map((n,i)=>({n:V.unit(n),ao:weights[i]?ao[i]/weights[i]:1}));'
assert needle in s
s=s.replace(needle,needle+'\n if(o.finished)finishVertexLighting(o);')
s=s.replace('単体レビュー 0.5','単体レビュー 0.6').replace('前回の形0.4','前回の形0.5')
s=s.replace('頭蓋・顔面と下顎の形を見直した版です。','人工的な面の継ぎ目とガタつきを抑えた版です。')
s=s.replace('<footer>','<footer><a href="cleanroom-bone-review-v0.5.html">前回の単体0.5へ</a> · ',1)
(r/'experiments/cleanroom-bone-review-v0.6.html').write_text(s)
