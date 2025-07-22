# aichallenge-2025

本リポジトリでは、2025年度に実施される自動運転AIチャレンジでご利用いただく開発環境を提供します。参加者の皆様には、Autoware Universe をベースとした自動運転ソフトウェアを開発し、予選大会では End to End シミュレーション空間を走行するレーシングカートにインテグレートしていただきます。開発した自動運転ソフトウェアで、安全に走行しながらタイムアタックに勝利することが目標です。また、決勝大会では本物のレーシングカートへのインテグレーションを行っていただきます。

This repository provides a development environment use in the Automotive AI Challenge which will be held in 2025. For the preliminaries, participants will develop autonomous driving software based on Autoware Universe and integrate it into a racing kart that drives in the End to End simulation space. The goal is to win in time attack while driving safely with the developed autonomous driving software. Also, for the finals, qualifiers will integrate it into a real racing kart.

## ドキュメント / Documentation

下記ページにて、本大会に関する情報 (ルールの詳細や環境構築方法) を提供する予定です。ご確認の上、奮って大会へご参加ください。

Toward the competition, we will update the following pages to provide information such as rules and how to set up your dev environment. Please follow them. We are looking forward your participation!

- [日本語ページ](https://automotiveaichallenge.github.io/aichallenge-documentation-2025/)
- [English Page](https://automotiveaichallenge.github.io/aichallenge-documentation-2025/en/)


# TPAC ブランチ運用ルール
## 🔀ブランチ構成
| ブランチ名                | 用途・役割                                     |
| -------------------- | ----------------------------------------- |
| `main`               | **大会公式リポジトリの追従用ブランチ**（原則、直接開発しません）|
| `develop`            | **チーム内の統合成果物ブランチ**。`main` から取り込みつつ各機能を統合。|
| `feature/control/*`  | 制御機能（例：simple pure pursuit, MPC,　強化学習など）の開発用|
| `feature/planning/*` | 経路計画機能（例：Vectormap最適化, accel/break.csv最適化, 経路最適化など）の開発用|
| `feature/eval/*`     | 自動評価・ログ解析等の評価機能の開発用(例 パラメータ最適化, 自動評価ツール)の開発用|
| `feature/integ/*`     | 機能統合用|

## 🧭 　開発フロー
```
大会公式 → main → develop ← feature/integ/* ← 各機能ブランチから統合
```
- main: 公式リポジトリを追従するためのブランチ。直接開発は行いません。
- develop: チーム内での開発成果を統合するブランチ。main の変更もここに取り込みます。
- feature/*: 機能ごとにブランチを作成して開発を行い、最適なタイミングでdevelopブランチにマージします。
- feature/integ/*: develop をベースにして、機能統合を行います。予選評価サーバへの提出もこちらのブランチからしてもOKです。

## 📝　命名規則
各featureブランチは判別できるように以下の命名ルールに従ってください。
```
feature/<機能カテゴリ>/<機能名>_<識別子>
```
| 種類      | 例                                   |
| ------- | ----------------------------------- |
| 制御機能    | `feature/control/simple_pure_pursuit_tanaka`|
| 経路計画    | `feature/planning/vectormap_optimize_yamada`|
| 評価機能    | `feature/eval/log-visualizer_v1`|
| 機能統合・提出 | `feature/integ/submit_20250701_tanaka` |

※識別子には、アカウント名 / バージョン番号 / チーム名略称などを使用してください。

## ✅　コミット・PRルール
- コミットは小さく、できるだけ意味のある単位で行ってください.
- PR（プルリクエスト）はチームのレビューを経て develop にマージします。
- 統合時は各自で統合する機能ブランチをマージし、feature/integ/* ブランチとしてプッシュしてください

### 🚧 Pull Request の送り先に注意！

本リポジトリは Fork 運用しています。
GitHub の「Compare & pull request」ボタンを押すと、Fork元（Upstream）に対してPRを送ろうとしてしまう場合があります。

以下の手順で、**Pull Requestの送信先が自分のリポジトリであること**をご確認ください。

1. GitHubでPull Requestを作成
2. 上部の「base repository」が `YourUsername/YourRepo` になっているか確認
3. 違う場合は `base repository` をクリックして、自分のリポジトリを選び直してください

# 📣　運用相談とルールの更新について
マージ・プッシュ・プルリクエストなどの運用判断に迷った場合は、Discordの”リポジトリ管理用チャンネル”で相談してください！！
チームの状況や大会の進行に応じて、運用ルールは柔軟に見直し・更新していく方針です。

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/ChallengeClub/aichallenge-2025)
