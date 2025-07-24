import re
import logging
from typing import Dict, List, Optional, Any, Set, Tuple
import os

logger = logging.getLogger(__name__)

# 預設藥品相關關鍵字
MEDICINE_NAME_KEYWORDS = {
    'zh-tw': ['藥品', '藥名', '品名', '商品名', '學名', '成藥', '醫藥', '膠囊', '錠', '藥片', '藥水', '注射液'],
    'zh-cn': ['药品', '药名', '品名', '商品名', '学名', '成药', '医药', '胶囊', '锭', '药片', '药水', '注射液'],
    'en': ['medicine', 'drug', 'name', 'brand', 'capsule', 'tablet', 'pill', 'syrup', 'injection', 'product'],
    'ja': ['薬', '薬品', '薬名', '商品名', 'カプセル', '錠', '丸', '注射液'],
    'ko': ['약', '약품', '약명', '상품명', '캡슐', '정', '주사액']
}

INGREDIENT_KEYWORDS = {
    'zh-tw': ['成分', '主成分', '活性成分', '配方', '含有', '含量', '組成', '組份', '賦形劑'],
    'zh-cn': ['成分', '主成分', '活性成分', '配方', '含有', '含量', '组成', '组份', '赋形剂'],
    'en': ['ingredient', 'active', 'composition', 'contains', 'content', 'component', 'excipient', 'formulation'],
    'ja': ['成分', '主成分', '組成', '含有', '含量', '配合', '賦形剤'],
    'ko': ['성분', '주성분', '조성', '함유', '함량', '배합']
}

QUANTITY_KEYWORDS = {
    'zh-tw': ['數量', '含量', '劑量', '每日劑量', '每日用量', '用量', '毫克', '微克', '公克', '公斤', '毫升', '克', 'mg', 'mcg', 'g', 'ml'],
    'zh-cn': ['数量', '含量', '剂量', '每日剂量', '每日用量', '用量', '毫克', '微克', '公克', '公斤', '毫升', '克', 'mg', 'mcg', 'g', 'ml'],
    'en': ['quantity', 'amount', 'dosage', 'daily dose', 'dose', 'milligram', 'microgram', 'gram', 'kilogram', 'milliliter', 'mg', 'mcg', 'g', 'ml'],
    'ja': ['数量', '含量', '用量', '1日量', '投与量', 'ミリグラム', 'マイクログラム', 'グラム', 'キログラム', 'ミリリットル', 'mg', 'mcg', 'g', 'ml'],
    'ko': ['수량', '함량', '용량', '일일 용량', '투여량', '밀리그램', '마이크로그램', '그램', '킬로그램', '밀리리터', 'mg', 'mcg', 'g', 'ml']
}

# 劑量模式
DOSE_PATTERNS = {
    'zh-tw': r'(\d+(?:\.\d+)?\s*(?:毫克|微克|公克|公斤|毫升|克|mg|mcg|g|ml|mL))',
    'zh-cn': r'(\d+(?:\.\d+)?\s*(?:毫克|微克|公克|公斤|毫升|克|mg|mcg|g|ml|mL))',
    'en': r'(\d+(?:\.\d+)?\s*(?:milligram|microgram|gram|kilogram|milliliter|mg|mcg|g|ml|mL))',
    'ja': r'(\d+(?:\.\d+)?\s*(?:ミリグラム|マイクログラム|グラム|キログラム|ミリリットル|mg|mcg|g|ml|mL))',
    'ko': r'(\d+(?:\.\d+)?\s*(?:밀리그램|마이크로그램|그램|킬로그램|밀리리터|mg|mcg|g|ml|mL))'
}

# 每包/每錠/每瓶的數量模式
UNIT_PATTERNS = {
    'zh-tw': r'(\d+(?:\.\d+)?\s*(?:錠|膠囊|粒|包|瓶|支|片|劑))',
    'zh-cn': r'(\d+(?:\.\d+)?\s*(?:锭|胶囊|粒|包|瓶|支|片|剂))',
    'en': r'(\d+(?:\.\d+)?\s*(?:tablet|capsule|pill|pack|bottle|piece|dose))',
    'ja': r'(\d+(?:\.\d+)?\s*(?:錠|カプセル|粒|包|瓶|本|枚|剤))',
    'ko': r'(\d+(?:\.\d+)?\s*(?:정|캡슐|알|팩|병|개|조각|제))'
}

# 嘗試載入進階NLP模型(如果有)
try:
    # 這裡可以嘗試載入如spaCy、HuggingFace模型等
    ADVANCED_NLP_AVAILABLE = False
    # 實際應用中，這裡可以載入更進階的NLP模型
except ImportError:
    ADVANCED_NLP_AVAILABLE = False

def extract_medicine_info(text: str, lang: str) -> Dict[str, Any]:
    """
    從OCR文本中抽取藥品資訊
    
    參數:
        text: OCR識別出的文字
        lang: 語言代碼
        
    返回:
        包含藥品名稱、成分、數量的字典
    """
    if not text or not text.strip():
        logger.warning("文本為空，無法抽取藥品資訊")
        return {"name": None, "ingredients": [], "quantity": None, "confidence": 0.0}
    
    # 如果語言不在支援列表中，使用英文作為預設
    if lang not in MEDICINE_NAME_KEYWORDS:
        logger.warning(f"不支援的語言: {lang}，使用英文作為預設")
        lang = 'en'
    
    # 抽取藥品名稱
    medicine_name = extract_medicine_name(text, lang)
    
    # 抽取成分
    ingredients = extract_ingredients(text, lang)
    
    # 抽取數量
    quantity = extract_quantity(text, lang)
    
    # 計算整體置信度
    confidence = calculate_confidence(medicine_name, ingredients, quantity)
    
    result = {
        "name": medicine_name,
        "ingredients": ingredients,
        "quantity": quantity,
        "confidence": confidence
    }
    
    logger.info(f"抽取結果: {result}")
    return result

def extract_medicine_name(text: str, lang: str) -> Optional[str]:
    """抽取藥品名稱"""
    # 使用關鍵詞查找相關行
    lines = text.split('\n')
    keywords = MEDICINE_NAME_KEYWORDS[lang]
    
    # 首先查找包含關鍵詞的行
    potential_lines = []
    for line in lines:
        for keyword in keywords:
            if keyword in line:
                potential_lines.append(line)
                break
    
    if potential_lines:
        # 取第一個匹配行，並嘗試提取冒號或其他分隔符後的內容
        for line in potential_lines:
            # 嘗試冒號分隔
            if ':' in line or '：' in line:
                parts = re.split(r'[:：]', line, 1)
                if len(parts) > 1 and parts[1].strip():
                    return clean_text(parts[1].strip())
            # 如果沒有分隔符，但行中同時包含「品名」和其他文字，嘗試提取
            elif '品名' in line and len(line) > 3:
                parts = line.split('品名', 1)
                if len(parts) > 1 and parts[1].strip():
                    return clean_text(parts[1].strip())
                else:
                    return clean_text(line)
    
    # 如果沒有找到明確的藥品名稱行，嘗試使用啟發式規則
    # 通常藥品名稱會在前幾行
    first_lines = lines[:min(5, len(lines))]
    for line in first_lines:
        if line.strip() and not contains_only_keywords(line, lang):
            return clean_text(line.strip())
    
    return None

def extract_ingredients(text: str, lang: str) -> List[str]:
    """抽取藥品成分"""
    lines = text.split('\n')
    keywords = INGREDIENT_KEYWORDS[lang]
    ingredients = []
    
    in_ingredient_section = False
    
    for line in lines:
        # 檢查是否進入成分區段
        for keyword in keywords:
            if keyword in line:
                in_ingredient_section = True
                # 嘗試提取冒號後的內容作為成分
                if ':' in line or '：' in line:
                    parts = re.split(r'[:：]', line, 1)
                    if len(parts) > 1 and parts[1].strip():
                        ingredients.append(clean_text(parts[1].strip()))
                        break
                # 如果該行還包含數量信息，很可能是成分和含量的組合
                else:
                    # 使用劑量模式提取
                    dose_pattern = DOSE_PATTERNS.get(lang, DOSE_PATTERNS['en'])
                    dose_matches = re.findall(dose_pattern, line)
                    if dose_matches:
                        ingredients.append(clean_text(line.strip()))
                        break
        
        # 如果已經在成分區段內，繼續提取下面的行，直到遇到可能的結束標記
        elif in_ingredient_section:
            # 如果是空行或者遇到其他區段關鍵詞，退出成分區段
            if not line.strip() or contains_section_keywords(line, lang, exclude=INGREDIENT_KEYWORDS[lang]):
                in_ingredient_section = False
            # 否則繼續添加到成分列表
            elif line.strip():
                # 檢查行中是否包含劑量信息
                dose_pattern = DOSE_PATTERNS.get(lang, DOSE_PATTERNS['en'])
                dose_matches = re.findall(dose_pattern, line)
                if dose_matches:
                    ingredients.append(clean_text(line.strip()))
    
    # 如果沒有找到任何成分，嘗試通過劑量模式直接查找
    if not ingredients:
        dose_pattern = DOSE_PATTERNS.get(lang, DOSE_PATTERNS['en'])
        dose_matches = re.findall(dose_pattern, text)
        for match in dose_matches:
            # 查找包含這個劑量的行
            for line in lines:
                if match in line:
                    ingredients.append(clean_text(line.strip()))
                    break
    
    # 移除重複項
    return list(set(ingredients))

def extract_quantity(text: str, lang: str) -> Optional[str]:
    """抽取藥品數量"""
    lines = text.split('\n')
    keywords = QUANTITY_KEYWORDS[lang]
    
    # 首先查找包含數量關鍵詞的行
    for line in lines:
        for keyword in keywords:
            if keyword in line:
                # 嘗試提取單位數量
                unit_pattern = UNIT_PATTERNS.get(lang, UNIT_PATTERNS['en'])
                unit_matches = re.findall(unit_pattern, line)
                if unit_matches:
                    return unit_matches[0]
                
                # 如果沒有找到單位數量，查找劑量
                dose_pattern = DOSE_PATTERNS.get(lang, DOSE_PATTERNS['en'])
                dose_matches = re.findall(dose_pattern, line)
                if dose_matches:
                    return dose_matches[0]
    
    # 如果通過關鍵詞沒有找到，直接尋找所有可能的單位數量
    for line in lines:
        unit_pattern = UNIT_PATTERNS.get(lang, UNIT_PATTERNS['en'])
        unit_matches = re.findall(unit_pattern, line)
        if unit_matches:
            return unit_matches[0]
    
    return None

def clean_text(text: str) -> str:
    """清理文本，移除多餘的空白字符"""
    return re.sub(r'\s+', ' ', text).strip()

def contains_only_keywords(text: str, lang: str) -> bool:
    """檢查文本是否僅包含關鍵詞"""
    all_keywords = set()
    all_keywords.update(MEDICINE_NAME_KEYWORDS[lang])
    all_keywords.update(INGREDIENT_KEYWORDS[lang])
    all_keywords.update(QUANTITY_KEYWORDS[lang])
    
    text_lower = text.lower()
    
    # 檢查文本是否只包含這些關鍵詞
    for keyword in all_keywords:
        text_lower = text_lower.replace(keyword.lower(), '')
    
    # 移除標點符號和空白
    cleaned = re.sub(r'[^\w\s]', '', text_lower).strip()
    
    # 如果清理後文本為空，表示原文本只包含關鍵詞
    return not cleaned

def contains_section_keywords(text: str, lang: str, exclude: List[str]) -> bool:
    """檢查文本是否包含某一區段的關鍵詞（排除指定關鍵詞）"""
    section_keywords = set()
    section_keywords.update(MEDICINE_NAME_KEYWORDS[lang])
    section_keywords.update(INGREDIENT_KEYWORDS[lang])
    section_keywords.update(QUANTITY_KEYWORDS[lang])
    
    # 移除排除的關鍵詞
    for kw in exclude:
        if kw in section_keywords:
            section_keywords.remove(kw)
    
    # 檢查是否包含任一區段關鍵詞
    for keyword in section_keywords:
        if keyword in text:
            return True
    
    return False

def calculate_confidence(name: Optional[str], ingredients: List[str], quantity: Optional[str]) -> float:
    """計算抽取結果的置信度"""
    confidence = 0.0
    
    # 藥品名稱佔比 40%
    if name:
        confidence += 0.4
    
    # 成分佔比 40%
    if ingredients:
        confidence += min(len(ingredients) * 0.1, 0.4)
    
    # 數量佔比 20%
    if quantity:
        confidence += 0.2
    
    return confidence 