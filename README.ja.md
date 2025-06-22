# Proxy Hunter

[English Version](README.md) | [中文版はこちら](README.zh-TW.md)

## 概要

Proxy Hunter は、無料プロキシリストサイト [Free Proxy List](https://free-proxy-list.net/) からプロキシを取得し、その有効性をテストする Python ツールです。正規表現を用いて IP アドレスを収集し、[ipify](https://www.ipify.org/) を利用して検証します。開発者やセキュリティアナリストが素早く信頼できるプロキシを得るために役立ちます。

## 特徴

- **無料プロキシの取得**: Free Proxy List から自動でプロキシを取得
- **プロキシの検証**: 取得したプロキシの接続確認
- **出力ファイル指定**: 結果を好きなファイルに保存可能
- **ファイルからの検証**: 指定ファイル内のプロキシを検証
- **スレッド数設定**: 検証に利用するスレッド数を指定
- **匿名プロキシフィルタ**: 実 IP を隠すプロキシのみを保持可能
- **柔軟な出力形式**: テキストまたは JSON 形式で保存

## インストール

```bash
pip install -r requirements.txt
```

## 使い方

```bash
python -m proxyhunter
```

## ウェブダッシュボード

```bash
python -m proxyhunter.web_app
```

## ライセンス

MIT ライセンスの下で配布されています。
