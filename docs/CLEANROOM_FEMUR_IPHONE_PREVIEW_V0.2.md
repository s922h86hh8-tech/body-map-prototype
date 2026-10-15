# iPhone添付HTMLプレビューの空白とWeb検証版 v0.2

日付: 2026-10-15  
対象: 右大腿骨近位部の独自形状試作。形状自体はv0.1のまま。

## 実際に確認した症状

ユーザーから届いた約12.57秒のiPhone録画では、見出し・説明・ボタンは表示されるが、3D領域は空白だった。画面上部にHTMLファイル名と閉じるUIが見えるため添付ファイルプレビューと推定するが、録画だけではJavaScriptの実行可否や正確な原因は断定できない。この録画をもってiPhoneで3Dが正常動作したとは扱わない。

## 今回の対応

- 添付HTMLの案内から、通常のWebページを開く方式へ変更する。
- 公開済みのGitHub Pagesが `prototype-0.3` から配信されていることを、直近のdeployment/runとブランチ参照で確認した。
- 新規の独立検証ページ `experiments/cleanroom-femur-study-v0.2.html` のみを公開する。本体ページのリンク・モデルURL・既存GLBを変更しない。
- 検証URL: https://s922h86hh8-tech.github.io/body-map-prototype/experiments/cleanroom-femur-study-v0.2.html
- 起動中の案内を表示し、3Dを開始したら取り除く。
- JavaScript無効時には、空白だけにせず「Web版をブラウザで開く」リンクを表示する。スクリプトが除去される等の環境でも、初期HTMLの案内リンクが残る設計。
- 制作記録のリンクは、公開ブランチに存在しない相対Markdownリンクから、保存ブランチのGitHub URLへ変更した。
- v0.1 HTML、新規glTF、造形パラメータは維持する。v0.2は配信・表示案内の変更であり、骨の形状や精度の改訂ではない。

## 検証

Chromium 155.0.8059.79で、通常表示、方向切替、タッチ回転・拡大縮小、リセット、glTF保存、狭い画面、WebGL非対応時を再確認した。さらにJavaScriptを無効化し、案内とWeb版リンクが見えることを確認した。結果: `docs/validation/cleanroom-femur-v0.2.json`。

GitHub Pagesへ保存した後、HTTP応答・配信内容・Web表示を別途確認する。公開反映状況は設計台帳に追記する。

## 未確認

- 新しいWeb URLをiPhone Safariで開いた場合の実機表示・操作。
- 解剖学的な形状・寸法の正確性。今回の変更で解決したとは扱わない。
