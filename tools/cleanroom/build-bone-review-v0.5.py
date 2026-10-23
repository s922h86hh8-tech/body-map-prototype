from pathlib import Path
import hashlib
r=Path(__file__).resolve().parents[2]
s=(r/'experiments/cleanroom-bone-review-v0.4.html').read_text()
assert hashlib.sha256(s.encode()).hexdigest()=='a903ec9c11527ab4ea1204ab546386ca06ac800a02f5dd0f0cad61c5e7c0f9f6'
v4=(r/'tools/cleanroom/bone-review-shapes-v0.4.js').read_text()
v2=(r/'tools/cleanroom/bone-review-shapes-v0.2.js').read_text()
v5=(r/'tools/cleanroom/bone-review-shapes-v0.5.js').read_text()
assert s.count(v4)==1 and s.count(v2)==1
s=s.replace(v4,v5).replace(v2,v4)
s=s.replace('単体レビュー 0.4','単体レビュー 0.5').replace('前回の形0.3','前回の形0.4')
s=s.replace('拡大時の輪郭を細かくした版です。造形の基準は0.2と共通で、','頭蓋・顔面と下顎の形を見直した版です。')
s=s.replace('眼窩の内外側と奥行き／眼窩下の凹み／頬骨弓の曲がり／下顎頭と三角形の筋突起／下顎枝前縁のつながり','頭蓋と顔面の比率／薄い眉の縁と眼窩の床／鼻の付け根と開口／頬骨から上顎へ続く面／下顎体・角・枝の輪郭')
s=s.replace('<footer>','<footer><a href="cleanroom-bone-review-v0.4.html">前回の単体0.4へ</a> · ',1)
(r/'experiments/cleanroom-bone-review-v0.5.html').write_text(s)
