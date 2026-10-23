from pathlib import Path
import hashlib
r=Path(__file__).resolve().parents[2]
s=(r/'experiments/cleanroom-bone-review-v0.2.html').read_text()
assert hashlib.sha256(s.encode()).hexdigest()=='9c863e23907a2d5d37911cb23a841203e06dfb10bb6dbed8520ebe79a84afc73'
s=s.replace('単体レビュー 0.2','単体レビュー 0.3')
a=s.index('function drawScene(');b=s.index('const $=id=>',a)
# Bind quality handlers after the original DOM helper exists.
renderer=(r/'tools/cleanroom/bone-review-renderer-v0.3.js').read_text()
s=s[:a]+renderer+s[b:]
s=s.replace('<p id="message"','<nav aria-label="表示画質"><button data-quality="high" aria-pressed="true">高精細</button><button data-quality="light" aria-pressed="false">軽量</button></nav><p class="small muted">高精細で滑らかに表示します。操作が重い場合は「軽量」に切り替えてください。</p><p id="message"',1)
s=s.replace('<footer>','<footer><a href="cleanroom-bone-review-v0.2.html">前回の表示0.2へ</a> · ',1)
s=s.replace('骨面の精度・人体寸法・専門家による承認は未確認です。','表示の滑らかさを改善した版です。骨の形状は0.2と同じで、骨面の精度・人体寸法・専門家による承認は未確認です。',1)
(r/'experiments/cleanroom-bone-review-v0.3.html').write_text(s)
