---
name: experiment-loop-runner
description: 学習実験を回し、log と metrics を要約し、summary をもとに次の打ち手を決め、必要なコード修正を入れ、再度実験を回す流れを反復する skill。target validation accuracy などの停止条件に到達するまで、training-log-summarizer、experiment-next-step、experiment-code-updater を連携させてループ運用したいときに使う。実験自動反復、改善サイクル管理、到達目標つきの実験運用、比較可能性を保ちながら反復改善したいときに使う。
---

# Experiment Loop Runner

## Overview

既存の experiment skill 群を束ねて、実験の実行から改善、再実行までを反復する。
この skill の主目的は、目標 validation accuracy に向かって改善ループを管理することにある。各ステップの専門作業は既存 skill に委譲しつつ、停止条件、比較可能性、実験履歴の整合性を保つ。

## Managed Skills

この skill は次の skill を順に使う前提で動く。

- `training-log-summarizer`: 実験結果の要約
- `experiment-next-step`: 次の仮説と実験案の決定
- `experiment-code-updater`: 実験案のコード化

この skill 自体は、それらの実行順序とループ条件を管理する。

## Inputs

最低限、次を受け取る。

- target validation accuracy
- 現在のコードベース
- baseline 実行コマンドまたは実験開始コマンド
- 実験保存先
- 許容する最大 iteration 数
- 計算資源や時間制約

あると良い追加情報は次。

- 比較対象にしたい baseline run
- 優先したい改善軸: optimizer、model、loss、augmentation など
- 触ってよいファイル範囲

## Loop Workflow

1. 現在のコードで実験を 1 本実行する。
2. `training-log-summarizer` で結果を要約する。
3. target に届いたかを確認する。
4. 未到達なら `experiment-next-step` で次の実験案を 1 個選ぶ。
5. `experiment-code-updater` でその案をコードへ反映する。
6. 変更後の smoke test を行う。
7. 新しい run 名で再実験する。
8. iteration budget または目標到達まで繰り返す。

## Stop Conditions

以下のいずれかで停止する。

- validation accuracy が target 以上に到達した
- 最大 iteration 数に達した
- 改善幅が小さく、これ以上の反復に根拠が薄い
- 変更が比較不能なほど大きくなりそう
- 追加調査や人の判断が必要になった

停止時には、なぜ止めたかを明示する。

## Iteration Rules

各 iteration で守ること。

- 1 iteration では主変更を 1 つに絞る
- baseline は残す
- run ごとに別の output_dir を使う
- 何を変えた run か分かる命名にする
- summary、提案、コード変更、実行コマンドを記録する
- smoke test run は配線確認として扱い、本番の改善判断にはフル run を優先する

複数変更をまとめるのは、単独変更で十分な改善が見えない場合に限る。

## Execution Discipline

実験実行前に次を確認する。

- 実行コマンドが比較可能な条件になっている
- 出力先が上書きされない
- 新しい引数や分岐が smoke test で通っている
- checkpoint や history 出力が壊れていない

実験実行後は次を残す。

- run 名
- 実行コマンド
- 最終 validation accuracy
- best validation accuracy
- 採用した変更点
- 次の判断理由

## Output Format

各 iteration の返答は次の形を基本にする。

### Iteration Status

- iteration 番号
- 実行した run
- 現在の best validation accuracy
- target validation accuracy
- 継続か停止か

### Summary

- `training-log-summarizer` の要点だけを短く載せる

### Chosen Next Step

- `experiment-next-step` で選んだ実験案を 1 つ明示する
- なぜそれを選んだかを書く

### Code Update

- `experiment-code-updater` で入れる変更を明示する

### Next Run Command

- 次に回すコマンドをそのまま出す

## Boundaries

この skill は以下を主目的にしない。

- 長い論文調査
- 一度に多数の実験を並列設計すること
- 変更理由のない大規模リファクタ
- 人間の承認が必要な危険な自動変更

不確実性が高い場合は、ループを止めて論点を整理して返す。

## Output Quality Rules

- iteration ごとに何が変わったかを明確にする
- target 到達だけでなく、再現性と比較可能性を守る
- 改善しないループを惰性で続けない
- 必要なら早めに web 調査や人判断へエスカレーションする
- 実験履歴をあとで追える形で残す
