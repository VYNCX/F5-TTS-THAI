import csv, os, html, re
from tltk import g2p as tltkg2p

##################################################
### CONSTANTS
##################################################

SHORT_VOWELS = "aivueyoxz"
LONG_VOWELS =  "AIVUEYOXZ"
DIPHTHONGS = "JWR"
VOWELS = SHORT_VOWELS + LONG_VOWELS + DIPHTHONGS
CLUSTERS = ["br","bl","pr","pl","Pr","Pl","fr","fl","dr","tr","Tr","kr","kl","kw","Kr","Kl","Kw"]
ONSETS = ["b","p","P","m","f","d","t","T","n","s","r","l","c","C","k","K","N","w","j","h","?"]
CODAS = ["p","m","f","t","d","n","s","l","c","k","N","w","j","?","-"]

### read dictionary
abs_dir = os.path.dirname(__file__)
with open(abs_dir + '/thai2phone.csv', encoding="utf-8") as f:
    THAI2PHONE_DICT = dict(csv.reader(f))
    THAI2PHONE_DICT = {k:v for k,v in THAI2PHONE_DICT.items() if v != ''}

##################################################
### UTILS FOR HANDLING PHONES
##################################################

# convert short vowel <> long vowel
def short2long(vowel_phone):
    """convert short vowel into long vowel
    >>> short2long('a') -> A
    """
    try:
        return LONG_VOWELS[SHORT_VOWELS.index(vowel_phone)]
    except:
        return None

def long2short(vowel_phone):
    """convert long vowel into short vowel
    >>> short2long('A') -> a
    """
    try:
        return SHORT_VOWELS[LONG_VOWELS.index(vowel_phone)]
    except:
        return None

def validate(phone):
    """validate encoded phone
    >>> validate('paj1 dAj3') -> True
    >>> validate('aaa aaa') -> False
    """
    syls = phone.split()
    for syl in syls:
        try:
            tone = syl[-1] # prA-1 -> 1
            coda = syl[-2] # prA-1 -> -
            vowel = syl[-3] # prA-1 -> A
            onset = syl[:-3] # # prA-1 -> pr
        except:
            return False 
        # check all 4 parts are valid
        if tone in '12345' and coda in CODAS and vowel in VOWELS and onset in CLUSTERS+ONSETS:
            continue
        else:
            return False
    return True

def get_tones(phone:str):
    """get all tones of one word
    >>> get_tones('paj1 dAj3') -> (1, 3)
    """
    return tuple(syl[-1] for syl in phone.split())

def get_onsets(phone:str):
    """get all onsets of one word
    >>> get_onsets('paj1 dAj3') -> (p, d)
    """
    return tuple(syl[:-3] for syl in phone.split())

def get_vowels(phone:str):
    """get all vowels of one word
    >>> get_tones('paj1 dAj3') -> (a, A)
    """
    return tuple(syl[-3] for syl in phone.split())

def get_codas(phone:str):
    """get all codas of one word
    >>> get_codas('paj1 dAj3') -> (j, j)
    """
    return tuple(syl[-2] for syl in phone.split())

def get_vowels_tone(phone:str):
    """get all vowels & tones of one word
    >>> get_vowels_tone('paj1 dAj3') -> (a1, A3)
    """
    return tuple(syl[-3]+syl[-1] for syl in phone.split())

def clean(text:str):
    text = html.unescape(text)
    text = re.sub(r'[\n\s]+', ' ', text) # shrink whitespaces
    text = re.sub(r'https?://[^\s]+((?=\s)|(?=$))', '', text) # remove URL
    text = re.sub(r'\((.+?)\)', r'( \1 )', text) # add space before/after parentheses
    text = re.sub(r'\"(.+?)\"', r'" \1 "', text) # add space before/after quotation
    text = re.sub(r'[“”„]', '"', text) # convert double quotations into "
    text = re.sub(r'[‘’`]', "'", text) # convert single quotations into '
    text = re.sub(r'[ \u00a0\xa0\u3000\u2002-\u200a\t]+', ' ', text) # e.g. good  boy -> good boy
    text = re.sub(r'[\r\u200b\ufeff]+', '', text) # remove non-breaking space
    return text.strip()

def get_phone_word(thaiword:str):
    # if the word in the dict, return the phone
    # ไป -> paj1
    return THAI2PHONE_DICT.get(thaiword, None)

def is_time(text:str):
    # 8:00, 09.12, 12:12, 23.31น., etc
    return bool(re.match(r'[012]?[0-9][:\.][0-5][0-9](\s*)?(น.)?', text))

def is_number(text:str):
    return bool(re.match(r'\-?\d[\d\,]*(?:\.\d+)?$', text))

def get_phone_word_tltk(thaiword:str):
    # if the word is not in dict, use tltk instead
    # tltk may return several sentences e.g. <tr/>paj0|maj4|<s/><tr/>maj2|paj0|<s/>
    # sentences = ['paj0|maj4', 'maj2|paj0']
    decoded_syls = []
    result = tltkg2p(thaiword)
    tokens = re.findall(r'<tr/>(\S+?)\|(?:<s/>|\s)', result)
    for token in tokens: # 'paj0|maj4'
        # split to each syllable 'paj0', 'maj4'
        # delimiter : | or ^ or ~ '
        for syl in re.split(r"[|^~\']", token):
            syl = syl.replace('\\', '') # remove \ e.g. เจิ้น -> c\\@n2
            ### change encoding ###
            tone = str(int(syl[-1])+1) # 0->1 because use 0-4 in tltk
            if int(tone) > 5: # strangely, there are tone "8" in tltk
                tone = str(int(tone)-5)
            syl = syl[:-1] + tone
            # replace vowels
            syl = re.sub(r'iia(?=\d)', 'J-', syl) # /ia/
            syl = re.sub(r'iia', 'J', syl)
            syl = re.sub(r'ia', 'J-', syl)
            syl = re.sub(r'UUa(?=\d)', 'W-', syl) # /ɯa/
            syl = re.sub(r'UUa', 'W', syl)
            syl = re.sub(r'Ua', 'W-', syl)
            syl = re.sub(r'uua(?=\d)', 'R-', syl) # /ua/
            syl = re.sub(r'uua', 'R', syl)
            syl = re.sub(r'ua', 'R-', syl)
            syl = re.sub(r'aa(?=\d)', 'A-', syl) # no coda
            syl = re.sub(r'aa', 'A', syl) # with coda
            syl = re.sub(r'a(?=\d)', 'a-', syl) # no coda
            syl = re.sub(r'ii(?=\d)', 'I-', syl)
            syl = re.sub(r'ii', 'I', syl)
            syl = re.sub(r'i(?=\d)', 'i-', syl)
            syl = re.sub(r'UU(?=\d)', 'V-', syl) # /ɯ/
            syl = re.sub(r'UU', 'V', syl)
            syl = re.sub(r'U(?=\d)', 'v-', syl)
            syl = re.sub(r'U', 'v', syl)
            syl = re.sub(r'uu(?=\d)', 'U-', syl) # /u/
            syl = re.sub(r'uu', 'U', syl)
            syl = re.sub(r'u(?=\d)', 'u-', syl)
            syl = re.sub(r'xx(?=\d)', 'Y-', syl) # /ɛ/
            syl = re.sub(r'xx', 'Y', syl)
            syl = re.sub(r'x(?=\d)', 'y-', syl)
            syl = re.sub(r'x', 'y', syl)
            syl = re.sub(r'ee(?=\d)', 'E-', syl) # /e/
            syl = re.sub(r'ee', 'E', syl)
            syl = re.sub(r'e(?=\d)', 'e-', syl)
            syl = re.sub(r'OO(?=\d)', 'X-', syl) # /ɔ/
            syl = re.sub(r'OO', 'X', syl)
            syl = re.sub(r'O(?=\d)', 'x-', syl)
            syl = re.sub(r'O', 'x', syl)
            syl = re.sub(r'oo(?=\d)', 'O-', syl) # /o/
            syl = re.sub(r'oo', 'O', syl)
            syl = re.sub(r'o(?=\d)', 'o-', syl)
            syl = re.sub(r'@@(?=\d)', 'Z-', syl) # /ə/
            syl = re.sub(r'@@', 'Z', syl)
            syl = re.sub(r'@(?=\d)', 'z-', syl)
            syl = re.sub(r'@', 'z', syl)
            # replace consonants
            syl = re.sub(r'th', 'T', syl)
            syl = re.sub(r'kh', 'K', syl)
            syl = re.sub(r'ph', 'P', syl)
            syl = re.sub(r'ch', 'C', syl)

            decoded_syls.append(syl)

    return ' '.join(decoded_syls)


##################################################
### G2P FUNCTIONS
##################################################

def decode(phone, transcription='haas', keep_space=True):
    """decode phone into Haas or IPA

    Parameters
    ----------
        phone : str or list
            encoded syllbles
            e.g. 'kot2 mAj5' or ['kot2', 'mAj5']
        transcription : str
            'haas'(default) or 'ipa' or 'RTGS'

    Return
    ------
    str
        decoded phone, e.g. kòt mǎːj

    Example
    -------
        decode('kot2 mAj5 ʔA-1 jA-1 123', 'ipa')
            'kòt mǎːj ʔaː jaː 123'
    """

    ## check type of parameter
    if type(phone) == str: # one string e.g. "kot2 mAj5" 
        syls = phone.split() 
    elif type(phone) == list: # ['kot2', 'mAj5']
        syls = phone
    else:
        raise TypeError

    decoded_syls = []
    for i, syl in enumerate(syls):
        if not validate(syl): # e.g. English, punctuation
            decoded_syls.append(syl) # return original string
            continue
        tone = syl[-1]
        coda = syl[-2]
        coda = coda.replace('ʔ','-') # delete ? in all codas
        """ # delete ? unless the final syllable
        if i != len(syls) - 1: 
            coda = coda.replace('ʔ','-') # "-" = no coda
        """
        vowel = syl[-3]
        onset = syl[:-3] # one or two characters
        if transcription.lower() == 'ipa':
            decoded_syls.append(''.join([PHONE2IPA[c] for c in onset]) + PHONE2IPA[vowel+tone] + PHONE2IPA[coda])
        elif transcription.lower() == 'haas':
            decoded_syls.append(''.join([PHONE2HAAS[c] for c in onset]) + PHONE2HAAS[vowel+tone] + PHONE2HAAS[coda])
        elif transcription.lower() == 'rtgs':
            decoded_syls.append(''.join([PHONE2RTGS[c] for c in onset]) + PHONE2RTGS[vowel+tone] + PHONE2RTGS_CODA[coda])
    if keep_space == False:
        decoded_syls = ''.join(decoded_syls)
    elif type(keep_space) == str: # custom delimiter
        decoded_syls = keep_space.join(decoded_syls)
    else:
        decoded_syls = ''.join(decoded_syls)
    return decoded_syls

# tokenize by pythainlp -> look up dictionary
# if there is none, try to use tltk instead
def g2p(sentence, transcription='haas', return_tokens=False, decoded=True):
    """G2P function for Thai sentence

    Parameters
    ----------
    sentence : str or list
        string of Thai sentences or list of tokenized words 
    transcription : str
        'haas'(default) or 'ipa' or 'rtgs'
    return_tokens : bool
        whether returns also tokenized sentence
    decoded : bool
        if True, returns decoded phone e.g. paj roːŋ rian
        if False, returns undecoded phone e.g. paj1 rON1 rJn1

    Return
    ------
    str
        syllables delimited by whitespaces 
    or list
        list of [token, phone]

    Examples
    --------
        g2p('ไปโรงเรียน')
            'paj rooŋ rian'

        g2p('ไปโรงเรียน', transcription='ipa')
            'paj roːŋ rian'

        g2p('ไปโรงเรียน', return_tokens=True)
            [['ไป', 'pay'], ['โรงเรียน', 'rooŋ rian']]
    """

    ### tokenize ###
    if type(sentence) == str: # input is string
        from pythainlp import word_tokenize
        sentence = clean(sentence) # preprocessing
        tokens = word_tokenize(sentence, keep_whitespace=False)
    elif type(sentence) == list and type(sentence[0]) == str: # input is tokens already
        tokens = sentence
    
    token_phone_list = [] # list of [token, phone] e.g. [['ไป','paj1'],['โรงเรียน','rON1 rJn1']]

    ### check each token ###
    for i, token in enumerate(tokens):

        # exceptions

        if token == 'น.' and i > 0 and\
        (token_phone_list[-1][1].endswith('nA-1 li-4 kA-1') or token_phone_list[-1][1].endswith('nA-1 TI-1')):
            token_phone_list[-1][0] += ' น.' # add to previous token to avoid duplicate
            continue
        elif token == 'ๆ' and i > 0: # if single ๆ, repeat final one
            token_phone_list[-1][0] += ' ๆ'
            token_phone_list[-1][1] += ' ' + token_phone_list[-1][1]
            continue
        
        # Thai word in dictionary
        elif token in THAI2PHONE_DICT:
            phone = get_phone_word(token)

        # single thai character (maybe mistake of tokenization) -> pass
        elif re.match('[ก-ฮ]$', token): 
            continue

        # thaiword, but not in dictionary -> use tltk instead
        elif re.match(r'[ก-๙][ก-๙\-\.]*$', token): 
            #phone = None  # return None, USE THIS LINE WHEN TEST
            phone = get_phone_word_tltk(token)
        
        # return original token, e.g. english, punctuation...
        else: 
            phone = token

        token_phone_list.append([token, phone])

    ### decode ###
    if decoded:
        token_phone_list = [[t, decode(p, transcription)] for t, p in token_phone_list]

    ### return ###
    if return_tokens:
        return token_phone_list # return as list of [token, phone]
    else:
        return ' '.join([phone for _, phone in token_phone_list])

def encode_haas(phone_haas):
    syls = phone_haas.split(' ')
    encoded_syls = []
    for syl in syls:
        # get coda
        if syl[-1] not in 'pmftdnslkŋwyʔ':
            coda = '-'
        else:
            coda = HAAS2PHONE[syl[-1]]
            syl = syl[:-1]

        # get onset
        if syl[:2] in ['ph','th','ch','kh'] and syl[2] in 'rlw': # aspirated cluster e.g. phr
            onset = HAAS2PHONE[syl[:2]] + HAAS2PHONE[syl[2]]
            syl = syl[3:]
        elif syl[0] in HAAS2PHONE and syl[1] in 'rlw':
            onset = HAAS2PHONE[syl[0]] + HAAS2PHONE[syl[1]] # cluster e.g. pr
            syl = syl[2:]
        elif syl[:2] in ['ph','th','ch','kh']: # aspirated
            onset = HAAS2PHONE[syl[:2]]
            syl = syl[2:]
        elif syl[:1] in HAAS2PHONE: # others
            onset = HAAS2PHONE[syl[:1]]
            syl = syl[1:]

        # vowel
        if syl not in HAAS2PHONE:
            print(coda, onset, syl)
            return None
        vowel, tone = HAAS2PHONE[syl]

        encoded_syls.append(onset+vowel+coda+tone)

    return ' '.join(encoded_syls)


PHONE2IPA = {
    'a1':'a' ,'a2':'à' ,'a3':'â' ,'a4':'á' ,'a5':'ǎ' ,
    'A1':'aː','A2':'àː','A3':'âː','A4':'áː','A5':'ǎː',
    'i1':'i' ,'i2':'ì' ,'i3':'î' ,'i4':'í' ,'i5':'ǐ' ,
    'I1':'iː','I2':'ìː','I3':'îː','I4':'íː','I5':'ǐː',
    'u1':'u' ,'u2':'ù' ,'u3':'û' ,'u4':'ú' ,'u5':'ǔ' ,
    'U1':'uː','U2':'ùː','U3':'ûː','U4':'úː','U5':'ǔː',
    'v1':'ɯ' ,'v2':'ɯ̀' ,'v3':'ɯ̂' ,'v4':'ɯ́' ,'v5':'ɯ̌' ,
    'V1':'ɯː','V2':'ɯ̀ː','V3':'ɯ̂ː','V4':'ɯ́ː','V5':'ɯ̌ː',
    'e1':'e' ,'e2':'è' ,'e3':'ê' ,'e4':'é' ,'e5':'ě' ,
    'E1':'eː','E2':'èː','E3':'êː','E4':'éː','E5':'ěː',
    'y1':'ɛ' ,'y2':'ɛ̀' ,'y3':'ɛ̂' ,'y4':'ɛ́' ,'y5':'ɛ̌' ,
    'Y1':'ɛː','Y2':'ɛ̀ː','Y3':'ɛ̂ː','Y4':'ɛ́ː','Y5':'ɛ̌ː',
    'o1':'o' ,'o2':'ò' ,'o3':'ô' ,'o4':'ó' ,'o5':'ǒ' ,
    'O1':'oː','O2':'òː','O3':'ôː','O4':'óː','O5':'ǒː',
    'x1':'ɔ' ,'x2':'ɔ̀' ,'x3':'ɔ̂' ,'x4':'ɔ́' ,'x5':'ɔ̌' ,
    'X1':'ɔː','X2':'ɔ̀ː','X3':'ɔ̂ː','X4':'ɔ́ː','X5':'ɔ̌ː',
    'z1':'ə' ,'z2':'ə̀' ,'z3':'ə̂' ,'z4':'ə́' ,'z5':'ə̌' ,
    'Z1':'əː','Z2':'ə̀ː','Z3':'ə̂ː','Z4':'ə́ː','Z5':'ə̌ː',
    'J1':'iə','J2':'ìə','J3':'îə','J4':'íə','J5':'ǐə',
    'W1':'ɯə','W2':'ɯ̀ə','W3':'ɯ̂ə','W4':'ɯ́ə','W5':'ɯ̌ə',
    'R1':'uə','R2':'ùə','R3':'ûə','R4':'úə','R5':'ǔə',
    'b' :'b' ,'p' :'p' ,'P' :'pʰ','m' :'m' ,'f' :'f' ,
    'd' :'d' ,'t' :'t' ,'T' :'tʰ','n' :'n' ,'s' :'s' ,
    'r' :'r' ,'l' :'l' ,'c' :'tɕ','C' :'tɕʰ',
    'k' :'k' ,'K' :'kʰ','N' :'ŋ' ,
    'w' :'w' ,'j' :'j' ,'h' :'h' ,'?' :'ʔ',
    '.' :'.' ,'-' :''
}

PHONE2HAAS = {
    'a1':'a' ,'a2':'à' ,'a3':'â' ,'a4':'á' ,'a5':'ǎ' ,
    'A1':'aa','A2':'àa','A3':'âa','A4':'áa','A5':'ǎa',
    'i1':'i' ,'i2':'ì' ,'i3':'î' ,'i4':'í' ,'i5':'ǐ' ,
    'I1':'ii','I2':'ìi','I3':'îi','I4':'íi','I5':'ǐi',
    'u1':'u' ,'u2':'ù' ,'u3':'û' ,'u4':'ú' ,'u5':'ǔ' ,
    'U1':'uu','U2':'ùu','U3':'ûu','U4':'úu','U5':'ǔu',
    'v1':'ɯ' ,'v2':'ɯ̀' ,'v3':'ɯ̂' ,'v4':'ɯ́' ,'v5':'ɯ̌' ,
    'V1':'ɯɯ','V2':'ɯ̀ɯ','V3':'ɯ̂ɯ','V4':'ɯ́ɯ','V5':'ɯ̌ɯ',
    'e1':'e' ,'e2':'è' ,'e3':'ê' ,'e4':'é' ,'e5':'ě' ,
    'E1':'ee','E2':'èe','E3':'êe','E4':'ée','E5':'ěe',
    'y1':'ɛ' ,'y2':'ɛ̀' ,'y3':'ɛ̂' ,'y4':'ɛ́' ,'y5':'ɛ̌' ,
    'Y1':'ɛɛ','Y2':'ɛ̀ɛ','Y3':'ɛ̂ɛ','Y4':'ɛ́ɛ','Y5':'ɛ̌ɛ',
    'o1':'o' ,'o2':'ò' ,'o3':'ô' ,'o4':'ó' ,'o5':'ǒ' ,
    'O1':'oo','O2':'òo','O3':'ôo','O4':'óo','O5':'ǒo',
    'x1':'ɔ' ,'x2':'ɔ̀' ,'x3':'ɔ̂' ,'x4':'ɔ́' ,'x5':'ɔ̌' ,
    'X1':'ɔɔ','X2':'ɔ̀ɔ','X3':'ɔ̂ɔ','X4':'ɔ́ɔ','X5':'ɔ̌ɔ',
    'z1':'ə' ,'z2':'ə̀' ,'z3':'ə̂' ,'z4':'ə́' ,'z5':'ə̌' ,
    'Z1':'əə','Z2':'ə̀ə','Z3':'ə̂ə','Z4':'ə́ə','Z5':'ə̌ə',
    'J1':'ia','J2':'ìa','J3':'îa','J4':'ía','J5':'ǐa',
    'W1':'ɯa','W2':'ɯ̀a','W3':'ɯ̂a','W4':'ɯ́a','W5':'ɯ̌a',
    'R1':'ua','R2':'ùa','R3':'ûa','R4':'úa','R5':'ǔa',
    'b' :'b' ,'p' :'p' ,'P' :'ph','m' :'m' ,'f' :'f' ,
    'd' :'d' ,'t' :'t' ,'T' :'th','n' :'n' ,'s' :'s' ,
    'r' :'r' ,'l' :'l' ,'c' :'c' ,'C' :'ch',
    'k' :'k' ,'K' :'kh','N' :'ŋ' ,
    'w' :'w' ,'j' :'y' ,'h' :'h' ,'?' :'ʔ' ,
    '.':'.',   '-':''
}

PHONE2RTGS = {
    'a1':'a' ,'a2':'a' ,'a3':'a' ,'a4':'a' ,'a5':'a',
    'A1':'a' ,'A2':'a' ,'A3':'a' ,'A4':'a' ,'A5':'a',
    'i1':'i' ,'i2':'i' ,'i3':'i' ,'i4':'i' ,'i5':'i',
    'I1':'i' ,'I2':'i' ,'I3':'i' ,'I4':'i' ,'I5':'i',
    'u1':'u' ,'u2':'u' ,'u3':'u' ,'u4':'u' ,'u5':'u',
    'U1':'u' ,'U2':'u' ,'U3':'u' ,'U4':'u' ,'U5':'u',
    'v1':'ue','v2':'ue','v3':'ue','v4':'ue','v5':'ue',
    'V1':'ue','V2':'ue','V3':'ue','V4':'ue','V5':'ue',
    'e1':'e' ,'e2':'e' ,'e3':'e' ,'e4':'e' ,'e5':'e',
    'E1':'e' ,'E2':'e' ,'E3':'e' ,'E4':'e' ,'E5':'e',
    'y1':'ae','y2':'ae','y3':'ae','y4':'ae','y5':'ae',
    'Y1':'ae','Y2':'ae','Y3':'ae','Y4':'ae','Y5':'ae',
    'o1':'o' ,'o2':'o' ,'o3':'o' ,'o4':'o' ,'o5':'o',
    'O1':'o' ,'O2':'o' ,'O3':'o' ,'O4':'o' ,'O5':'o',
    'x1':'o' ,'x2':'o' ,'x3':'o' ,'x4':'o' ,'x5':'o',
    'X1':'o' ,'X2':'o' ,'X3':'o' ,'X4':'o' ,'X5':'o',
    'z1':'oe','z2':'oe','z3':'oe','z4':'oe','z5':'oe',
    'Z1':'oe','Z2':'oe','Z3':'oe','Z4':'oe','Z5':'oe',
    'J1':'ia','J2':'ia','J3':'ia','J4':'ia','J5':'ia',
    'W1':'uea','W2':'uea','W3':'uea','W4':'uea','W5':'uea',
    'R1':'ua','R2':'ua','R3':'ua','R4':'ua','R5':'ua',
    'b' :'b' ,'p' :'p' ,'P' :'ph','m' :'m' ,'f' :'f' ,
    'd' :'d' ,'t' :'t' ,'T' :'th','n' :'n' ,'s' :'s' ,
    'r' :'r' ,'l' :'l' ,'c' :'ch' ,'C' :'ch',
    'k' :'k' ,'K' :'kh','N' :'ng' ,
    'w' :'w' ,'j' :'y' ,'h' :'h' ,'?' :'' ,
    '.':'.',   '-':''
}

PHONE2RTGS_CODA = {
    'b' :'b' ,'p' :'p' ,'P' :'ph','m' :'m' ,'f' :'f' ,
    'd' :'d' ,'t' :'t' ,'T' :'th','n' :'n' ,'s' :'s' ,
    'r' :'r' ,'l' :'l' ,'c' :'ch' ,'C' :'ch',
    'k' :'k' ,'K' :'kh','N' :'ng' ,
    'w' :'o' ,'j' :'i' ,'h' :'h' ,'?' :'' ,
    '.':'.',   '-':''
}

HAAS2PHONE = {
    'a' :'a1','à' :'a2','â' :'a3','á' :'a4','ǎ' :'a5',
    'aa':'A1','àa':'A2','âa':'A3','áa':'A4','ǎa':'A5',
    'i' :'i1','ì' :'i2','î' :'i3','í' :'i4','ǐ' :'i5',
    'ii':'I1','ìi':'I2','îi':'I3','íi':'I4','ǐi':'I5',
    'u' :'u1','ù' :'u2','û' :'u3','ú' :'u4','ǔ' :'u5',
    'uu':'U1','ùu':'U2','ûu':'U3','úu':'U4','ǔu':'U5',
    'ɯ' :'v1','ɯ̀' :'v2','ɯ̂' :'v3','ɯ́' :'v4','ɯ̌' :'v5',
    'ɯɯ':'V1','ɯ̀ɯ':'V2','ɯ̂ɯ':'V3','ɯ́ɯ':'V4','ɯ̌ɯ':'V5',
    'e' :'e1','è' :'e2','ê' :'e3','é' :'e4','ě' :'e5',
    'ee':'E1','èe':'E2','êe':'E3','ée':'E4','ěe':'E5',
    'ɛ' :'y1','ɛ̀' :'y2','ɛ̂' :'y3','ɛ́' :'y4','ɛ̌' :'y5',
    'ɛɛ':'Y1','ɛ̀ɛ':'Y2','ɛ̂ɛ':'Y3','ɛ́ɛ':'Y4','ɛ̌ɛ':'Y5',
    'o' :'o1','ò' :'o2','ô' :'o3','ó' :'o4','ǒ' :'o5',
    'oo':'O1','òo':'O2','ôo':'O3','óo':'O4','ǒo':'O5',
    'ɔ' :'x1','ɔ̀' :'x2','ɔ̂' :'x3','ɔ́' :'x4','ɔ̌' :'x5',
    'ɔɔ':'X1','ɔ̀ɔ':'X2','ɔ̂ɔ':'X3','ɔ́ɔ':'X4','ɔ̌ɔ':'X5',
    'ə' :'z1','ə̀' :'z2','ə̂' :'z3','ə́' :'z4','ə̌' :'z5',
    'əə':'Z1','ə̀ə':'Z2','ə̂ə':'Z3','ə́ə':'Z4','ə̌ə':'Z5',
    'ia':'J1','ìa':'J2','îa':'J3','ía':'J4','ǐa':'J5',
    'ɯa':'W1','ɯ̀a':'W2','ɯ̂a':'W3','ɯ́a':'W4','ɯ̌a':'W5',
    'ua':'R1','ùa':'R2','ûa':'R3','úa':'R4','ǔa':'R5',
    'b' :'b' ,'p' :'p' ,'ph':'P' ,'m' :'m' ,'f' :'f' ,
    'd' :'d' ,'t' :'t' ,'th':'T' ,'n' :'n' ,'s' :'s' ,
    'r' :'r' ,'l' :'l' ,'c' :'c' ,'ch':'C' ,
    'k' :'k' ,'kh':'K' ,'ŋ' :'N' ,
    'w' :'w' ,'y' :'j' ,'h' :'h' ,'ʔ' :'?'
}
