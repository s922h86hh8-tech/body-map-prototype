# 『施術者からだの地図6』L3 VerSe RAS方向付きCT断面・仮ランドマーク画面 v7.3 監査

**作成日** 2026-11-15 JST  
**研究ブランチ** `l3-reference-method-evaluation-v1`  
**判定** 技術検査は成功。**前後180度反転の解剖学的な独立判定は未完了。L3解剖学教材としては未合格。**

## 1. 今回完成した技術
- VerSe 2020再配布版の元CT／椎骨分割マスク（別ファイルの同一スキャン）を端末／一時CI環境で読み込み、NIfTI affineをCTとmaskで照合。
- 数値ラベル22（データセット上のL3）の重心をRAS世界座標(mm)で計算し、RAS世界軸に正対した3枚の断面（水平／前額／矢状）を局所生成。
- **水平**：画像右=患者右（+R）、画像上=患者前（+A）。**前額**：画像右=+R、上=患者上（+S）。**矢状**：画像右=+A、上=+S。これらは物理座標規約であり、個々の実骨構造が正しく同定済みという意味ではない。
- 3断面の「元CTのみ」と「CT＋L3ラベル22」の切替、仮ランドマーク登録、座標RAS(mm)変換、前後候補点の+Y差の技術的チェック、未承認JSONのローカル書出しを実装。
- 既存LumASe数値1〜7向けのv5比較ビューアーは**流用して上書きしない**。VerSe用v7.3を別画面として追加。
- v7.3のページ自体は**HTML/JSのみ**GitHubに保存。実CT画像・元マスク・生成JSONはGitHubにコミット・公開・Actions artifactへ出さない。画像データはローカルJSONをユーザーが選択する方式。CDNや外部スクリプト呼出しを用いない。
- 既存の公開`prototype-0.3`のL3 v2.4、開発ブランチ`cleanroom-pelvis-v0.1`、v3.3/v3.5/v5.0研究形状のいずれにも変更を加えていない。

## 2. VerSe実CT2症例での技術検査
入力は先行v7.1と同じVerSe20 *再配布版*（`MedOtter/VERSE20`）で、CTとmaskのそれぞれを先行して固定したSHA256と照合して取得。

CI記録：https://github.com/s922h86hh8-tech/body-map-prototype/actions/runs/43677790496

| 実データ | verse005 | verse008 |
|---|---|---|
| CTとmaskの固定SHA256照合 | 成功 | 成功 |
| 3断面の生成 | axial・coronal・sagittal | axial・coronal・sagittal |
| 断面サイズ | 201×201px | 201×201px |
| 画素間隔 | 0.65mm | 0.65mm |
| maskラベル22陽性ボクセル | 64,116 | 32,838 |
| CT+L3領域の3方向画像を生成 | 成功 | 成功 |
| 生成JSONにCT画像を含む | はい・CI内部のみ | はい・CI内部のみ |
| 元画像・マスク・生成画像の外部公開 | なし | なし |
| CT骨格の前後構造の人手同定 | **未実施** | **未実施** |
| 解剖学的完成・専門家認定 | **未合格** | **未合格** |

**注意：**「3断面生成成功」は画像の方向・CT強度とラベル22の表示という技術試験の結果であり、実際の椎体前面・棘突起後端・上下関節面を正しく同定したとの意味ではない。

## 3. 合成試験・UIの検証
- Python合成データによるRAS方向表示・左右／前後／上下画素対応・元CT/mask格子不一致の拒否・ローカル出力合計**8件成功**。
- JavaScriptの方向計算、前後の候補点の数値チェック、ブラウザー操作スクリプトの構文・ネットワーク送信不在の静的点検など **18チェック成功**。
- Chromium Playwrightで**320px、390px、768px**をそれぞれ実画面操作。人工画像のみ使用。3枚読み込み、候補点をタップで選択、+A前後数値順序、印2件、ローカルJSON書出し、読込解除、**横スクロールなし**を確認。
- 初回の実操作テストは、画面外画像をマウス座標で直接クリックするテストの誤りにより失敗。その後Playwright Locatorの自動スクロールを使う試験へ修正し再実行、全画面幅で成功。失敗履歴も保存して経緯を明確にする。
- 合成ブラウザー初回失敗：https://github.com/s922h86hh8-tech/body-map-prototype/actions/runs/43677915533
- 合成ブラウザー修正後成功：https://github.com/s922h86hh8-tech/body-map-prototype/actions/runs/43677979017
- **実機iPhone Safari、Mac Safari、実CTの人手レビューは未確認。** Chromium成功をSafari合格として扱わない。

## 4. 新規コードの所在
- `experiments/tools/build-verse-l3-orientation-review-v7.3.py`
- `experiments/l3-verse-orientation-coordinates-v7.3.js`
- `experiments/l3-verse-orientation-review-v7.3.html`
- `experiments/tests/test-verse-l3-orientation-v7.3.py`
- `experiments/tests/l3-verse-orientation-coordinate-v7.3.test.cjs`
- `experiments/tests/test-verse-l3-orientation-browser-v7.3.py`
- `.github/workflows/l3-verse-orientation-v7.3.yml`
- `.github/workflows/l3-verse-orientation-browser-v7.3.yml`

## 5. 未解決の核心：前後の解剖学的同定
- 現行UIは**ひとつのL3重心を通る断面**しか出さない。棘突起や上下関節面など重要な構造がその断面に写らない場合がある。無理に候補点を登録して形状合格としてはいけない。
- RASの前後ラベルは物理座標上の表記であり、ユーザーが登録した`body_anterior`と`spinous_posterior`の名称が正しいかは**別の独立監査が必要**。単にbody.y > spinous.yを満たしても、180度反転の医学的な誤認を独立に排除したことにならない。
- CT元画像上の前後・上下・左右の構造特徴の人手による同定、異なるスライスでの確認、v2.4/v3.5等のモデル上の対応点との同一座標系での位置合わせが未完了。
- 公式VerSe再構成版と再配布ファイルの同一性・ライセンス・異常椎の検討、解剖学専門家の監査、誤差基準の事前定義が必要。

## 6. 次の実行順序
1. **v7.4**：現在の3枚だけで結論を出さず、L3の上下および前後に複数断面を走査できる安全な研究機能を追加。全断面で物理方向を固定し、選択点に出典ハッシュ・世界座標・スライス位置を記録する。
2. 元CTの椎体前面・棘突起後端・上下終板を異なる断面から独立に照合。1症例の人工的に良い表面距離で前後方向を採用しない。
3. L3の実物由来形状を、出典と監査が残る方式でモデルと比較。左右椎弓根・関節面の監査手順はv5/v6の学習成果を保持。
4. 専門家監査に合格するまでは**公開版の形状を変更せず、L3は医学的・解剖学的未合格**として扱う。

**保存対象は検査コード・表示コード・記録のみ。症例由来CTや派生画像はGitHubへ残していない。**
