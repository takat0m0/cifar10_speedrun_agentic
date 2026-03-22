---
name: experiment-code-updater
description: experiment-next-step などが提案した実験案を、実際の学習コード変更に落とし込んで実装する skill。loss 関数の変更、optimizer や scheduler の変更、augmentation の追加、base network の差し替え、設定引数の追加、checkpoint や log 出力の更新など、実験を実行できる状態までコードを直したいときに使う。提案の意図を保ちつつ、比較しやすく安全な最小変更で実装したいときに使う。
---

# Experiment Code Updater

## Overview

実験提案を、比較可能で再実行しやすいコード変更に変換する。
この skill はアイデア出しではなく実装に集中する。変更理由を理解したうえで、既存の学習パイプラインに最小限の差分で組み込む。

## Workflow

1. 変更要求を実験単位で読む。
2. どのファイルと API に触るべきか特定する。
3. 比較を壊さない最小変更に分解する。
4. 学習コード、設定、CLI、保存物を必要に応じて更新する。
5. 変更後の実行経路を smoke test する。
6. 比較時の注意点を短く残す。

## Inputs

優先して使う入力は次。

- `experiment-next-step` の推奨実験
- 実験 summary とその根拠
- 現在の学習コード
- 既存 CLI や設定引数
- 保存中の checkpoint や metrics 形式

要求が曖昧な場合でも、まずは 1 実験 1 変更の形に落とす。
複数の実験変更をまとめて同時に入れない。

## Step 1: Map Proposal to Code

提案をコード上の変更点に翻訳する。

例:

- `loss を cross entropy から label smoothing 付きに変える`
  - `train.py` の criterion 構築と CLI 引数を更新する
- `optimizer を SGD から AdamW に変える`
  - optimizer 構築部と関連ハイパーパラメータを更新する
- `scheduler を変える`
  - scheduler 構築部、必要なら warmup や step 単位処理を更新する
- `ResNet から ResNeXt に変える`
  - `models.py` の model factory と CLI/model 選択引数を更新する
- `augmentation を強める`
  - `data.py` の transform 構築や設定引数を更新する

## Step 2: Preserve Comparability

実験比較を壊さないように次を守る。

- 変更対象は要求に直接関係する範囲に絞る
- 既存の baseline を壊さない
- 可能なら新しい引数や分岐で切り替え可能にする
- 既存の保存形式をむやみに壊さない
- 互換性を壊す場合は明示する

デフォルト動作を変えるなら、その理由が必要。
比較目的なら、まずは opt-in な引数追加を優先する。

## Step 3: Update Interfaces

必要に応じて次を更新する。

- model factory
- dataloader / transforms
- criterion
- optimizer
- scheduler
- CLI 引数
- checkpoint 保存項目
- metrics 出力
- baseline 実行スクリプト

実験実行に必要な入口が揃っていることを確認する。
コードだけ直して CLI から使えない状態にしない。

## Step 4: Validate

少なくとも次を確認する。

- import が通る
- CLI から新しい設定が指定できる
- 1 step あるいは 1 epoch の smoke test が通る
- checkpoint / history 出力が壊れていない

変更が大きい場合でも、まずは軽い検証を優先する。

## Step 5: Report

返答では次を明確にする。

- 何を変えたか
- どの実験提案をコード化したか
- baseline と何が切り替え可能か
- 実行コマンド例
- 互換性上の注意点

## Boundaries

この skill は以下を主目的にしない。

- 実験案の優先順位付け
- 長いログ要約
- 論文調査や web 調査
- 根拠のない大規模リファクタ

方向性が未確定なら、まず `experiment-next-step` で案を固める。
その後でこの skill を使って実装する。

## Output Quality Rules

- 変更理由と変更箇所を対応付ける。
- 可能なら baseline を保ったまま新オプションで追加する。
- 1 回の変更で比較不能なほど多くを変えない。
- 互換性破壊がある場合は必ず明記する。
- 実行コマンドまで提示して、すぐ試せる状態にする。
