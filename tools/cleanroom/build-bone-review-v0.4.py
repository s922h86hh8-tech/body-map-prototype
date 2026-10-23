from pathlib import Path
import hashlib
r=Path(__file__).resolve().parents[2]
s=(r/'experiments/cleanroom-bone-review-v0.3.html').read_text()
assert hashlib.sha256(s.encode()).hexdigest()=='89c36d1e50c649740e649454d32a471abeef44b83649de3c98cb03f93c74fe11'
old=(r/'tools/cleanroom/bone-review-shapes-v0.1.js').read_text()
v2=(r/'tools/cleanroom/bone-review-shapes-v0.2.js').read_text()
fine=v2.replace("version:'0.2'","version:'0.4'").replace('skullGridStep:.5,lumbarGridStep:.25','skullGridStep:.3,jawGridStep:.25,lumbarGridStep:.18').replace('[9,12,13],.5)','[9,12,13],.3)').replace('[7,10,-1],.4)','[7,10,-1],.25)').replace('[9,6,4],.25)','[9,6,4],.18)')
assert s.count(v2)==1 and s.count(old)==1
s=s.replace(v2,fine).replace(old,v2)
# Snap intersections extremely near a grid endpoint consistently; compact unused vertices.
s=s.replace('t<1e-7?a:t>1-1e-7?b:null','t<1e-4?a:t>1-1e-4?b:null')
s=s.replace(' add(name,reg,side,vs,fs);\n}', ' const used=[...new Set(fs.flat())].sort((a,b)=>a-b), remap=new Map(used.map((v,i)=>[v,i]));\n add(name,reg,side,used.map(i=>vs[i]),fs.map(f=>f.map(i=>remap.get(i))));\n}',1)
s=s.replace('単体レビュー 0.3','単体レビュー 0.4').replace('前回の単体0.1','前回の形0.3')
s=s.replace('表示の滑らかさを改善した版です。骨の形状は0.2と同じで、','拡大時の輪郭を細かくした版です。造形の基準は0.2と共通で、')
s=s.replace('初回は生成に時間がかかります。','初回は細かな形状を生成するため時間がかかります。')
s=s.replace('Math.min(4,viewState.zoom*v)','Math.min(6,viewState.zoom*v)')
s=s.replace('<footer>','<footer><a href="cleanroom-bone-review-v0.3.html">前回の表示0.3へ</a> · ',1)
(r/'tools/cleanroom/bone-review-shapes-v0.4.js').write_text(fine)
(r/'experiments/cleanroom-bone-review-v0.4.html').write_text(s)
