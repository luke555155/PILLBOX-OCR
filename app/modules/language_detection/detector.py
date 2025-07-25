import logging
import os
from typing import Optional, Dict, List
from langdetect import detect as langdetect_detect
from langdetect import DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

# 確保語言偵測結果的一致性
DetectorFactory.seed = 0

logger = logging.getLogger(__name__)

# 支援的語言映射
LANGUAGE_MAP = {
    'zh': 'zh-tw',  # 中文 (預設為繁體中文)
    'zh-cn': 'zh-cn',  # 簡體中文
    'zh-tw': 'zh-tw',  # 繁體中文
    'en': 'en',  # 英文
    'ja': 'ja',  # 日文
    'ko': 'ko'   # 韓文
}

# 預設語言
DEFAULT_LANGUAGE = 'zh-tw'

def detect_language_langdetect(text: str) -> str:
    """
    檢測文本中的主要語言 (langdetect fallback)
    """
    if not text or len(text.strip()) < 5:
        logger.warning(f"文本過短或為空，無法進行可靠的語言偵測: '{text}'")
        return DEFAULT_LANGUAGE
    try:
        detected_lang = langdetect_detect(text)
        logger.info(f"偵測到語言: {detected_lang}")
        mapped_lang = LANGUAGE_MAP.get(detected_lang, DEFAULT_LANGUAGE)
        if detected_lang == 'zh':
            mapped_lang = detect_chinese_variant(text)
        logger.info(f"映射後語言: {mapped_lang}")
        return mapped_lang
    except LangDetectException as e:
        logger.error(f"語言偵測失敗: {str(e)}")
        return DEFAULT_LANGUAGE

def detect_chinese_variant(text: str) -> str:
    """
    區分繁體和簡體中文
    
    參數:
        text: 中文文本
        
    返回:
        'zh-tw' 表示繁體中文，'zh-cn' 表示簡體中文
    """
    # 簡體中文獨有字符集
    simplified_chars = set('专东么买乾亚产亲亿仅从仓价众优伦伟传估侣储光兴决况冻净准凉减凑几划则刘别制刹剑剩劳势匀华协单卖占卫厂历厅压厕厘发变叹后向吓吕听启吴呐呕员响哑唤啰啴喷嘘嘱团园国图圆圣场坏块坛垄垒埋执堕塑塔填境墙壮声壳处备复够头夹夺奋奖妇妈妩姊姜娄娱婴婶媪嫒实宠审宪宽寝对寻导尔尝尴层屉属岁岗峦崭巢币师带帮干并幸广库废廿开异弃张弹强归当录彦彻征径忆忏怀态总恋恒恳恶悬情惊惩惯愤慑懒戏战戮户扑执扩扰报担拟拢拥拦择挂挚挛挤挥捆据掷摇摄摊摧敌敛数斋斗断昙昼显晋晒晓晕晖暂历暧术朴机杀杂权条来杰极构枢枣栋栏树样桢检椅楼榄槛毁气氧汇汉沟泄泪泽洁洼浊测浓涛涝润涨渐渗湿温溃滚满滥漓潜灭灯灵灾灿炀炼烁烂烦烧爱爷牍牵牺犊状犷独狭狮猎献猪猫猬玛玮环现玺珐珑琏琐琼瑶疮疯痒痖瘘瘪癣皑皱盏盐监盖盘眍着矫矾矿砖础硕碍碱磷礼祸离秃种积称窜窝竖竞笔笺笼筑筝筹签简粤糕系紧絷纟纠红约级纪纬纱纲纳纵纷纸纺纽线练组绀绁绊绌绍绎经绑绒结绕绘给络绝绞统绢绣绥绦继绨绩绪绫续绮绯绰绳维绵绷绸绺绻综绽绾绿缀缁缄缅缆缉缎缓缔缕编缚缜缝缠缢缤缨缩缭缮缯缰缴缵罂网罗罚罢罴羁羡翘耻聂胆脉脏脓脸臭舆舍舰舱艰艺节芈芗芜苍苹茑范茧荆荐荚药莱莲获莹莺渐玛玮环现玺珐珑琏琐琼瑶疮疯痒痖瘘瘪癣皑皱盏盐监盖盘眍着矫矾砖础硕碍碱礼祸离秃种积称窜窝竖竞笔笺筑筝筹签简粤糕系纪纬纱纲纳纵纷纸纺纽线练组绀绁绊绌绍绎经绑绒结绕绘给络绝绞统绢绣绥绦继绨绩绪绫续绮绯绰绳维绵绷绸绺绻综绽绾绿缀缁缄缅缆缉缎缓缔缕编缚缜缝缠缢缤缨缩缭缮缯缰缴缵罂网罗罚罢羁羡翘耻聂胆脉脏脓脸臭舆舍舰舱艰艺节芈芗芜苍苹茑范茧荆荐荚药莱莲获莹莺')

    # 繁體中文獨有字符集
    traditional_chars = set('專東麼買乾亞產親億僅從倉價眾優倫偉傳估侶儲光興決況凍淨準涼減湊幾劃則劉別製剎劍剩勞勢勻華協單賣占衛廠歷廳壓廁釐發變嘆後向嚇呂聽啟吳吶嘔員響啞喚囉嗡噴噓囑團園國圖圓聖場壞塊壇壟壘埋執墮塑塔填境牆壯聲殼處備複夠頭夾奪奮獎婦媽嫵姊姜婁娛嬰嬸媼嬡實寵審憲寬寢對尋導爾嘗尷層屜屬歲崗巒嶄巢幣師帶幫幹並幸廣庫廢廿開異棄張彈強歸當錄彥徹征徑憶懺懷態總戀恆懇惡懸情驚懲慣憤懾懶戲戰戮戶撲執擴擾報擔擬攏擁攔擇掛摯攣擠揮捆據擲搖攝攤撲敵斂數齋鬥斷曇晝顯晉曬曉暈暉暫歷曖術樸機殺雜權條來傑極構樞棗棟欄樹樣樟檢椅樓欖檻毀氣氧匯漢溝洩淚澤潔窪濁測濃濤澇潤漲漸滲溼溫潰滾滿濫瀝潛滅燈靈災燦煬煉爍爛煩燒愛爺牘牽犧犢狀獷獨狹獅獵獻豬貓蝟瑪瑋環現璽琺瓏璉瑣瓊瑤瘡瘋癢癆瘺瘪癬皚皺盞鹽監蓋盤瞍著矯礬礦磚礎碩礙鹼磷禮禍離禿種積稱竄窩豎競筆箋籠築箏籌簽簡粵糕系緊縶糸糾紅約級紀緯紗綱納縱紛紙紡紐線練組紺紲絆絀紹繹經綁絨結繞繪給絡絕絞統絹繡綏絛繼綯績緒綠維綿繃綢綹綣綜綻綰綠綴緇緘緬縴緝緞緩締縷編縛緹縫縞縑縴縵縲繆縯繅纓縮繾繯繰繳掘罌網羅罰罷羆羈羨翹恥聶膽脈臟膿臉臭輿舍艦艙艱藝節芎芻藍苧茜菴荊莢萊蓮獲瑩鶯鶴縣麵埡墻檐癤項餘姸')
    
    # 計算簡體和繁體字符的出現次數
    simplified_count = sum(1 for char in text if char in simplified_chars)
    traditional_count = sum(1 for char in text if char in traditional_chars)
    
    # 基於出現次數判斷
    if simplified_count > traditional_count:
        return 'zh-cn'
    else:
        return 'zh-tw'

# 如果有FastText或CLD3模型，可以添加更複雜的檢測邏輯
try:
    import fasttext
    FASTTEXT_MODEL_PATH = os.environ.get("FASTTEXT_MODEL_PATH", "models/fasttext/lid.176.bin")
    if os.path.exists(FASTTEXT_MODEL_PATH):
        logger.info(f"載入FastText語言檢測模型: {FASTTEXT_MODEL_PATH}")
        fasttext_model = fasttext.load_model(FASTTEXT_MODEL_PATH)
        def detect_language_fasttext(text: str) -> str:
            """使用FastText檢測語言"""
            try:
                result = fasttext_model.predict(text.replace('\n', ' '))
                lang_code = result[0][0].replace('__label__', '')
                confidence = result[1][0]
                logger.info(f"FastText檢測語言: {lang_code}, 信心度: {confidence:.4f}")
                if lang_code.startswith('zh'):
                    return detect_chinese_variant(text)
                else:
                    return LANGUAGE_MAP.get(lang_code, DEFAULT_LANGUAGE)
            except Exception as e:
                logger.error(f"FastText語言檢測失敗: {str(e)}")
                return detect_language_langdetect(text)  # 直接 fallback 到 langdetect
        detect_language = detect_language_fasttext
        logger.info("成功啟用FastText語言檢測")
    else:
        logger.warning(f"找不到FastText模型: {FASTTEXT_MODEL_PATH}，使用基本語言檢測")
        detect_language = detect_language_langdetect
except ImportError:
    logger.info("未安裝FastText，使用基本語言檢測")
    detect_language = detect_language_langdetect 