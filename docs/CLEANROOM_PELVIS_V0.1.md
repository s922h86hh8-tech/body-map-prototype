# Clean-room 3D試作仕様：殿部深層5筋 v0.1

日付: 2026-10-15
作業ブランチ: cleanroom-pelvis-v0.1
目的: 既存GLBの形状を使わず、文章資料から確認できる解剖学的事実をもとに独自の3D試作を始める。

## 権利・制作上の制約

- 既存3Dモデル、GLB、メッシュ、頂点、スクリーンショットを形状の手本や座標抽出元にしない。
- 現行アプリは必要な操作・表示機能を確認する目的に限って参照する。
- 筋名、骨指標、起始・停止・走行など確認済みの事実から設計し、形状表現・分割・色・画面説明は独自に作成する。
- 既存の寸法を調査なしに当てはめない。資料間で差がある記述と個体差は個別に記録する。
- このファイルとJSONは調査・設計資料。解剖学的に監査済みの3Dモデルではない。

## 試作範囲

梨状筋、内閉鎖筋、上双子筋、下双子筋、大腿方形筋。各筋の確認済み付着・走行は `assets/cleanroom/deep-gluteal-facts.v0.1.json` に記録する。

## 今回確定した設計上の事実

- 内閉鎖筋・上双子筋・下双子筋は、共同腱を形成して大転子内側へ向かう代表形で表す。
- 梨状筋は仙骨前面から大坐骨孔を通り、大転子上部へ向かう代表形で整理する。停止腱の合流などは変異があるため固定しない。
- 大腿方形筋は坐骨結節から転子間稜・方形結節近傍へ向かう別筋として扱う。
- 5筋の上下関係は概略表示に使うが、深さ・奥行きは資料照合と独立形状レビューを経て設定する。

## 未確定のまま残す項目

- 骨盤・大腿骨の三次元座標と寸法
- 筋腹の幅、厚さ、断面、曲率、腱へ移る位置
- 個体差を代表形にどう反映するか
- 独自形状が施術者向け学習に十分な解剖学的精度を持つか

上記を推測で埋めず、資料照合を先に行う。既存アプリと元GLBは変更しない。公開ページへの掲載もしない。

## 参照資料

- StatPearls, Piriformis Muscle: https://www.ncbi.nlm.nih.gov/books/NBK519497/
- Carro et al., Deep gluteal space problems: piriformis syndrome and other entrapments: https://pmc.ncbi.nlm.nih.gov/articles/PMC5193530/
- StatPearls, Obturator Muscles: https://www.ncbi.nlm.nih.gov/books/NBK589636/
- StatPearls, Gemelli Muscles: https://www.ncbi.nlm.nih.gov/books/NBK557420/
- Hip impingement: beyond femoroacetabular: https://pmc.ncbi.nlm.nih.gov/articles/PMC4765300/
- Surgically Relevant Bony and Soft Tissue Anatomy of the Proximal Femur: https://pmc.ncbi.nlm.nih.gov/articles/PMC4555602/

注: 画面用の参考文献欄ではなく、独自制作と解剖学監査のための内部記録。
