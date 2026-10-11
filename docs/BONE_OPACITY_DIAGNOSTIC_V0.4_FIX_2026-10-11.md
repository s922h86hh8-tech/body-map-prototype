# 全身3D骨透明度検証 v0.4｜初期カメラ計算の実行エラー修正

日付: 2026-10-11
対象ブランチ: `prototype-0.3`
対象ページ: `fullbody-bone-opacity-diagnostic-v0.4.html`
元ファイル: `fullbody-bone-opacity-diagnostic-v0.3.html`（blob `12236f121eb09a015696f2d070c88da9039b8da7`）

## コードで確定した不具合

v0.3 の `diagnosticFit()` では、存在しない `targetRoot` を `THREE.Box3().setFromObject(targetRoot)` に渡していた。この処理が実行されると ReferenceError でカメラの初期調整が途中停止する。以前実施した静的なJavaScript構文検査だけでは、未定義の変数参照は検出できなかった。

この不具合がiPhoneで実際にどの表示結果を起こしたかは、v0.3の新しい実機録画がないため未判定。

## 修正内容

- `fullSkeleton` と `fullAnatomy` の両方について `Box3().setFromObject(...)` を計算し、`union()` で結合した範囲を初期表示の基準にする。
- 空・無効なBox3の場合は診断パネルにエラーを表示し、不正なカメラ位置を設定しない。
- v0.3で統一した「両GLBの読み込み完了後に一度初期視点を設定する」流れは維持する。
- A/B/C/Dの比較、骨だけ/筋と骨、透明度スライダー、中央へ戻す操作は残す。

## 実施した検査

- JavaScript構文検査: 通過。
- `targetRoot` の未定義参照が残っていないこと: 確認。
- 実際の `diagnosticFit()` 関数を、Three.jsの必要な機能だけを模した独立テストで呼び出す実行確認: 通過。
- GitHub上の原本 `index.html` とGLBは更新しない。
- iPhone実機での最新画面表示・透明度比較: **未確認**。

## 次の判定

iPhoneでv0.4を開いて、(1)初期全身表示 (2)「全身を中央に」 (3)骨だけで透明度変更 (4)AとBの同条件比較、を確認する。その結果が出るまでは本体 `index.html` への反映をしない。
