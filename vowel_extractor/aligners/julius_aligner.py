import os

from .base import Aligner
from ..types import PhonemeSegment

_SETUP_HELP = (
    "JuliusAligner の実行に必要な設定が不足しています。\n"
    "Julius本体・日本語音響モデル(dictation-kit)・julius4segのセットアップが必要です。\n"
    "手順は README.md の「Juliusのセットアップ」セクションを参照してください。\n"
    "必要な環境変数: JULIUS_BIN, JULIUS_HMM, JULIUS_HMMLIST\n"
    "(任意: JULIUS_HMM_MODEL, JULIUS_CONFIG)"
)


class JuliusAligner(Aligner):
    """Julius音声認識エンジン + julius4seg(segmentation-kit方式)による強制アライメント。

    Julius本体・音響モデルのインストールはこのクラスの責務外。
    環境変数でパスを指定する:
      JULIUS_BIN: julius実行バイナリへのパス
      JULIUS_HMM: 音響モデル(.binhmm等)へのパス
      JULIUS_HMMLIST: HMMリストファイルへのパス
      JULIUS_HMM_MODEL: (任意) triphone/monophone等モデル種別
      JULIUS_CONFIG: (任意) julius設定ファイル(.jconf)へのパス
    """

    def __init__(self):
        self.julius_bin = os.environ.get("JULIUS_BIN")
        self.hmm = os.environ.get("JULIUS_HMM")
        self.hmmlist = os.environ.get("JULIUS_HMMLIST")
        self.hmm_model = os.environ.get("JULIUS_HMM_MODEL")
        self.config = os.environ.get("JULIUS_CONFIG")

    def _check_setup(self) -> None:
        missing = [
            name
            for name, value in (
                ("JULIUS_BIN", self.julius_bin),
                ("JULIUS_HMM", self.hmm),
                ("JULIUS_HMMLIST", self.hmmlist),
            )
            if not value
        ]
        if missing:
            raise RuntimeError(
                f"環境変数 {', '.join(missing)} が設定されていません。\n{_SETUP_HELP}"
            )

        try:
            import julius4seg  # noqa: F401
        except ImportError as e:
            raise RuntimeError(
                "julius4seg がインストールされていません。\n"
                "pip install git+https://github.com/Hiroshiba/julius4seg でインストールしてください。\n"
                f"{_SETUP_HELP}"
            ) from e

        if not os.path.exists(self.julius_bin):
            raise RuntimeError(
                f"JULIUS_BIN で指定されたパスが存在しません: {self.julius_bin}\n{_SETUP_HELP}"
            )

    def align(self, wav_path: str, phonemes: list[str]) -> list[PhonemeSegment]:
        self._check_setup()

        # julius4seg のAPIを用いて julius によるセグメンテーションを実行する。
        # julius4seg はコマンドラインツールとしての利用が主で、Python API仕様は
        # バージョンによって変わりうるため、ここでは遅延importし、
        # 実行時にセットアップ不備があれば分かりやすいエラーに変換する。
        try:
            from julius4seg.sp_inserter import ModelType, space_missing_inserter
            from julius4seg.julius_segmentation import julius_segmentation
        except ImportError as e:
            raise RuntimeError(
                "julius4seg の想定モジュールが見つかりませんでした。"
                "julius4seg のバージョンを確認し、README.md の手順を見直してください。\n"
                f"{_SETUP_HELP}"
            ) from e

        raise NotImplementedError(
            "JuliusAligner は julius4seg 連携のインターフェースのみ定義されています。"
            "実際のJulius/音響モデル導入後、環境に合わせて julius4seg 呼び出し部分を実装してください。\n"
            f"{_SETUP_HELP}"
        )
