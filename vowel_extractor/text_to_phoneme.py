import pyopenjtalk


def text_to_phonemes(text: str) -> list[str]:
    """日本語テキストを音素列(リスト)に変換する

    pyopenjtalk.g2p() は "k o N n i ch i w a" のような空白区切り文字列を返す。
    無音区間を表す "pau" はここでは除外せず、そのままアライナーに渡す。
    """
    phoneme_str = pyopenjtalk.g2p(text, kana=False)
    return phoneme_str.split()
