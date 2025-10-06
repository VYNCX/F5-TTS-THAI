from f5_tts.cleantext.thaig2p_modules import main 
from pythainlp.tokenize import word_tokenize
from f5_tts.cleantext.th_normalize import normalize_text

def th_to_g2p(text):
    text = normalize_text(text)
    word = word_tokenize(text)
    ipa = main.g2p(word, 'ipa') 
    return ipa.replace("  "," ") + "."

