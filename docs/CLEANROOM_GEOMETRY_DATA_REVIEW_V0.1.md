# Clean-room形状用データ候補の利用条件レビュー v0.1

確認日: 2026-10-15  
結論: 調べた第三者座標・メッシュは造形に取り込まない。定義表と最新版ヘッダーの確認を終え、今回の5筋配置には不採用とした。

## 先に守る条件

- 既存3Dモデルの形状、画像、頂点を複製・変形・トレースしない。
- 学術データを使う場合は、データ本体の利用条件、必要な帰属表示、元計測の対象範囲、ランドマーク定義をすべて確認してから使う。
- 「公開ダウンロード可能」は「再利用・商用配布可能」と同じ意味ではない。
- 法的に最低限必要な表示が製品に必要となるデータを、表示要件の確認なしに本番素材へ取り込まない。

## 調査候補

### Recherche Data Gouv: 3D anatomic landmarks

- Claudio Vergari, 2026, DOI: https://doi.org/10.57745/TJJLD6
- 813名の健常者を立位で二方向X線撮影し、脊柱・骨盤・下肢の骨性ランドマーク座標を記録したデータ。説明ページにはEtalab Open Licence 2.0（CC BY 2.0と互換）と表示され、座標データファイルとランドマーク定義表が公開されている。
- Etalab Open Licence 2.0本文は商用・非商用の利用を認める一方、出典・作者などの帰属条件を課す。費用なしの利用権は確認できるが、帰属表示をゼロにはできない。
- 定義表（file ID 723126）と最新v2.0 CSVの先頭行（file ID 770788）を取得・照合した。最新版は2026-09-17公開。骨盤関連の7点の列はあるが、必要な坐骨棘・坐骨結節・閉鎖膜付着面・筋腱停止面の明示列はない。参加者の座標行は取得・使用していない。
- 判断: 今回の5筋形状・付着位置を定めるデータには不採用。識別子・応答ハッシュ・不足点を `assets/cleanroom/landmark-fit-audit.v0.1.json` に保存。

### MedPelvis3D（Zenodo v3.0.0）

- DOI: https://doi.org/10.5281/zenodo.21757686
- 99例の骨盤CT、ランドマークCSV、骨盤STLなどを公開。ページには座標の単位とLPS座標規約、測定誤差評価が記載される。
- 現在確認できるZenodo Rights欄は “Copyright (C) 2026 The Authors.” とだけ表示し、明確な再利用ライセンス名が記載されていない。GitHub上の説明にはCC BY 4.0との記述も見つかったが、権利者の一次配布元メタデータとの不一致を解消できていない。
- 判断: 権利者がZenodo記録へ明示ライセンスを設定するか、書面で許諾条件を確認できるまで、メッシュ・座標とも使わない。

### TCIA Pelvic-Reference-Data

- DOI: https://doi.org/10.7937/TCIA.2019.WOSKQ5OO
- 58例のCT/CBCT画像ペアと、位置合わせ検証用の選択ランドマーク座標。該当の座標ファイルはCC BY 3.0と表示され、データセット引用が案内されている。
- 目的は画像ペアの剛体位置合わせを評価すること。解剖学的な骨指標を統一定義した標準座標データかは確認できず、筋起始・停止を直接置く用途には不適合と判断。
- 判断: 独自3D形状のランドマーク根拠には採用しない。

## 次の確認

1. まずEtalabデータのランドマーク一覧・定義を確認し、筋付着に必要な点が含まれるか判定する。
2. 含まれない場合は、既存メッシュ・スキャン図を参照せず、査読論文にある骨性位置と数値計測の文章事実だけで作れる範囲を明確にする。
3. Etalabを使う場合は正確な帰属文、出典リンク、データの改変有無を整理し、控えめな画面表示で条件を満たせるか決める。表示条件を満たせないなら使わない。
4. どの経路でも、解剖学監査前に形状を「正確」と表示しない。

## 参照

- Dataset record: https://entrepot.recherche.data.gouv.fr/dataset.xhtml?persistentId=doi:10.57745/TJJLD6
- Etalab Open Licence 2.0: https://www.etalab.gouv.fr/wp-content/uploads/2018/11/open-licence.pdf
- MedPelvis3D v3.0.0 Zenodo record: https://zenodo.org/records/21757686
- TCIA dataset page: https://wiki.cancerimagingarchive.net/display/Public/Pelvic-Reference-Data

内部の制作・権利条件の照合記録。法的意見や個別許諾確認の代用ではない。


## 追記: データ配布記録と処理コードのライセンスを分ける

- Recherche Data Gouv のデータ記録は、ランドマーク座標データにEtalab Open Licence 2.0を表示している。
- 付属GitHubリポジトリ `IBHGC/3D-anatomical-landmarks` は、データ処理コードのREADMEとLICENSEにCC BY-SA 4.0を表示している。READMEにはコードがデータを自動取得するとある。
- これはデータ本体の記録とは別の対象として整理する。座標CSVの再利用条件はデータ記録のEtalab表示を参照する。コードは本アプリへ取り込まない。座標データにコードライセンスが及ぶか等、資料の対象範囲を超えた法的判断はしない。
- 追記時は定義表未読だったが、その後に定義表・最新版CSVヘッダーを実取得して照合済み。今回の5筋配置には不採用と確定。
- 参照: https://entrepot.recherche.data.gouv.fr/dataset.xhtml?persistentId=doi:10.57745/TJJLD6 、https://github.com/IBHGC/3D-anatomical-landmarks/blob/main/README.md 、https://github.com/IBHGC/3D-anatomical-landmarks/blob/main/LICENSE


## 形状試作へ進んだ経路（2026-10-15）

座標データの不採用後、Wellcome CollectionがPublic Domain Markとして公開する1858年版Gray/Carter原資料を確認。外部モデルのメッシュ・頂点・スキャン座標を使わず、右大腿骨近位部の模式形状を今回記述したコードで生成した。造形パラメータは測定済み人体座標とは扱わず、学習用への採用前に監査する。詳細は `docs/CLEANROOM_FEMUR_STUDY_V0.1.md`。
