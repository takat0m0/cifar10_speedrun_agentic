---
name: experiment-next-step
description: 学習実験の summary や主要指標を受け取り、次に試すべき実験案、仮説、優先順位、比較条件、必要なら web 検索で確認すべき論点を整理する skill。training-log-summarizer などが作った要約をもとに、次の打ち手を決めたいとき、改善案を絞りたいとき、実験計画に落としたいとき、追加調査が必要か判断したいときに使う。
---

# Experiment Next Step

## Overview

学習実験の summary を入力として受け取り、次に打つべき実験を仮説ベースで提案する。
この skill は観測事実の再整理ではなく、次の意思決定に重点を置く。必要なら web 検索を使って候補の妥当性や既知の改善策を確認する。

## Workflow

1. 既存 summary と主要指標を読む。
2. ボトルネック仮説を 1-3 個に絞る。
3. 仮説ごとに小さく検証できる実験案を作る。
4. 優先順位を付ける。
5. 必要なら web 検索論点を定義し、追加調査を行う。
6. 実行しやすい次のアクションに落とす。

## Inputs

入力として優先するものは次。

- `training-log-summarizer` が作った summary
- `history.jsonl` や `history.csv` の主要数値
- 学習設定: model、optimizer、scheduler、augmentation、batch size、epoch 数
- 過去 run との比較結果
- ユーザーの制約: 計算資源、時間、比較したい条件

summary が無い場合は、必要最小限だけログを見て仮説形成に必要な事実を拾う。
ただし、詳細なログ読解そのものはこの skill の主目的ではない。

## Step 1: Form Hypotheses

観測から、まず主要な仮説を少数に絞る。

例:

- 過学習が主因
- 最適化が弱く、十分に学習できていない
- data augmentation が不足している
- model capacity が不足または過剰
- validation/test の取り方に問題がある
- scheduler や learning rate 設定が不適切

仮説は 1 回の返答で増やしすぎない。
通常は 1-3 個に絞る。

## Step 2: Propose Experiments

各仮説に対して、変更点が明確で比較しやすい実験案を出す。

各実験案には最低限次を含める。

- 何を変えるか
- なぜその変更がその仮説を検証できるか
- 成功したかを何で判断するか
- 比較対象は何か
- コストは軽いか重いか

複数変更を 1 実験に詰め込みすぎない。
まずは切り分けやすい実験を優先する。

## Step 3: Prioritize

優先順位は次の観点で付ける。

- 変更コストが低い
- 仮説検証力が高い
- 改善幅が期待できる
- 失敗しても学びが大きい
- 現在のボトルネックを直接叩いている

出力時は `High` / `Medium` / `Low` などの粗い優先度で十分。

## Step 4: Decide Whether to Search the Web

次のような場合は web 検索を使う。

- モデルや手法が最近の知見に強く依存する
- augmentation や optimizer の定番設定を最新の実践で確認したい
- speedrun 的な既知の強い baseline を確認したい
- そのタスク固有の一般的な改善パターンを確かめたい

検索時は、summary から作った仮説に直接関係する論点だけを調べる。
闇雲に広く調べない。

## Step 5: Produce Output

出力は次の形を基本にする。

### Current Read

- 現状を 2-4 文で再確認する。
- summary の要点だけを短く再掲する。

### Working Hypotheses

- 仮説を 1-3 個並べる。
- 各仮説は根拠と一緒に短く書く。

### Recommended Experiments

- `High` から順に 1-5 個並べる。
- 各項目に変更点、狙い、判断基準を書く。

### Optional Research Questions

- web 検索が有効なら、検索すべき論点を 1-5 個並べる。
- 検索不要なら、その旨を明記する。

### Next Action

- 直近で 1 つだけ着手するなら何かを明示する。

## Boundaries

この skill は以下を主目的にしない。

- 生ログ全体の詳細要約
- 実験結果の長文レポート化
- コード実装そのもの
- 根拠のない網羅的アイデア出し

ログの読解が必要なら、まず `training-log-summarizer` を使って summary を作る。
その後でこの skill を使って次の打ち手を決める。

## Output Quality Rules

- 実験案は比較可能な粒度で書く。
- 一度に変える要素はできるだけ少なくする。
- 仮説と推奨を明確に分ける。
- web 検索を使う場合は、何を確認したいのかを先に明確にする。
- 計算コストが高い案は、期待リターンが大きい場合だけ上位に置く。
