# 身体の地図｜頭蓋・腰椎の単体レビュー v0.9 引継ぎ・監査記録
更新日：2026-10-25

## 位置づけ
- 元版：`experiments/cleanroom-bone-review-v0.8.html`（改変なし）
- 新版：`experiments/cleanroom-bone-review-v0.9.html`
- ブランチ：`cleanroom-pelvis-v0.1`
- ステータス：**要レビュー。人体形態データとしての解剖学的承認は未実施。**
- 採用方針：基準画像との照合および複数視点での表示検証完了まで、全身版に移植しない。
- 画像利用：資料図版を形態確認に使用。図・画像・既存メッシュの複製や輪郭トレースはしていない。
- 形状値：すべて作図上の単位。mm等の実測値ではない。

## 参考にした外部資料
1. Gray's Anatomy 1918, head anterior/lateral and typical lumbar vertebra: https://anatomie.cosminpopa.ro/en/5c-the-exterior-of-the-skull/ （正面図 Fig.190・側面図 Fig.188）
2. OpenStax Anatomy and Physiology 2e 7.2 The Skull: https://openstax.org/books/anatomy-and-physiology-2e/pages/7-2-the-skull （Fig.7.4・7.5、眼窩・頬骨弓・側頭骨）
3. OpenStax Anatomy and Physiology 2e 7.3 Vertebral Column: https://openstax.org/books/anatomy-and-physiology-2e/pages/7-3-the-vertebral-column （腰椎・椎間孔・関節突起）
4. NCBI StatPearls, Anatomy, Back, Lumbar Vertebrae: https://www.ncbi.nlm.nih.gov/books/NBK459278/ （椎弓、関節突起、椎体、棘突起、乳頭突起）
5. Additional visual comparison: https://anatomie.cosminpopa.ro/en/3a-3-the-lumbar-vertebr/ （腰椎原図）

## v0.8 → v0.9 の差分
- 頭蓋：眼窩外側縁と頬骨への支持部分に、連続性を意識した体積を追加。眼窩開口は再度くり抜き、塞がない設計。
- 側面：頬骨弓の後方付着・側頭骨付近の厚み、乳様突起の概形と外耳道の「入口のくぼみ」を追加。**外耳道を正確なトンネルとして制作したわけではない。**
- 腰椎：椎弓根の下椎切痕と上椎切痕を区別する凹み、横突起基部付近の副突起の概形を追加。
- 新旧比較：**頭蓋・腰椎とも v0.8 の実装を旧版として保持**。旧v0.7比較ではない。
- 操作：眼窩・頬骨弓・顎に加えて外耳道付近へ寄るボタン、腰椎の椎切痕へ寄るボタンを追加。
- iPhone：指での回転・ピンチ中のみ軽量描画し、指を離すと元の画質へ復帰する方式を試作。**実機確認は未実施。**

## 必須監査項目（未完了）
- [ ] 頭蓋骨の正面・側面・上面・斜め・後面をv0.8と見比べ、骨の連続性、眼窩開口、顔面幅、歯列と下顎の位置を評価
- [ ] 頬骨弓の前後接続と側頭部・耳孔・乳様突起の位置関係を実物資料の図と照合
- [ ] 腰椎上面・下面・側面を評価し、椎体輪郭・椎孔・椎弓板・椎切痕・関節面・乳頭/副突起を照合
- [ ] 新旧切替時に方向・縮尺・中心を固定できるか、画像と形状に破綻がないか確認
- [ ] 下顎・歯冠の表示切替、焦点移動・拡大縮小・初期表示への復帰を確認
- [ ] iPhone Safari実機で操作性、起動時間、メモリ使用、画質復帰、スクロールを確認
- [ ] レンダリングだけでなく独立した解剖学レビューを実施

## 次の版の候補
- 3方向レンダリング画像と実物の写真を並べた差分監査
- 骨ごとの分割・名称表示に進む前に頭蓋骨輪郭の精度を確保する
- 実測骨標本または利用許諾が明確な3Dデータによる寸法比の検証
- 監査済み部分のみ、全身版へ段階的に取り込む

## 開発に関する注意
このメモは実装と資料照合に基づく記録であり、骨格の医学的正確性、実機性能、ページ配信を保証しない。