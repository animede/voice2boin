# voice2boin

日本語音声ファイル + 読み上げ原稿テキストから、母音(a/i/u/e/o、任意で撥音N)の
出現タイミングを抽出するツールです。VTuber/アバターのリップシンク(口パク)用データ
生成を主な用途としています。

ASRは行わず、テキスト(正解が既知)と音声を強制アライメントする方式を採用しています。

## 構成

- `vowel_extractor/`: ライブラリ本体
  - `text_to_phoneme.py`: `pyopenjtalk` によるテキスト→音素列変換
  - `aligners/`: 強制アライメント実装
    - `base.py`: `Aligner` 抽象基底クラス
    - `mock_aligner.py`: デモ・テスト用のダミー実装(音声全長を音素数で均等割り)
    - `julius_aligner.py`: Julius + julius4seg を用いた本番用実装
  - `extractor.py`: `VowelTimingExtractor`(テキスト→音素変換 + アライメントを統合)
- `server/`: FastAPIによるWeb API・UI
- `tests/`: pytestによるテスト

## セットアップ

```bash
pip install -r requirements.txt
```

pyopenjtalk はビルドに時間がかかることがあります。

## ライブラリとしての使い方

```python
from vowel_extractor import VowelTimingExtractor
from vowel_extractor.aligners import MockAligner

extractor = VowelTimingExtractor(aligner=MockAligner())
result = extractor.extract("path/to/audio.wav", "こんにちは")

for seg in result.vowel_segments:
    print(seg.vowel, seg.start, seg.end, seg.duration)

print(result.to_json(indent=2))
```

本番精度で使う場合は `JuliusAligner` を使用してください(下記セットアップが必要です)。

```python
from vowel_extractor.extractor import VowelTimingExtractor
from vowel_extractor.aligners.julius_aligner import JuliusAligner

extractor = VowelTimingExtractor(aligner=JuliusAligner())
result = extractor.extract("path/to/audio.wav", "こんにちは")
```

撥音(N)も抽出したい場合:

```python
extractor = VowelTimingExtractor(aligner=MockAligner(), include_n=True)
```

## テストの実行

```bash
pytest tests/
```

## サーバの起動

```bash
uvicorn server.app:app --reload
```

起動後、ブラウザで `http://localhost:8000/` を開くとUIが利用できます。

### API

`POST /api/analyze` (multipart/form-data)

| フィールド | 必須 | 説明 |
|---|---|---|
| `audio` | ○ | 音声ファイル(wav) |
| `text` | ○ | 読み上げ原稿テキスト |
| `mode` | - | `"mock"`(デフォルト) または `"julius"` |

レスポンス例:

```json
{
  "vowel_segments": [
    {"vowel": "o", "start": 0.11, "end": 0.22, "duration": 0.11}
  ],
  "phoneme_segments": [
    {"phoneme": "k", "start": 0.0, "end": 0.11, "duration": 0.11}
  ]
}
```

## Juliusのセットアップ(JuliusAligner を使う場合)

`JuliusAligner` は本番精度の強制アライメントのため、以下のセットアップが必要です。
このリポジトリ・セッションでは重いためインストールを行っていません。

1. Julius本体をビルド、またはバイナリを用意する
   - https://github.com/julius-speech/julius
2. 日本語音響モデル(dictation-kit等)を入手する
   - https://osdn.net/projects/julius/downloads/ 等
3. julius4seg をインストールする
   ```bash
   pip install git+https://github.com/Hiroshiba/julius4seg
   ```
4. 以下の環境変数を設定する

   | 環境変数 | 説明 |
   |---|---|
   | `JULIUS_BIN` | julius実行バイナリへのパス(必須) |
   | `JULIUS_HMM` | 音響モデルファイルへのパス(必須) |
   | `JULIUS_HMMLIST` | HMMリストファイルへのパス(必須) |
   | `JULIUS_HMM_MODEL` | モデル種別(任意) |
   | `JULIUS_CONFIG` | julius設定ファイル(.jconf)へのパス(任意) |

環境変数が不足している場合、`JuliusAligner` は分かりやすいエラーメッセージ(この
READMEを参照するよう促すメッセージ)を出して失敗します。
