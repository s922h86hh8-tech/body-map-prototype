from pathlib import Path
import hashlib

r = Path(__file__).resolve().parents[2]
s = (r / 'experiments/cleanroom-bone-review-v0.7.html').read_text()
assert hashlib.sha256(s.encode()).hexdigest() == 'cf9ec3140e4c08db8d463bdef05787f88ba711e5e4aaa61d899a9dc34db732e4'
a = s.index('const PREVIOUS_FACE=(()=>{')
b = s.index('const SURFACE_FINISH=', a)
old = (r / 'tools/cleanroom/bone-review-shapes-v0.7.js').read_text()
new = (r / 'tools/cleanroom/bone-review-shapes-v0.8.js').read_text()
s = s[:a] + 'const PREVIOUS_FACE=(()=>{\n' + old + '\nreturn {buildSkullNew,orbitD,nasalD};})();\n' + new + '\n' + s[b:]
s = s.replace('単体レビュー 0.7', '単体レビュー 0.8').replace('前回の形0.6', '前回の形0.7')
s = s.replace('眼窩の縁・頬骨から上顎への面・鼻の開口部を見直した形状試作です。', '眼窩の壁と床・上顎の凹凸・骨性鼻中隔と下鼻甲介の概形を見直した試作です。')
s = s.replace('骨の縫合・鼻腔内部・頭蓋底の細部・歯根などは未制作です。', '縫合・頭蓋底・歯根は未制作です。鼻腔内部は中隔と下鼻甲介の概形のみで、眼窩奥の管や裂は未制作です。')
s = s.replace('<footer>', '<footer><a href="cleanroom-bone-review-v0.7.html">前回の単体0.7へ</a> · ', 1)
(r / 'experiments/cleanroom-bone-review-v0.8.html').write_text(s)
