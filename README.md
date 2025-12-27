# Bokicast MCP Server

**Presented by Aska Lanclaude**  
Bokicast MCP Server is an MCP server designed for a brand-new style of bookkeeping study.
mcp-name: io.github.lambda-tuber/bokicast-mcp-server

---

## 概要

簿記キャストは、AITuber の霊夢と魔理沙による簿記勉強会を支援するために開発した MCP サーバです。
問題演習や解説を行う際、仕訳や計算結果を口頭だけで説明するのではなく、視覚的に確認できることを重視しています。

本サーバでは、仕訳、T 字勘定、残高試算表といった簿記の基本要素をビジュアライズし、表示・操作することができます。
これにより、学習の流れに合わせて情報を整理しながら解説を進めることが可能になります。

また、MCP サーバとして実装しているため、AI である霊夢や魔理沙自身がこれらの表示や操作を行えます。
人が裏で操作する必要がなく、キャラクターが自律的に説明し、問題を解いていく形の簿記勉強会を実現します。

---


## Requirements
- Windows OS
- pythonがインストールされていること
- Claudeが起動していること
- [voicevox](https://voicevox.hiroshiba.jp/)が起動していること

---

## インストール

1. pvv-mcp-serverのインストール
    ```bash
    > pip install bokicast-mcp-server
    ```

2. MCPBのインストール  
- [リリースアセット](https://github.com/lambda-tuber/bokicast-mcp-server/tags)よりMCPBファイルをダウンロードし、Claudeにドロップする。

---

## Youtube 動画一覧
この動画は、音声対話MCP「pvv」を使って制作された簿記学習バラエティです。  
東方Projectの霊夢と魔理沙が登場し、簿記の基礎から応用、過去問や例題まで、会話形式で楽しく学んでいきます。  
VOICEVOXによる自然な音声と、会話内容に合わせて表情が変わるアバターが特徴。  
AI×東方キャラによる、新感覚の簿記勉強会をお楽しみください。

- [シリーズまとめはこちら](https://www.youtube.com/playlist?list=PLML1P2WReMnmcc8C__lQsz3c_nBFaXRB_)

----

### 霊夢と魔理沙と簿記キャスト その1
#### 概要
霊夢と魔理沙と簿記の話をしてみた。  
問題を解いてもらって、解説してもらったよ。  
その他有価証券の追加取得。関連会社へ。  
#### 動画
[![霊夢と魔理沙と簿記キャスト その1](https://img.youtube.com/vi/As4WjiHkuFg/hqdefault.jpg)](https://youtu.be/As4WjiHkuFg)

----

### 霊夢と魔理沙と簿記キャスト その2
#### 概要
霊夢と魔理沙と簿記の話をしてみた。  
簿記の興味深い観点が話題になったよ。  
最終的に、試験合格を応援してもらった。  
テクニカルな観点で簿記システムを考察してみた。  
#### 動画
[![霊夢と魔理沙と簿記キャスト その2](https://img.youtube.com/vi/RWjC9qs6Z0k/hqdefault.jpg)](https://youtu.be/RWjC9qs6Z0k)

----

### 霊夢と魔理沙と簿記キャスト その3 ROI①
#### 概要
霊夢と魔理沙と簿記の話をしてみた。  
システム開発やSW開発のプロジェクトにおける損益計算について話題になったよ。  
そこから、管理会計の指標をどうしようか、相談てみた。  
#### 動画
[![霊夢と魔理沙と簿記キャスト その3](https://img.youtube.com/vi/z9cWy9uCwt4/hqdefault.jpg)](https://youtu.be/z9cWy9uCwt4)

----

### 霊夢と魔理沙と簿記キャスト その4 ROI②
#### 概要
霊夢と魔理沙と簿記の話をしてみた。  
システム開発やSW開発のプロジェクトにおける損益計算について話題になったよ。  
そこから、管理会計の指標をどうしようか、相談てみた  
#### 動画
[![霊夢と魔理沙と簿記キャスト その4](https://img.youtube.com/vi/QsGibtWQwDo/hqdefault.jpg)](https://youtu.be/QsGibtWQwDo)

----

### 霊夢と魔理沙と簿記キャスト その5 ROI③
#### 概要
霊夢と魔理沙と簿記の話をしてみた。  
システム開発やSW開発のプロジェクトにおける損益計算について話題になったよ。  
そこから、管理会計の指標をどうしようか、相談てみた  
#### 動画
[![霊夢と魔理沙と簿記キャスト その5](https://img.youtube.com/vi/dqPk61mCdwM/hqdefault.jpg)](https://youtu.be/dqPk61mCdwM)


----

### 霊夢と魔理沙と簿記キャスト その6 資産グループの減損
#### 概要
資産グループの減損損失の問題をやったよ。  
派生して、土地の減損について調べたけど、よくわからんかった。  
引き続き、調査することになったよ。  
#### 動画
[![霊夢と魔理沙と簿記キャスト その6](https://img.youtube.com/vi/HdYR-fcvXsk/hqdefault.jpg)](https://youtu.be/HdYR-fcvXsk)

----

### 霊夢と魔理沙と簿記キャスト その7 成果連結の調整仕訳
#### 概要
成果連結の仕訳問題をやったよ。  
建物に評価差額がある場合の減価償却の調整仕訳だね。  
#### 動画
[![霊夢と魔理沙と簿記キャスト その7](https://img.youtube.com/vi/OcJYMCeGFSo/hqdefault.jpg)](https://youtu.be/OcJYMCeGFSo)

----

### 霊夢と魔理沙と簿記キャスト その14
#### 概要
今回は「簿記キャスト」というMCPツールを作ったので、霊夢と魔理沙にお披露目してみたよ。  
このツールは、霊夢と魔理沙と一緒にやっている簿記の勉強会で、問題を解いたり説明したりするときに、画面上で仕訳や勘定の流れを確認できるものだよ。  
まずは、簡単な使い方を紹介するね。  
#### 動画
[![霊夢と魔理沙と簿記キャスト その14](https://img.youtube.com/vi/ksl0DX5ZdKw/hqdefault.jpg)](https://youtu.be/ksl0DX5ZdKw)


----

### 霊夢と魔理沙と簿記キャスト その15
#### 概要
今回は「簿記キャスト」というMCPツールを作ったので、霊夢と魔理沙にお披露目してみたよ。
- ✓ 貸借や損益の表(Box)は、高さが金額に比例して表示される。
- ✓ 期中でも、貸借と損益を合算すれば貸借が一致し、表(Box)の高さもそろう。
- ✓ 仕訳には貸借が一致しているかのバリデーションが組み込まれている。
- ✓ 試しに不正な仕訳を入力してみたところ、しっかりエラーで弾かれた。
- ✓ 簿記システムでは、貸借一致は仕訳段階で必須のチェック。
- ✓ 一方、T字勘定では残高が最も重要なポイントとなる。
#### 動画
[![霊夢と魔理沙と簿記キャスト その15](https://img.youtube.com/vi/W5aOI38Shyk/maxresdefault.jpg)](https://youtu.be/W5aOI38Shyk)

----

### 霊夢と魔理沙と簿記キャスト その16
#### 概要
今回は「簿記キャスト」というMCPツールを作ったので、霊夢と魔理沙にお披露目してみたよ。  
いじってたら一部バグも見つかっちゃったので、あとで直しておくね。
- ✓ 残高試算表の「残高」ってなに？
- ✓ 損益の利益を貸借へ振り替える仕組みのこと
- ✓ 損益計算書は経営成績、貸借対照表は財政状態を示す
- ✓ 売上・仕入などの勘定を締めて損益勘定を作成
- ✓ 損益勘定の残高を利益剰余金へ振り替え
- ✓ 最後に、決算報告として貸借対照表を作成する流れを
- ✓ ツールで一通りシミュレートしてみたよ 
#### 動画
[![霊夢と魔理沙と簿記キャスト その16](https://img.youtube.com/vi/ZGZjuHAIYbE/default.jpg)](https://youtu.be/ZGZjuHAIYbE)


----
