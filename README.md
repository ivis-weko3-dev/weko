# README.md

## ディレクトリ構造(整理中)

```
.
├── build                            : 環境構築用ファイル
│   ├── data                         : 環境構築用データ
│   ├── images                       : Dockerイメージ
│   ├── scripts                      : 環境構築スクリプト
│   └── README.md                    : 構築手順
├── modules                          : モジュール（イメージに含める）
│   ├── cookiecutter-weko-module
│   ├── invenio-accounts
│   ├── ~省略~
│   └── weko-workspace
├── tools                            : ツール（イメージに含める）
├── utils                            : その他のツール（イメージに含めない）
├── update                           : アップデート用ファイル
│   ├── x.x.x                        : 一つ前からのアップデート用ファイル（イメージに含める）
│   └── old                          : 過去のアップデート用ファイル（イメージに含めない）
│       └── x.x.x 
└── 

```