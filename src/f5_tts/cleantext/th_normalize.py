import re
from ssg import syllable_tokenize

def number2text(text):
    thai_digits = {
        0: "ศูนย์", 1: "หนึ่ง", 2: "สอง", 3: "สาม", 4: "สี่",
        5: "ห้า", 6: "หก", 7: "เจ็ด", 8: "แปด", 9: "เก้า"
    }
    thai_places = ["", "สิบ", "ร้อย", "พัน", "หมื่น", "แสน", "ล้าน"]

    def num2th(num, digit_by_digit=False):
        if num == 0:
            return thai_digits[0]
        if digit_by_digit:
            return " ".join(thai_digits[int(d)] for d in str(num))
        if num >= 1000000:
            millions = num // 1000000
            remainder = num % 1000000
            result = num2th(millions) + "ล้าน"
            if remainder > 0:
                result += num2th(remainder)
            return result
        num_str = str(num)
        digits = [int(d) for d in num_str]
        digits.reverse()
        result = []
        for i, digit in enumerate(digits):
            if digit == 0:
                continue
            if i == 1:
                if digit == 1:
                    result.append(thai_places[i])
                elif digit == 2:
                    result.append("ยี่" + thai_places[i])
                else:
                    result.append(thai_digits[digit] + thai_places[i])
            elif i == 0 and digit == 1:
                if len(digits) > 1 and digits[1] in [1, 2]:
                    result.append("เอ็ด")
                else:
                    result.append(thai_digits[digit])
            else:
                result.append(thai_digits[digit] + thai_places[i])
        result.reverse()
        return "".join(result)

    def convert_match(match):
        num_str = match.group(0).replace(',', '')
        if not num_str or num_str == '.':
            return match.group(0)
        if '.' in num_str:
            parts = num_str.split('.')
            integer_part = parts[0]
            decimal_part = parts[1] if len(parts) > 1 else ''
            integer_value = int(integer_part) if integer_part else 0
            if len(integer_part) > 7:
                result = num2th(integer_value, digit_by_digit=True)
            else:
                result = num2th(integer_value)
            if decimal_part:
                result += "จุด " + " ".join(num2th(int(d)) for d in decimal_part)
            return result
        num = int(num_str)
        if len(num_str) > 7:
            return num2th(num, digit_by_digit=True)
        return num2th(num)

    def process_text(text):
        words = text.split()
        result = []
        for word in words:
            if re.match(r'^[\d,]+(\.\d+)?$', word):
                result.append(convert_match(re.match(r'[\d,\.]+', word)))
            else:
                if any(c.isdigit() for c in word):
                    processed = ""
                    num_chunk = ""
                    for char in word:
                        if char.isdigit():
                            num_chunk += char
                        else:
                            if num_chunk:
                                processed += " ".join(num2th(int(d)) for d in num_chunk) + " "
                                num_chunk = ""
                            processed += char + " "
                    if num_chunk:
                        processed += " ".join(num2th(int(d)) for d in num_chunk)
                    result.append(processed.strip())
                else:
                    result.append(word)
        return " ".join(result)

    return process_text(text)

def remove_symbol(text):
    symbols = "{}[]()-_?/\\|!*%$&@#^<>+-\";:~\`=“”"
    for symbol in symbols:
        text = text.replace(symbol, '')
    text = text.replace(" ๆ","ๆ")
    return text
    
def maiyamok(text):
    
    cleaned_symbols = remove_symbol(text)

    words = syllable_tokenize(cleaned_symbols)
    
    result = []
    i = 0
    while i < len(words):
        if i + 1 < len(words) and words[i + 1] == "ๆ":
            result.append(words[i])
            result.append(words[i])  
            i += 2 
        else:
            result.append(words[i])
            i += 1
    
    return "".join(result)

def normalize_text(text):
    text = maiyamok(text)
    text = number2text(text)
    return text

if __name__ == "__main__":
    
    test_cases = [
        "วันที่ ฉันสนุกมากๆ",
        "ดีมากๆ",
        "บ้านสวยๆ",
        "วันที่ 15 มิถุนายน 2556 ฉันสนุกมากๆ และกินอร่อยๆ",
        "Today เป็นวันเกิดของฉัน วันที่ 20 ฉันอยากให้คุณ listern to me."
    ]
    
    for text in test_cases:
        result = normalize_text(text)
        print(f"Original: {text} -> Converted: {result}")
