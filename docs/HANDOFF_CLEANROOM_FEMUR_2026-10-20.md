
# 引継ぎ｜独自大腿骨形状試作 v0.3・関連資料整理版

更新日：2026-10-20（日本時間）  
リポジトリ：s922h86hh8-tech/body-map-prototype  
対象ブランチ：cleanroom-pelvis-v0.1  
確認時HEAD：c440ad31c7a781bf16d7f36b54a4f020f45363fb  
公開ブランチ：prototype-0.3

## 目的と現状

既存3Dモデルを転用せず、参照資料で一般的な位置関係を確認しながら独自に作成した、右大腿骨近位部の形状レビュー用試作です。公開ページは[右大腿骨・形状試作 v0.3](https://s922h86hh8-tech.github.io/body-map-prototype/experiments/cleanroom-femur-study-v0.3.html)。本体アプリから独立しています。

ページはv0.3、形状パラメータ/保存用glTFはv0.2です。大転子上内側縁と「転子窩（模式）」の凹み、内側/後内側の方向、全体/骨面拡大、凹み選択時の拡大を加えました。前・後ろ・外側・斜め、回転、拡大縮小、リセット、glTF保存は維持。画面下の浮動バー対策としてモバイル下余白を増やしましたが、v0.3実機での改善は未確認です。

今回の形状値はすべて無単位の描画値です。人体の計測座標・mm・標準寸法ではありません。骨形状の解剖学的正確性、臨床/学習用途への採用、筋の付着面は承認されていません。

## 技術検証と解剖学監査

**技術検証（v0.3）**：Node VMで実ページの形状コードと操作コールバックを検査。21,512頂点、43,020三角形、連結1、境界/不正辺0、面積0/尺度調整後極小面積三角形0、凹み表面342頂点。6方向・凹み選択の視点/拡大・リセットを確認。実HTMLシェーダーをMesaオフスクリーンOpenGL ES 3.2で描画し、後内側/内側拡大で凹みを確認。ブラウザWebGLやタッチ操作の実機試験ではありません。

**公開確認**：HTTP 200、25,378 bytes、SHA-256 744dd83db04d0735e395e4c5684ee130489ac4e8c69feac4651275f5eeef13e7。Pages workflow run 38745373556 success。クラウド確認ブラウザではページ本文/ボタンは読み込まれたもののWebGLを起動できず、3Dは表示されませんでした。これはiPhoneの挙動を示しません。

**解剖学監査**：既存のCLEANROOM_FEMUR_ANATOMY_AUDIT_V0.1.mdとcleanroom-femur-landmarks-v0.1.jsonは、原形状v0.1を含むv0.2 HTMLと形状パラメータv0.1を対象にしています。前後/内外方向の数式と骨頭・小転子の大まかな位置関係等を確認していますが、表面精度、実寸、付着面は未承認です。造形軸の112.22669783°は検証済み頸体角ではありません。v0.3の追加した縁/凹みは別途解剖学監査されていません。

未監査項目：骨頭・頸部・大/小転子・近位骨体の形状/比率/曲率、頸体角と前捻角（遠位/膝側基準なし）、大転子の区画と転子窩の正確な位置/深さ、骨頭窩・転子間線等の未作成部位、切断範囲、5筋の起始/走行/停止面・個体差・骨盤との接続。監査には各骨性点/面と軸の定義、独立資料の明示的な定義、計測/比較方法が必要。資料にない座標や値は作らず未確認と記録する。

記録上の参照：Gray/Carter 1858（Wellcome Collection、右大腿骨後面図、所蔵記録はPublic Domain Mark表示）、Philippon et al. 2014（近位大腿骨/付着関係、DOI 10.1177/2325967114535188）、Soodmand et al. 2019（角度の軸定義、DOI 10.1111/os.12416）。図版・写真・座標・既存メッシュは形状へ転写していません。資料全文はリポジトリに同梱されておらず、URLと照合メモがあります。

## iPhone実機確認（v0.3未完了）

v0.2には2026-10-15のユーザー提供録画の記録があり、3D/方向変更/ハイライト/サイズ変化を確認したとあります。Safariか別アプリ内ブラウザかは不明で、v0.3の根拠にはできません。v0.3は次の項目を実機で記録してください。

1. 公開URLで3Dが起動し、WebGLエラーや空白が出ない。
2. 前・後ろ・外側・斜め・内側・後内側の向き。
3. 全体/骨面拡大、転子窩選択と拡大、リセット。
4. 1本指回転、2本指ズーム、glTF保存。
5. 縦/横画面で下部ブラウザバーがボタン/説明を隠さない。

端末/ブラウザ名・操作ごとの結果・必要なら画面証跡を保存してください。v0.3の録画/スクリーンショットは現在のブランチ内で確認できていません。

## 次の作業と完了条件

1. **iPhone確認**：上記5項目を操作別に記録。完了＝v0.3の実機挙動と表示重なりが再現できる記録がある。
2. **監査軸と基準点の定義**：骨頭中心、頸部/骨体軸、評価点/面、遠位基準を出典付きで表にする。完了＝単位・測定法・資料の定義が揃い、欠けた項目は未確認と明記。
3. **独立資料で形状監査**：外形/比率、転子窩/大転子、角度等を区別して照合。完了＝根拠、差分、個体差、未確定範囲が記録される。未判定部分は模式表示のまま。
4. **必要なら新バージョンを作る**：理由と根拠を先に記録し、新HTML/パラメータ/glTFとして保存。完了＝メッシュ/操作/書出し/表示/公開を再検証し、旧版が残る。
5. **採用判断**：実機と解剖学監査の後、利用範囲/未確定表示/必要な出典表示を決める。現時点で正確性や臨床利用をうたわない。

## 権利・制作・保全ルール

- 既存メッシュ/頂点/輪郭/寸法/座標の抽出、スクリーンショット/図版のトレース、他モデルのリトポロジーをしない。一般的な解剖学的事実と独自の形状表現を区別。
- 参照した事実、資料の版/ライセンス、設計判断、成果物ハッシュを内部記録する。独自制作が法的な非侵害保証になるわけではない。
- 無単位の描画値を実測値、mm、標準値、筋停止面に読み替えない。技術検証と解剖学承認は別。
- 旧HTML v0.1/v0.2、パラメータv0.1、glTF v0.1、既存アプリ、GLB原本は上書き/削除しない。公開本体への統合/モデル差替えは別途監査後に判断。
- 今回の変更は文書2ファイルだけ（本引継ぎ追加、ANATOMY_MASTER追記）。アプリ/GLB/旧版/公開ブランチは変更しない。

## 関連資料一覧

「確認済み」はファイル内容や記録を確認した意味で、専門家承認や現在の実機再確認を意味しません。

| ファイル | 内容・確認済み事項 | 未確認事項/範囲 |
| --- | --- | --- |
| [docs/ANATOMY_MASTER.md](https://github.com/s922h86hh8-tech/body-map-prototype/blob/cleanroom-pelvis-v0.1/docs/ANATOMY_MASTER.md) | アプリ全体の設計正本、独自制作方針と履歴 | 全身モデルの監査は別。台帳全体を今回再監査していない |
| [docs/CLEANROOM_PELVIS_V0.1.md](https://github.com/s922h86hh8-tech/body-map-prototype/blob/cleanroom-pelvis-v0.1/docs/CLEANROOM_PELVIS_V0.1.md) | 5筋制作制約、骨単体試作への分離 | 5筋形状/座標/外形は未作成 |
| [docs/CLEANROOM_PELVIS_LANDMARK_AUDIT_V0.1.md](https://github.com/s922h86hh8-tech/body-map-prototype/blob/cleanroom-pelvis-v0.1/docs/CLEANROOM_PELVIS_LANDMARK_AUDIT_V0.1.md) | 骨盤/大腿骨の文章資料上の相対関係、作業ゲート | 完全な骨面座標や筋腹形状なし |
| [docs/CLEANROOM_COORDINATE_FRAME_V0.1.md](https://github.com/s922h86hh8-tech/body-map-prototype/blob/cleanroom-pelvis-v0.1/docs/CLEANROOM_COORDINATE_FRAME_V0.1.md) | +X外側/+Y前/+Z上の制作座標規約 | 原点の数値、mm計測点群なし |
| [docs/CLEANROOM_GEOMETRY_DATA_REVIEW_V0.1.md](https://github.com/s922h86hh8-tech/body-map-prototype/blob/cleanroom-pelvis-v0.1/docs/CLEANROOM_GEOMETRY_DATA_REVIEW_V0.1.md) | Recherche Data Gouv、MedPelvis3D、TCIAの候補評価 | 候補全件を今回再調査していない |
| [docs/CLEANROOM_FEMUR_STUDY_V0.1.md](https://github.com/s922h86hh8-tech/body-map-prototype/blob/cleanroom-pelvis-v0.1/docs/CLEANROOM_FEMUR_STUDY_V0.1.md) | 最初の骨単体試作、制作来歴と技術検証 | v0.1記録はv0.3検証ではない。厳密自己交差等に制限 |
| [docs/CLEANROOM_FEMUR_ANATOMY_AUDIT_V0.1.md](https://github.com/s922h86hh8-tech/body-map-prototype/blob/cleanroom-pelvis-v0.1/docs/CLEANROOM_FEMUR_ANATOMY_AUDIT_V0.1.md) | v0.2 HTML/形状v0.1の方向式、粗い位置関係、軸・資料 | v0.3追加形状、骨面精度、実寸、停止面は未監査 |
| [docs/CLEANROOM_FEMUR_SURFACE_V0.2.md](https://github.com/s922h86hh8-tech/body-map-prototype/blob/cleanroom-pelvis-v0.1/docs/CLEANROOM_FEMUR_SURFACE_V0.2.md) | v0.3ページ/形状v0.2の設計、値、操作、技術記録 | 実機と解剖学的正確さは未確認 |
| [docs/CLEANROOM_FEMUR_IPHONE_PREVIEW_V0.2.md](https://github.com/s922h86hh8-tech/body-map-prototype/blob/cleanroom-pelvis-v0.1/docs/CLEANROOM_FEMUR_IPHONE_PREVIEW_V0.2.md) | 添付HTML空白、v0.2録画、下部バーの重なり | 録画ブラウザ特定不可。v0.3未確認 |
| [docs/HANDOFF_CLEANROOM_FEMUR_2026-10-19.md](https://github.com/s922h86hh8-tech/body-map-prototype/blob/cleanroom-pelvis-v0.1/docs/HANDOFF_CLEANROOM_FEMUR_2026-10-19.md) | 前回の短い引継ぎ、公開確認の要約 | 本書で資料別の範囲を拡張 |
| [assets/cleanroom/deep-gluteal-facts.v0.1.json](https://github.com/s922h86hh8-tech/body-map-prototype/blob/cleanroom-pelvis-v0.1/assets/cleanroom/deep-gluteal-facts.v0.1.json) | 5筋の文章上の起始/走行/停止と出典URL | 形状値ではない。全記載を今回独立再照合していない |
| [assets/cleanroom/landmark-fit-audit.v0.1.json](https://github.com/s922h86hh8-tech/body-map-prototype/blob/cleanroom-pelvis-v0.1/assets/cleanroom/landmark-fit-audit.v0.1.json) | ライセンス/定義表/CSVヘッダーの調査と応答ハッシュ | 参加者座標は使用せず。筋付着面の座標資料ではない |
| [assets/cleanroom/femur-shape-parameters.v0.1.json](https://github.com/s922h86hh8-tech/body-map-prototype/blob/cleanroom-pelvis-v0.1/assets/cleanroom/femur-shape-parameters.v0.1.json) | 旧形状の無単位プリミティブ値、監査pending | 実測/標準寸法ではない |
| [assets/cleanroom/femur-shape-parameters.v0.2.json](https://github.com/s922h86hh8-tech/body-map-prototype/blob/cleanroom-pelvis-v0.1/assets/cleanroom/femur-shape-parameters.v0.2.json) | 縁/凹み追加を含む現行描画パラメータ | 解剖学精度は未承認 |
| [assets/cleanroom/right-proximal-femur-study.v0.1.gltf](https://github.com/s922h86hh8-tech/body-map-prototype/blob/cleanroom-pelvis-v0.1/assets/cleanroom/right-proximal-femur-study.v0.1.gltf) | 保全された旧生成モデル | 現行追加形状を含まず。解剖学承認なし |
| [assets/cleanroom/right-proximal-femur-study.v0.2.gltf](https://github.com/s922h86hh8-tech/body-map-prototype/blob/cleanroom-pelvis-v0.1/assets/cleanroom/right-proximal-femur-study.v0.2.gltf) | 現行模式形状の出力。メッシュ検査対象 | 実寸/臨床正確性は未承認 |
| [experiments/cleanroom-femur-study-v0.1.html](https://github.com/s922h86hh8-tech/body-map-prototype/blob/cleanroom-pelvis-v0.1/experiments/cleanroom-femur-study-v0.1.html) | 初版ページ | 旧版。現行操作を含まない |
| [experiments/cleanroom-femur-study-v0.2.html](https://github.com/s922h86hh8-tech/body-map-prototype/blob/cleanroom-pelvis-v0.1/experiments/cleanroom-femur-study-v0.2.html) | 起動案内などを加えた旧公開ページ、録画対象 | 現行形状v0.2/新操作を含まない |
| [experiments/cleanroom-femur-study-v0.3.html](https://github.com/s922h86hh8-tech/body-map-prototype/blob/cleanroom-pelvis-v0.1/experiments/cleanroom-femur-study-v0.3.html) | 現行公開ページ。6方向、範囲切替、凹み選択 | WebGL実ブラウザ/タッチ/iPhoneは未確認 |
| [docs/validation/cleanroom-femur-v0.1.json](https://github.com/s922h86hh8-tech/body-map-prototype/blob/cleanroom-pelvis-v0.1/docs/validation/cleanroom-femur-v0.1.json) | v0.1の過去のブラウザ/形状値 | 現行版の証明ではない |
| [docs/validation/cleanroom-femur-v0.2.json](https://github.com/s922h86hh8-tech/body-map-prototype/blob/cleanroom-pelvis-v0.1/docs/validation/cleanroom-femur-v0.2.json) | v0.2旧ページのブラウザ検査、JS無効案内 | v0.3操作の記録ではない |
| [docs/validation/cleanroom-femur-v0.2-hosted.json](https://github.com/s922h86hh8-tech/body-map-prototype/blob/cleanroom-pelvis-v0.1/docs/validation/cleanroom-femur-v0.2-hosted.json) | 公開v0.2、旧クラウドWebGLとiPhone録画の記録 | v0.3ではない。Safariとは確定しない |
| [docs/validation/cleanroom-femur-landmarks-v0.1.json](https://github.com/s922h86hh8-tech/body-map-prototype/blob/cleanroom-pelvis-v0.1/docs/validation/cleanroom-femur-landmarks-v0.1.json) | v0.2 HTML/形状v0.1の計算監査結果 | v0.3追加面は対象外 |
| [docs/validation/cleanroom-femur-surface-v0.2.json](https://github.com/s922h86hh8-tech/body-map-prototype/blob/cleanroom-pelvis-v0.1/docs/validation/cleanroom-femur-surface-v0.2.json) | 現行形状/操作/glTFのNode VM検査 | DOM/ブラウザ/実機/解剖学検証なし |
| [docs/validation/cleanroom-femur-surface-gles-v0.2.json](https://github.com/s922h86hh8-tech/body-map-prototype/blob/cleanroom-pelvis-v0.1/docs/validation/cleanroom-femur-surface-gles-v0.2.json) | 実HTMLシェーダーのオフスクリーン描画 | ブラウザWebGL/iPhone試験ではない |
| [docs/validation/cleanroom-femur-surface-hosted-v0.2.json](https://github.com/s922h86hh8-tech/body-map-prototype/blob/cleanroom-pelvis-v0.1/docs/validation/cleanroom-femur-surface-hosted-v0.2.json) | 現行v0.3公開URL、HTTP/ハッシュ/workflow | クラウドWebGL不可、iPhone未確認 |
| [tools/cleanroom/audit-femur-landmarks.cjs](https://github.com/s922h86hh8-tech/body-map-prototype/blob/cleanroom-pelvis-v0.1/tools/cleanroom/audit-femur-landmarks.cjs) | v0.2 HTML/形状v0.1対象の方向/軸計算スクリプト | v0.3の凹みは監査しない |
| [tools/cleanroom/check-femur-study.cjs](https://github.com/s922h86hh8-tech/body-map-prototype/blob/cleanroom-pelvis-v0.1/tools/cleanroom/check-femur-study.cjs) | 主にv0.1ページを実Chromiumで検査 | スクリプトの存在は最新実行を意味しない |
| [tools/cleanroom/check-femur-surface-study.cjs](https://github.com/s922h86hh8-tech/body-map-prototype/blob/cleanroom-pelvis-v0.1/tools/cleanroom/check-femur-surface-study.cjs) | v0.3形状/操作コールバック/glTF構造検査 | UI/実機/解剖学監査はしない |
| [tools/cleanroom/build-femur-surface-page.py](https://github.com/s922h86hh8-tech/body-map-prototype/blob/cleanroom-pelvis-v0.1/tools/cleanroom/build-femur-surface-page.py) | v0.2ページ+形状値からv0.3生成 | この更新作業で再生成一致を再実行していない |
| [tools/cleanroom/render-femur-surface.py](https://github.com/s922h86hh8-tech/body-map-prototype/blob/cleanroom-pelvis-v0.1/tools/cleanroom/render-femur-surface.py) | EGL/GLESによるシェーダー描画 | ブラウザ操作試験ではない |

## 今回ブランチで確認できなかった資料

- v0.3のiPhone録画/スクリーンショット、専門家の形状承認、人体標本の計測データ、解剖学的に検証済みの比較3Dモデルは見つかりませんでした。
- v0.2の17.6秒録画そのものはGitHubに保存されていません。文書の観察メモのみ確認。
- Gray/Carter、Philippon、Soodmand等の資料全文はブランチにありません。URLと内部照合記録を確認しましたが、今回この棚卸しでリンク先全文を再取得していません。
- docs/PHASE1_2D_WEBAPP_HANDOFF_2026-10-11.md は全体アプリの別引継ぎとして存在しますが、大腿骨監査根拠ではないため内容確認の対象外です。
- オフスクリーン描画画像は一時出力で、GitHubに保存された成果物としては確認できません。記載のコードと対応環境が必要です。

## 次チャットでの確認順

1. 本書とdocs/ANATOMY_MASTER.mdを同じブランチの最新HEADで読む。
2. CLEANROOM_FEMUR_SURFACE_V0.2.md、CLEANROOM_FEMUR_ANATOMY_AUDIT_V0.1.mdを読む。
3. cleanroom-femur-surface-v0.2.json、cleanroom-femur-surface-gles-v0.2.json、cleanroom-femur-surface-hosted-v0.2.jsonの対象と限界を確認。
4. iPhoneでv0.3を確認した新証跡があれば、その記録と実ファイルを照合。
5. 変更前にブランチHEADとHTML/形状JSONのハッシュを確かめ、差分があれば先に調査。

## 継続作業の追記（2026-10-22）
- [監査基準・v0.3の評価範囲](https://github.com/s922h86hh8-tech/body-map-prototype/blob/cleanroom-pelvis-v0.1/docs/CLEANROOM_FEMUR_AUDIT_BASIS_2026-10-22.md) を追加し、一次資料の軸定義と現行パラメータを照合した。最新状況は同文書と設計台帳の10月22日追記を参照。
- 計測定義の対応表と造形値の再計算まで完了。骨面評価点の抽出、具体的な軸当てはめ手順、転子窩の表面精度、独立別資料との照合、iPhone v0.3実機確認は未完了。
- 原文の10月20日時点の状態を履歴として保持。形状・公開ページの変更はない。

## 表面測定の実装・実行（2026-10-22追記）
- [表面の数値診断](https://github.com/s922h86hh8-tech/body-map-prototype/blob/cleanroom-pelvis-v0.1/docs/CLEANROOM_FEMUR_SURFACE_DIAGNOSTICS_V0.1.md) と測定コード tools/cleanroom/measure-femur-surface-v0.1.cjs、実行結果 docs/validation/cleanroom-femur-surface-diagnostics-v0.1.json を追加。
- buildMesh()由来表面の球当てはめ、断面輪郭、一方向の凹みプロファイルを計算済み。臨床計測・解剖学的承認ではない。
- 頸部75%断面が2輪郭となり、軸点を囲む輪郭の中心も不安定。頸部の評価領域定義が必要。iPhone未確認。形状・公開ページの改訂はなし。
