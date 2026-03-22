---
name: training-log-summarizer
description: 学習実験のログ、history.jsonl、history.csv、標準出力、checkpoint 周辺の指標を読み取り、学習の経過と最終結果を短く構造化して要約する skill。学習中の accuracy/loss の推移、最終的な validation accuracy や test accuracy、過学習・学習不足・発散の兆候、気になる点、次に分析すべき論点を整理したいときに使う。実験結果のサマリ作成、ログの読み解き、結果比較の前処理、次の意思決定のための観測整理で使う。
---

# Training Log Summarizer

## Overview

学習実験の出力を読んで、結果を人がすぐ判断できる短い summary に整理する。
この skill は観測事実の整理に集中し、詳細な打ち手の探索や web 検索は行わない。必要なら、そのための入力になる summary と論点一覧を作る。

## Workflow

1. 実験の入力を特定する。
2. 学習経過と最終結果を抽出する。
3. 異常や気になる点を列挙する。
4. 次に検討すべき論点を整理する。
5. 再利用しやすい短い summary を返す。

## Step 1: Gather Inputs

優先して読む対象を確認する。

- `history.jsonl`
- `history.csv`
- 学習の標準出力ログ
- checkpoint に含まれる `metrics` や `history`
- 実験設定が分かる CLI 引数や設定ファイル

複数ある場合は、まず最新 run と比較対象 run を分けて扱う。
ファイルが欠けている場合は、あるものだけで要約し、欠損を明記する。

## Step 2: Extract Facts

最低限、次を抽出する。

- 実験名または run 名
- epoch 数
- train accuracy / validation accuracy / test accuracy の最終値
- 可能なら best validation accuracy とその epoch
- loss の増減傾向
- learning rate の変化が分かるならその概要
- 学習時間や epoch あたり時間

推測と事実を混ぜない。
数値は可能な限りそのまま使う。

## Step 3: Identify Patterns

次の観点で観測を整理する。

- train は上がるが validation が伸びない: 過学習の疑い
- train/validation ともに低い: 学習不足、capacity 不足、最適化不足の疑い
- loss や accuracy が大きく揺れる: 学習率や batch 条件の不安定さの疑い
- validation と test の乖離が大きい: split や評価条件の差異の可能性
- 改善が早期に頭打ち: scheduler、augmentation、model size を後で検討する余地

ここでは診断を断定しない。
「兆候」「可能性」「追加で見るべき点」として表現する。

## Step 4: Produce Output

出力は短く構造化する。基本フォーマットは次を使う。

### Experiment Summary

- Run: `<run-name>`
- Epochs: `<n>`
- Final train accuracy: `<value>`
- Final validation accuracy: `<value>`
- Final test accuracy: `<value>`
- Best validation accuracy: `<value>` at epoch `<k>`

### Trend Summary

- 学習の進み方を 2-4 文で要約する。
- どこで改善が止まったか、train/validation/test の関係を述べる。

### Notable Issues

- 気になる点を 1-4 個並べる。
- 事実と解釈を分ける。

### Open Questions

- 次の意思決定のために追加で見たい点を 1-5 個並べる。
- ここでは具体的な実験計画に踏み込みすぎない。

## Boundaries

この skill は以下を主目的にしない。

- web 検索による改善策調査
- 論文や既存実装の調査
- 次の実験計画の優先順位付けを深く行う
- コード変更の実装

ユーザーが改善策や次の実験案まで求める場合でも、まず summary を返し、その後に別 skill へ渡せる材料を揃える。

## Output Quality Rules

- 数値は丸めすぎない。必要なら小数 3-4 桁程度まで残す。
- 根拠がないことは言わない。
- 欠損データがあれば明示する。
- 複数 run を比較する場合は、各 run の差分を同じ指標で並べる。
- 長いログをそのまま貼らず、要点だけ抜く。
