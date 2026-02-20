"""
موقع إسلامي متكامل — القرآن الكريم والسنة النبوية
مطور بواسطة: @m2_byte
GitHub: @m2-byte
"""

from flask import Flask, render_template, request, jsonify, make_response, send_from_directory, g
from datetime import datetime, date, timedelta
import requests
import json
import math
import os
import gzip
import io
import random
import hashlib
import logging
import functools

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Optional: Hijri Library
try:
    from hijri_converter import Hijri, Gregorian
except ImportError:
    Hijri = None
    Gregorian = None

# ═══════════════════════════════════════════════════════════════
#  CONFIGURATION & SETUP
# ═══════════════════════════════════════════════════════════════

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-please-change-in-prod-12345'
    DEBUG = True
    CACHE_TYPE = 'simple'
    JSON_AS_ASCII = False
    # Social
    INSTAGRAM = '@m2_byte'
    GITHUB = '@m2-byte'

app = Flask(__name__)
app.config.from_object(Config)

# ═══════════════════════════════════════════════════════════════
#  PERFORMANCE & VIP FEATURES
# ═══════════════════════════════════════════════════════════════

# GZIP Compression Middleware
@app.after_request
def compress_response(response):
    # Security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

    accept_encoding = request.headers.get('Accept-Encoding', '')
    if response.status_code < 200 or response.status_code >= 300 or 'gzip' not in accept_encoding.lower() or 'Content-Encoding' in response.headers:
        return response
    
    response.direct_passthrough = False
    content = response.get_data()
    
    # Don't compress small responses
    if len(content) < 500:
        return response
        
    gzip_buffer = io.BytesIO()
    gzip_file = gzip.GzipFile(mode='wb', fileobj=gzip_buffer)
    gzip_file.write(content)
    gzip_file.close()
    
    response.set_data(gzip_buffer.getvalue())
    response.headers['Content-Encoding'] = 'gzip'
    response.headers['Content-Length'] = len(response.get_data())
    return response

# CACHING — Improved with Error Handling & Session
_cache = {}
MAX_CACHE_SIZE = 500  # Prevent unbounded memory growth
# Initialize a session for connection pooling and retries
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(max_retries=3)
session.mount('https://', adapter)
session.mount('http://', adapter)

def cached_get(url, ttl=3600, params=None):
    """
    Cache API responses to improve speed.
    Handles connection errors gracefully.
    """
    cache_key = f"{url}{str(params)}"
    now = datetime.now().timestamp()
    
    # Check cache
    if cache_key in _cache:
        data, ts = _cache[cache_key]
        if now - ts < ttl:
            return data
            
    try:
        r = session.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        # Limit cache size
        if len(_cache) >= MAX_CACHE_SIZE:
            oldest_key = min(_cache, key=lambda k: _cache[k][1])
            del _cache[oldest_key]
        _cache[cache_key] = (data, now)
        return data
    except requests.exceptions.RequestException as e:
        logger.warning(f"API Error fetching {url}: {e}")
        # Fallback to expired cache if available
        if cache_key in _cache:
            return _cache[cache_key][0]
        return None
    except ValueError:
        logger.warning(f"API Error decoding JSON from {url}")
        return None

# DATA LOADING
def load_json(filename):
    filepath = os.path.join(os.path.dirname(__file__), 'data', filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# ═══════════════════════════════════════════════════════════════
#  STATIC DATA
# ═══════════════════════════════════════════════════════════════

SURAHS_META = [
    {"id":1,"name":"الفاتحة","name_en":"Al-Fatihah","meaning":"The Opening","verses":7,"type":"meccan"},
    {"id":2,"name":"البقرة","name_en":"Al-Baqarah","meaning":"The Cow","verses":286,"type":"medinan"},
    {"id":3,"name":"آل عمران","name_en":"Ali 'Imran","meaning":"Family of Imran","verses":200,"type":"medinan"},
    {"id":4,"name":"النساء","name_en":"An-Nisa","meaning":"The Women","verses":176,"type":"medinan"},
    {"id":5,"name":"المائدة","name_en":"Al-Ma'idah","meaning":"The Table Spread","verses":120,"type":"medinan"},
    {"id":6,"name":"الأنعام","name_en":"Al-An'am","meaning":"The Cattle","verses":165,"type":"meccan"},
    {"id":7,"name":"الأعراف","name_en":"Al-A'raf","meaning":"The Heights","verses":206,"type":"meccan"},
    {"id":8,"name":"الأنفال","name_en":"Al-Anfal","meaning":"The Spoils of War","verses":75,"type":"medinan"},
    {"id":9,"name":"التوبة","name_en":"At-Tawbah","meaning":"The Repentance","verses":129,"type":"medinan"},
    {"id":10,"name":"يونس","name_en":"Yunus","meaning":"Jonah","verses":109,"type":"meccan"},
    {"id":11,"name":"هود","name_en":"Hud","meaning":"Hud","verses":123,"type":"meccan"},
    {"id":12,"name":"يوسف","name_en":"Yusuf","meaning":"Joseph","verses":111,"type":"meccan"},
    {"id":13,"name":"الرعد","name_en":"Ar-Ra'd","meaning":"The Thunder","verses":43,"type":"medinan"},
    {"id":14,"name":"إبراهيم","name_en":"Ibrahim","meaning":"Abraham","verses":52,"type":"meccan"},
    {"id":15,"name":"الحجر","name_en":"Al-Hijr","meaning":"The Rocky Tract","verses":99,"type":"meccan"},
    {"id":16,"name":"النحل","name_en":"An-Nahl","meaning":"The Bee","verses":128,"type":"meccan"},
    {"id":17,"name":"الإسراء","name_en":"Al-Isra","meaning":"The Night Journey","verses":111,"type":"meccan"},
    {"id":18,"name":"الكهف","name_en":"Al-Kahf","meaning":"The Cave","verses":110,"type":"meccan"},
    {"id":19,"name":"مريم","name_en":"Maryam","meaning":"Mary","verses":98,"type":"meccan"},
    {"id":20,"name":"طه","name_en":"Taha","meaning":"Ta-Ha","verses":135,"type":"meccan"},
    {"id":21,"name":"الأنبياء","name_en":"Al-Anbiya","meaning":"The Prophets","verses":112,"type":"meccan"},
    {"id":22,"name":"الحج","name_en":"Al-Hajj","meaning":"The Pilgrimage","verses":78,"type":"medinan"},
    {"id":23,"name":"المؤمنون","name_en":"Al-Mu'minun","meaning":"The Believers","verses":118,"type":"meccan"},
    {"id":24,"name":"النور","name_en":"An-Nur","meaning":"The Light","verses":64,"type":"medinan"},
    {"id":25,"name":"الفرقان","name_en":"Al-Furqan","meaning":"The Criterion","verses":77,"type":"meccan"},
    {"id":26,"name":"الشعراء","name_en":"Ash-Shu'ara","meaning":"The Poets","verses":227,"type":"meccan"},
    {"id":27,"name":"النمل","name_en":"An-Naml","meaning":"The Ant","verses":93,"type":"meccan"},
    {"id":28,"name":"القصص","name_en":"Al-Qasas","meaning":"The Stories","verses":88,"type":"meccan"},
    {"id":29,"name":"العنكبوت","name_en":"Al-Ankabut","meaning":"The Spider","verses":69,"type":"meccan"},
    {"id":30,"name":"الروم","name_en":"Ar-Rum","meaning":"The Romans","verses":60,"type":"meccan"},
    {"id":31,"name":"لقمان","name_en":"Luqman","meaning":"Luqman","verses":34,"type":"meccan"},
    {"id":32,"name":"السجدة","name_en":"As-Sajdah","meaning":"The Prostration","verses":30,"type":"meccan"},
    {"id":33,"name":"الأحزاب","name_en":"Al-Ahzab","meaning":"The Combined Forces","verses":73,"type":"medinan"},
    {"id":34,"name":"سبأ","name_en":"Saba","meaning":"Sheba","verses":54,"type":"meccan"},
    {"id":35,"name":"فاطر","name_en":"Fatir","meaning":"Originator","verses":45,"type":"meccan"},
    {"id":36,"name":"يس","name_en":"Ya-Sin","meaning":"Ya Sin","verses":83,"type":"meccan"},
    {"id":37,"name":"الصافات","name_en":"As-Saffat","meaning":"Those Ranged in Ranks","verses":182,"type":"meccan"},
    {"id":38,"name":"ص","name_en":"Sad","meaning":"The Letter Sad","verses":88,"type":"meccan"},
    {"id":39,"name":"الزمر","name_en":"Az-Zumar","meaning":"The Groups","verses":75,"type":"meccan"},
    {"id":40,"name":"غافر","name_en":"Ghafir","meaning":"The Forgiver","verses":85,"type":"meccan"},
    {"id":41,"name":"فصلت","name_en":"Fussilat","meaning":"Explained in Detail","verses":54,"type":"meccan"},
    {"id":42,"name":"الشورى","name_en":"Ash-Shura","meaning":"The Consultation","verses":53,"type":"meccan"},
    {"id":43,"name":"الزخرف","name_en":"Az-Zukhruf","meaning":"The Ornaments of Gold","verses":89,"type":"meccan"},
    {"id":44,"name":"الدخان","name_en":"Ad-Dukhan","meaning":"The Smoke","verses":59,"type":"meccan"},
    {"id":45,"name":"الجاثية","name_en":"Al-Jathiyah","meaning":"The Crouching","verses":37,"type":"meccan"},
    {"id":46,"name":"الأحقاف","name_en":"Al-Ahqaf","meaning":"The Wind-Curved Sandhills","verses":35,"type":"meccan"},
    {"id":47,"name":"محمد","name_en":"Muhammad","meaning":"Muhammad","verses":38,"type":"medinan"},
    {"id":48,"name":"الفتح","name_en":"Al-Fath","meaning":"The Victory","verses":29,"type":"medinan"},
    {"id":49,"name":"الحجرات","name_en":"Al-Hujurat","meaning":"The Rooms","verses":18,"type":"medinan"},
    {"id":50,"name":"ق","name_en":"Qaf","meaning":"The Letter Qaf","verses":45,"type":"meccan"},
    {"id":51,"name":"الذاريات","name_en":"Adh-Dhariyat","meaning":"The Winnowing Winds","verses":60,"type":"meccan"},
    {"id":52,"name":"الطور","name_en":"At-Tur","meaning":"The Mount","verses":49,"type":"meccan"},
    {"id":53,"name":"النجم","name_en":"An-Najm","meaning":"The Star","verses":62,"type":"meccan"},
    {"id":54,"name":"القمر","name_en":"Al-Qamar","meaning":"The Moon","verses":55,"type":"meccan"},
    {"id":55,"name":"الرحمن","name_en":"Ar-Rahman","meaning":"The Beneficent","verses":78,"type":"medinan"},
    {"id":56,"name":"الواقعة","name_en":"Al-Waqi'ah","meaning":"The Inevitable","verses":96,"type":"meccan"},
    {"id":57,"name":"الحديد","name_en":"Al-Hadid","meaning":"The Iron","verses":29,"type":"medinan"},
    {"id":58,"name":"المجادلة","name_en":"Al-Mujadila","meaning":"She That Disputeth","verses":22,"type":"medinan"},
    {"id":59,"name":"الحشر","name_en":"Al-Hashr","meaning":"The Exile","verses":24,"type":"medinan"},
    {"id":60,"name":"الممتحنة","name_en":"Al-Mumtahanah","meaning":"She That Is Examined","verses":13,"type":"medinan"},
    {"id":61,"name":"الصف","name_en":"As-Saf","meaning":"The Ranks","verses":14,"type":"medinan"},
    {"id":62,"name":"الجمعة","name_en":"Al-Jumu'ah","meaning":"The Congregation","verses":11,"type":"medinan"},
    {"id":63,"name":"المنافقون","name_en":"Al-Munafiqun","meaning":"The Hypocrites","verses":11,"type":"medinan"},
    {"id":64,"name":"التغابن","name_en":"At-Taghabun","meaning":"The Mutual Disillusion","verses":18,"type":"medinan"},
    {"id":65,"name":"الطلاق","name_en":"At-Talaq","meaning":"The Divorce","verses":12,"type":"medinan"},
    {"id":66,"name":"التحريم","name_en":"At-Tahrim","meaning":"The Prohibition","verses":12,"type":"medinan"},
    {"id":67,"name":"الملك","name_en":"Al-Mulk","meaning":"The Sovereignty","verses":30,"type":"meccan"},
    {"id":68,"name":"القلم","name_en":"Al-Qalam","meaning":"The Pen","verses":52,"type":"meccan"},
    {"id":69,"name":"الحاقة","name_en":"Al-Haqqah","meaning":"The Reality","verses":52,"type":"meccan"},
    {"id":70,"name":"المعارج","name_en":"Al-Ma'arij","meaning":"The Ascending Stairways","verses":44,"type":"meccan"},
    {"id":71,"name":"نوح","name_en":"Nuh","meaning":"Noah","verses":28,"type":"meccan"},
    {"id":72,"name":"الجن","name_en":"Al-Jinn","meaning":"The Jinn","verses":28,"type":"meccan"},
    {"id":73,"name":"المزمل","name_en":"Al-Muzzammil","meaning":"The Enshrouded One","verses":20,"type":"meccan"},
    {"id":74,"name":"المدثر","name_en":"Al-Muddaththir","meaning":"The Cloaked One","verses":56,"type":"meccan"},
    {"id":75,"name":"القيامة","name_en":"Al-Qiyamah","meaning":"The Resurrection","verses":40,"type":"meccan"},
    {"id":76,"name":"الإنسان","name_en":"Al-Insan","meaning":"The Man","verses":31,"type":"medinan"},
    {"id":77,"name":"المرسلات","name_en":"Al-Mursalat","meaning":"The Emissaries","verses":50,"type":"meccan"},
    {"id":78,"name":"النبأ","name_en":"An-Naba","meaning":"The Tidings","verses":40,"type":"meccan"},
    {"id":79,"name":"النازعات","name_en":"An-Nazi'at","meaning":"Those Who Drag Forth","verses":46,"type":"meccan"},
    {"id":80,"name":"عبس","name_en":"Abasa","meaning":"He Frowned","verses":42,"type":"meccan"},
    {"id":81,"name":"التكوير","name_en":"At-Takwir","meaning":"The Overthrowing","verses":29,"type":"meccan"},
    {"id":82,"name":"الانفطار","name_en":"Al-Infitar","meaning":"The Cleaving","verses":19,"type":"meccan"},
    {"id":83,"name":"المطففين","name_en":"Al-Mutaffifin","meaning":"Defrauding","verses":36,"type":"meccan"},
    {"id":84,"name":"الانشقاق","name_en":"Al-Inshiqaq","meaning":"The Sundering","verses":25,"type":"meccan"},
    {"id":85,"name":"البروج","name_en":"Al-Buruj","meaning":"The Mansions of the Stars","verses":22,"type":"meccan"},
    {"id":86,"name":"الطارق","name_en":"At-Tariq","meaning":"The Nightcomer","verses":17,"type":"meccan"},
    {"id":87,"name":"الأعلى","name_en":"Al-A'la","meaning":"The Most High","verses":19,"type":"meccan"},
    {"id":88,"name":"الغاشية","name_en":"Al-Ghashiyah","meaning":"The Overwhelming","verses":26,"type":"meccan"},
    {"id":89,"name":"الفجر","name_en":"Al-Fajr","meaning":"The Dawn","verses":30,"type":"meccan"},
    {"id":90,"name":"البلد","name_en":"Al-Balad","meaning":"The City","verses":20,"type":"meccan"},
    {"id":91,"name":"الشمس","name_en":"Ash-Shams","meaning":"The Sun","verses":15,"type":"meccan"},
    {"id":92,"name":"الليل","name_en":"Al-Layl","meaning":"The Night","verses":21,"type":"meccan"},
    {"id":93,"name":"الضحى","name_en":"Ad-Duhaa","meaning":"The Morning Hours","verses":11,"type":"meccan"},
    {"id":94,"name":"الشرح","name_en":"Ash-Sharh","meaning":"The Relief","verses":8,"type":"meccan"},
    {"id":95,"name":"التين","name_en":"At-Tin","meaning":"The Fig","verses":8,"type":"meccan"},
    {"id":96,"name":"العلق","name_en":"Al-Alaq","meaning":"The Clot","verses":19,"type":"meccan"},
    {"id":97,"name":"القدر","name_en":"Al-Qadr","meaning":"The Power","verses":5,"type":"meccan"},
    {"id":98,"name":"البينة","name_en":"Al-Bayyinah","meaning":"The Clear Proof","verses":8,"type":"medinan"},
    {"id":99,"name":"الزلزلة","name_en":"Az-Zalzalah","meaning":"The Earthquake","verses":8,"type":"medinan"},
    {"id":100,"name":"العاديات","name_en":"Al-Adiyat","meaning":"The Chargers","verses":11,"type":"meccan"},
    {"id":101,"name":"القارعة","name_en":"Al-Qari'ah","meaning":"The Calamity","verses":11,"type":"meccan"},
    {"id":102,"name":"التكاثر","name_en":"At-Takathur","meaning":"The Rivalry in Worldly Increase","verses":8,"type":"meccan"},
    {"id":103,"name":"العصر","name_en":"Al-Asr","meaning":"The Declining Day","verses":3,"type":"meccan"},
    {"id":104,"name":"الهمزة","name_en":"Al-Humazah","meaning":"The Traducer","verses":9,"type":"meccan"},
    {"id":105,"name":"الفيل","name_en":"Al-Fil","meaning":"The Elephant","verses":5,"type":"meccan"},
    {"id":106,"name":"قريش","name_en":"Quraysh","meaning":"Quraysh","verses":4,"type":"meccan"},
    {"id":107,"name":"الماعون","name_en":"Al-Ma'un","meaning":"The Small Kindnesses","verses":7,"type":"meccan"},
    {"id":108,"name":"الكوثر","name_en":"Al-Kawthar","meaning":"The Abundance","verses":3,"type":"meccan"},
    {"id":109,"name":"الكافرون","name_en":"Al-Kafirun","meaning":"The Disbelievers","verses":6,"type":"meccan"},
    {"id":110,"name":"النصر","name_en":"An-Nasr","meaning":"The Divine Support","verses":3,"type":"medinan"},
    {"id":111,"name":"المسد","name_en":"Al-Masad","meaning":"The Palm Fiber","verses":5,"type":"meccan"},
    {"id":112,"name":"الإخلاص","name_en":"Al-Ikhlas","meaning":"The Sincerity","verses":4,"type":"meccan"},
    {"id":113,"name":"الفلق","name_en":"Al-Falaq","meaning":"The Daybreak","verses":5,"type":"meccan"},
    {"id":114,"name":"الناس","name_en":"An-Nas","meaning":"Mankind","verses":6,"type":"meccan"},
]

HADITH_COLLECTIONS = [
    {"id": "ara-bukhari", "name": "صحيح البخاري", "name_en": "Sahih al-Bukhari", "author": "الإمام البخاري", "count": "7563"},
    {"id": "ara-muslim", "name": "صحيح مسلم", "name_en": "Sahih Muslim", "author": "الإمام مسلم", "count": "5362"},
    {"id": "ara-abudawud", "name": "سنن أبي داود", "name_en": "Sunan Abu Dawud", "author": "أبو داود", "count": "4590"},
    {"id": "ara-tirmidhi", "name": "جامع الترمذي", "name_en": "Jami at-Tirmidhi", "author": "الإمام الترمذي", "count": "3891"},
    {"id": "ara-nasai", "name": "سنن النسائي", "name_en": "Sunan an-Nasa'i", "author": "الإمام النسائي", "count": "5662"},
    {"id": "ara-ibnmajah", "name": "سنن ابن ماجه", "name_en": "Sunan Ibn Majah", "author": "ابن ماجه", "count": "4332"},
]

TRANSLATION_MAP = {
    'en.sahih': 'English — Saheeh International',
    'en.hilali': 'English — Hilali & Khan',
    'fr.hamidullah': 'Français — Hamidullah',
    'ur.jalandhry': 'اردو — Jalandhry',
    'tr.diyanet': 'Türkçe — Diyanet',
    'id.indonesian': 'Bahasa Indonesia',
    'de.bubenheim': 'Deutsch — Bubenheim',
    'es.cortes': 'Español — Cortes',
    'ru.kuliev': 'Русский — Kuliev',
    'bn.bengali': 'বাংলা — Bengali',
}

RECITERS = [
    {"id": "ar.alafasy", "name": "مشاري العفاسي", "name_en": "Mishary Rashid Alafasy"},
    {"id": "ar.abdulbasitmurattal", "name": "عبد الباسط عبد الصمد", "name_en": "Abdul Basit (Murattal)"},
    {"id": "ar.abdullahbasfar", "name": "عبدالله بصفر", "name_en": "Abdullah Basfar"},
    {"id": "ar.hudhaify", "name": "الحذيفي", "name_en": "Ali Al-Hudhaifi"},
    {"id": "ar.husary", "name": "محمود خليل الحصري", "name_en": "Mahmoud Khalil Al-Husary"},
    {"id": "ar.mahermuaiqly", "name": "ماهر المعيقلي", "name_en": "Maher Al Muaiqly"},
    {"id": "ar.abdurrahmaansudais", "name": "عبدالرحمن السديس", "name_en": "Abdurrahmaan As-Sudais"},
    {"id": "ar.saoodshuraym", "name": "سعود الشريم", "name_en": "Saood Ash-Shuraym"},
]

# Arabic translations for Hadith section names (API returns English)
HADITH_SECTIONS_AR = {
    # Sahih al-Bukhari
    "Revelation": "بدء الوحي",
    "Belief": "الإيمان",
    "Knowledge": "العلم",
    "Ablutions (Wudu')": "الوضوء",
    "Bathing (Ghusl)": "الغسل",
    "Menstrual Periods": "الحيض",
    "Rubbing hands and feet with dust (Tayammum)": "التيمم",
    "Prayers (Salat)": "الصلاة",
    "Times of the Prayers": "مواقيت الصلاة",
    "Call to Prayers (Adhaan)": "الأذان",
    "Friday Prayer": "الجمعة",
    "Fear Prayer": "صلاة الخوف",
    "The Two Festivals (Eids)": "العيدين",
    "Witr Prayer": "الوتر",
    "Invoking Allah for Rain (Istisqaa)": "الاستسقاء",
    "Eclipses": "الكسوف",
    "Prostration During Recital of Qur'an": "سجود القرآن",
    "Shortening the Prayers (At-Taqseer)": "تقصير الصلاة",
    "Prayer at Night (Tahajjud)": "التهجد",
    "Virtues of Prayer at Masjid Makkah and Madinah": "فضل الصلاة في مسجد مكة والمدينة",
    "Actions while Praying": "العمل في الصلاة",
    "Forgetfulness in Prayer": "السهو",
    "Funerals (Al-Janaa'iz)": "الجنائز",
    "Obligatory Charity Tax (Zakat)": "الزكاة",
    "Hajj (Pilgrimage)": "الحج",
    "`Umrah (Minor pilgrimage)": "العمرة",
    "Pilgrims Prevented from Completing the Pilgrimage": "المحصر",
    "Penalty of Hunting while on Pilgrimage": "جزاء الصيد",
    "Virtues of Madinah": "فضائل المدينة",
    "Fasting": "الصيام",
    "Praying at Night in Ramadaan (Taraweeh)": "التراويح",
    "Virtues of the Night of Qadr": "فضل ليلة القدر",
    "Retiring to a Mosque for Remembrance of Allah (I'tikaf)": "الاعتكاف",
    "Sales and Trade": "البيوع",
    "Hiring": "الإجارة",
    "Agriculture": "المزارعة",
    "Gifts": "الهبة",
    "Witnesses": "الشهادات",
    "Peacemaking": "الصلح",
    "Wills and Testaments (Wasaayaa)": "الوصايا",
    "Fighting for the Cause of Allah (Jihaad)": "الجهاد والسير",
    "Beginning of Creation": "بدء الخلق",
    "Prophets": "الأنبياء",
    "Virtues and Merits of the Prophet (pbuh) and his Companions": "المناقب",
    "Companions of the Prophet": "أصحاب النبي ﷺ",
    "Merits of the Helpers in Madinah (Ansaar)": "مناقب الأنصار",
    "Military Expeditions led by the Prophet (pbuh) (Al-Maghaazi)": "المغازي",
    "Prophetic Commentary on the Qur'an (Tafseer of the Prophet (pbuh))": "التفسير",
    "Virtues of the Qur'an": "فضائل القرآن",
    "Wedlock, Marriage (Nikaah)": "النكاح",
    "Divorce": "الطلاق",
    "Supporting the Family": "النفقات",
    "Food, Meals": "الأطعمة",
    "Hunting, Slaughtering": "الصيد والذبائح",
    "Drinks": "الأشربة",
    "Patients": "المرضى",
    "Medicine": "الطب",
    "Dress": "اللباس",
    "Good Manners and Form (Al-Adab)": "الأدب",
    "Asking Permission": "الاستئذان",
    "Invocations": "الدعوات",
    "To make the Heart Tender (Ar-Riqaq)": "الرقاق",
    "Divine Will (Al-Qadar)": "القدر",
    "Oaths and Vows": "الأيمان والنذور",
    "Laws of Inheritance (Al-Faraa'id)": "الفرائض",
    "Limits and Punishments set by Allah (Hudood)": "الحدود",
    "Blood Money (Ad-Diyat)": "الديات",
    "Apostates": "المرتدين",
    "Interpretation of Dreams": "تعبير الرؤيا",
    "Afflictions and the End of the World": "الفتن",
    "Judgments (Ahkaam)": "الأحكام",
    "Holding Fast to the Qur'an and Sunnah": "الاعتصام بالكتاب والسنة",
    "Oneness, Uniqueness of Allah (Tawheed)": "التوحيد",
    # Sahih Muslim
    "Introduction": "المقدمة",
    "Faith": "الإيمان",
    "Purification (Kitab Al-Taharah)": "الطهارة",
    "Menstruation": "الحيض",
    "Prayer": "الصلاة",
    "Zakat": "الزكاة",
    "Fasts": "الصيام",
    "Pilgrimage": "الحج",
    "Marriage": "النكاح",
    "Suckling": "الرضاع",
    "Transactions": "البيوع",
    "Inheritance": "الفرائض",
    "Gifts": "الهبة",
    "Oaths": "الأيمان",
    "Vows": "النذور",
    "Oaths in Courts": "القسامة والمحاربين",
    "Punishments": "الحدود",
    "Hunting and Slaughter": "الصيد والذبائح",
    "Food and Drink": "الأشربة",
    "Clothing and Adornments": "اللباس والزينة",
    "Jihad": "الجهاد والسير",
    "Government": "الإمارة",
    "Virtue, Enjoining Good Manners": "البر والصلة والآداب",
    "Destiny": "القدر",
    "Knowledge": "العلم",
    "Remembrance of Allah": "الذكر والدعاء",
    "Heart Melting Traditions": "التوبة",
    "Paradise": "الجنة وصفة نعيمها وأهلها",
    "Tribulations": "الفتن وأشراط الساعة",
    "Commentary on the Quran": "تفسير القرآن",
}


def translate_section_name(name):
    """Try to translate English hadith section names to Arabic."""
    return HADITH_SECTIONS_AR.get(name, name)


# ═══════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════

def get_today_verse_index(max_val):
    """Generate a deterministic index for today without polluting global random state."""
    d = date.today().isoformat()
    h = int(hashlib.md5(d.encode()).hexdigest(), 16)
    return h % max_val

# ═══════════════════════════════════════════════════════════════
#  FILTERS
# ═══════════════════════════════════════════════════════════════

@app.template_filter('get_at_index')
def get_at_index_filter(l, i):
    try:
        return l[i]
    except:
        return None

# ═══════════════════════════════════════════════════════════════
#  ROUTES — Pages
# ═══════════════════════════════════════════════════════════════

@app.route('/')
def home():
    return render_template('index.html',
        title="القرآن الكريم والسنة النبوية | منصة إسلامية متكاملة",
        description="موقع إسلامي شامل ومتميز بجودة VIP يحتوي على القرآن الكريم كاملاً، الحديث الشريف، مواقيت الصلاة، الأذكار، وتفاسير القرآن الكريم."
    )

@app.route('/quran')
def quran_index():
    search = request.args.get('q', '').strip()
    filtered = SURAHS_META
    if search:
        filtered = [s for s in SURAHS_META if search.lower() in s['name_en'].lower() or search in s['name'] or search in str(s['id'])]
    return render_template('quran/index.html',
        surahs=filtered,
        search_query=search,
        title="القرآن الكريم — جميع السور",
        description="تصفح المصحف الشريف بالكامل. استمع وتدبر آيات الله مع الترجمة والتفسير."
    )

@app.route('/quran/juz/<int:juz_id>')
def quran_juz(juz_id):
    if juz_id < 1 or juz_id > 30:
        return render_template('404.html'), 404
        
    # Get Juz data
    url = f"https://api.alquran.cloud/v1/juz/{juz_id}/quran-uthmani"
    data = cached_get(url)
    
    if not data or data.get('code') != 200:
        return render_template('404.html'), 500
        
    # Process verses to group by Surah (since a Juz contains parts of Surahs)
    juz_data = data['data']
    verses = juz_data['ayahs']
    
    # Structure: { surah_number: { name: "...", verses: [...] } }
    grouped_verses = {}
    surah_order = [] # To keep order
    
    for v in verses:
        s_num = v['surah']['number']
        if s_num not in grouped_verses:
            grouped_verses[s_num] = {
                'name': v['surah']['name'],
                'englishName': v['surah']['englishName'],
                'number': s_num,
                'verses': []
            }
            surah_order.append(s_num)
        
        # Add verse
        grouped_verses[s_num]['verses'].append({
            'number': v['numberInSurah'],
            'text': v['text'],
            'audio': f"https://cdn.islamic.network/quran/audio/128/ar.alafasy/{v['number']}.mp3", # Global number for audio
            'global_number': v['number']
        })
        
    return render_template('quran/juz.html',
                          juz_id=juz_id,
                          grouped_verses=grouped_verses,
                          surah_order=surah_order,
                          title=f"الجزء {juz_id} — القرآن الكريم",
                          description=f"قراءة واستماع آيات الجزء {juz_id} كاملاً.")

@app.route('/quran/<int:surah_id>')
def quran_surah(surah_id):
    if surah_id < 1 or surah_id > 114:
        return render_template('404.html'), 404

    surah_meta = SURAHS_META[surah_id - 1]
    translation = request.args.get('translation', 'en.sahih')

    # Fetch Arabic text from AlQuran Cloud API (Complete Surah)
    url = f"https://api.alquran.cloud/v1/surah/{surah_id}"
    data = cached_get(url, ttl=86400) # Cache for 24h
    verses = []
    if data and data.get('data') and data['data'].get('ayahs'):
        verses = [{'text': a['text'], 'number': a['numberInSurah']} for a in data['data']['ayahs']]

    # Fetch translation
    trans_verses = []
    if translation:
        turl = f"https://api.alquran.cloud/v1/surah/{surah_id}/{translation}"
        tdata = cached_get(turl, ttl=86400)
        if tdata and tdata.get('data') and tdata['data'].get('ayahs'):
            trans_verses = [{'text': a['text']} for a in tdata['data']['ayahs']]

    prev_surah = SURAHS_META[surah_id - 2] if surah_id > 1 else None
    next_surah = SURAHS_META[surah_id] if surah_id < 114 else None

    return render_template('quran/surah.html',
        surah=surah_meta,
        verses=verses,
        trans_verses=trans_verses,
        prev_surah=prev_surah,
        next_surah=next_surah,
        reciters=RECITERS,
        translations=TRANSLATION_MAP,
        current_translation=translation,
        title=f"سورة {surah_meta['name']} — {surah_meta['name_en']}",
        description=f"اقرأ واستمع لسورة {surah_meta['name']} كاملة. {surah_meta['verses']} آية، {surah_meta['type'] == 'meccan' and 'مكية' or 'مدنية'}."
    )

@app.route('/quran/search')
def quran_search():
    query = request.args.get('q', '').strip()
    # Basic input sanitization
    query = query[:200]  # Limit query length
    results = []
    if query and len(query) >= 2:
        url = f"https://api.alquran.cloud/v1/search/{query}/all/ar"
        data = cached_get(url, ttl=3600)
        if data and data.get('data') and data['data'].get('matches'):
            results = data['data']['matches'][:50]
    return render_template('quran/search.html',
        query=query,
        results=results,
        title=f"بحث في القرآن — {query}" if query else "بحث في القرآن الكريم",
        description="ابحث في القرآن الكريم بسهولة ودقة عالية."
    )

# ═══════════════════════════════════════════════════════════════
#  HADITH SECTION — NEW STRUCTURE
# ═══════════════════════════════════════════════════════════════

@app.route('/hadith')
def hadith_index():
    return render_template('hadith/index.html',
        collections=HADITH_COLLECTIONS,
        title="موسوعة الحديث الشريف",
        description="تصفح كتب الصحاح والسنن الستة في أقوى موسوعة للحديث الشريف."
    )

@app.route('/hadith/<collection>')
def hadith_collection(collection):
    """Shows list of sections/books inside a Hadith collection."""
    col_meta = next((c for c in HADITH_COLLECTIONS if c['id'] == collection), None)
    if not col_meta:
        return render_template('404.html'), 404

    # Fetch sections metadata
    url = f"https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/{collection}.json"
    data = cached_get(url, ttl=86400)
    
    sections = []
    if data and 'metadata' in data:
        raw_sections = data['metadata'].get('sections', {})
        # Convert {"1": "Name"} to list of objects, translate to Arabic where possible
        sections = [
            {'id': k, 'name': translate_section_name(v), 'name_en': v}
            for k, v in raw_sections.items() if v
        ]
        # Sort by ID numerically
        try:
            sections.sort(key=lambda x: int(x['id']))
        except:
            pass  # Fallback if IDs are not ints

    return render_template('hadith/sections.html',
        collection=col_meta,
        sections=sections,
        title=f"{col_meta['name']} — الأقسام",
        description=f"تصفح أقسام وكتب {col_meta['name']}."
    )

@app.route('/hadith/<collection>/<section_id>')
def hadith_section_read(collection, section_id):
    """Reads specific section (Book) of Hadith."""
    col_meta = next((c for c in HADITH_COLLECTIONS if c['id'] == collection), None)
    if not col_meta:
        return render_template('404.html'), 404

    url = f"https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/{collection}/{section_id}.json"
    data = cached_get(url, ttl=86400)
    
    hadiths = data.get('hadiths', []) if data else []
    section_name = data.get('metadata', {}).get('section', {}).get(str(section_id), f"القسم {section_id}") if data else ""

    return render_template('hadith/reader.html',
        collection=col_meta,
        hadiths=hadiths,
        section_id=section_id,
        section_name=section_name,
        title=f"{section_name} — {col_meta['name']}",
        description=f"قراءة {section_name} من {col_meta['name']}."
    )

@app.route('/hadith/search')
def hadith_search():
    query = request.args.get('q', '').strip()
    results = []
    
    if query and len(query) >= 2:
        # Search strategy:
        # Since we don't have a database, we'll search in the "Forty Hadith of Nawawi" (small collection)
        # as a demonstrated feature, or use a cached external search if available.
        # For this VIP demo, we will simulated a search in a local subset or use an API if available.
        
        # Actually, let's try to search in the first few sections of Bukhari/Muslim if cached,
        # otherwise act as a "demo" search for specific terms or show a message.
        
        # REAL IMPLEMENTATION START:
        # We'll search in 'ara-nawawi' (40 Hadith) because it's small and likely to be quick to fetch/cache.
        try:
            url = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/ara-nawawi.json"
            data = cached_get(url, ttl=86400 * 7)
            if data and 'hadiths' in data:
                # Naive in-memory search
                for h in data['hadiths']:
                    text = h.get('text', '')
                    if query in text:
                        # Highlight match? Maybe later.
                        h['collection'] = {'name': 'الأربعين النووية', 'id': 'ara-nawawi'}
                        results.append(h)
                        if len(results) >= 20: break
        except Exception as e:
            logger.warning(f"Hadith search error: {e}")

    return render_template('hadith/search.html',
        query=query,
        results=results,
        title=f"بحث في الحديث — {query}" if query else "بحث في الحديث الشريف",
        description="بحث سريع في الأحاديث النبوية (تجريبي في الأربعين النووية)."
    )

# ═══════════════════════════════════════════════════════════════
#  RELIGIOUS TOOLS
# ═══════════════════════════════════════════════════════════════

@app.route('/prayer-times')
def prayer_times():
    return render_template('prayer_times.html',
        title="مواقيت الصلاة الدقيقة",
        description="أوقات الصلاة دقيقة حسب موقعك الجغرافي مع تنبيهات للأذان وإمساكية."
    )

@app.route('/qibla')
def qibla():
    return render_template('qibla.html',
        title="اتجاه القبلة — الواقع المعزز",
        description="بوصلة ذكية دقيقة لتحديد اتجاه القبلة من أي مكان في العالم."
    )

@app.route('/adhkar')
def adhkar():
    adhkar_data = load_json('adhkar.json')
    # Grouping logic
    groups = {'morning': [], 'evening': [], 'after_prayer': []}
    for a in adhkar_data:
        cat = a.get('category')
        if cat in groups:
            groups[cat].append(a)
            
    return render_template('adhkar.html',
        morning=groups['morning'],
        evening=groups['evening'],
        after_prayer=groups['after_prayer'],
        title="حصن المسلم — الأذكار اليومية",
        description="أذكار الصباح والمساء الصحيحة وأذكار ما بعد الصلاة."
    )

@app.route('/names')
def names():
    names_data = load_json('names.json')
    return render_template('names.html',
        names=names_data,
        title="أسماء الله الحسنى",
        description="شرح ومعاني أسماء الله الحسنى التسعة والتسعين."
    )

@app.route('/calendar')
def calendar():
    hijri_date = None
    if Gregorian:
        try:
            today = date.today()
            h = Gregorian(today.year, today.month, today.day).to_hijri()
            months = ['محرم','صفر','ربيع الأول','ربيع الثاني','جمادى الأولى','جمادى الآخرة','رجب','شعبان','رمضان','شوال','ذو القعدة','ذو الحجة']
            hijri_date = {
                'day': h.day,
                'month': months[h.month - 1],
                'year': h.year,
                'formatted': f"{h.day} {months[h.month - 1]} {h.year} هـ"
            }
        except Exception:
            pass
    return render_template('calendar.html',
        hijri_date=hijri_date,
        title="التقويم الهجري",
        description="التقويم الهجري والميلادي مع محول تواريخ دقيق."
    )

# ═══════════════════════════════════════════════════════════════
#  API ENDPOINTS (VIP)
# ═══════════════════════════════════════════════════════════════

@app.route('/api/prayer-times')
def api_prayer_times():
    lat = request.args.get('lat')
    lng = request.args.get('lng')
    if not lat or not lng:
        return jsonify({'error': 'Missing coordinates'}), 400
    
    try:
        lat = float(lat)
        lng = float(lng)
    except ValueError:
        return jsonify({'error': 'Invalid coordinates'}), 400

    url = f"https://api.aladhan.com/v1/timings?latitude={lat}&longitude={lng}&method=4"  # 4 = Umm Al-Qura
    data = cached_get(url, ttl=1800)
    
    if data and 'data' in data:
        t = data['data']['timings']
        h = data['data']['date']['hijri']
        return jsonify({
            'times': t,
            'hijri': f"{h['day']} {h['month']['ar']} {h['year']}"
        })
    return jsonify({'error': 'Provider error'}), 503

@app.route('/api/tafsir/<int:surah>/<int:ayah>')
def api_tafsir(surah, ayah):
    """Get Tafsir (Ibn Kathir or Saadi) for a specific verse."""
    # Using AlQuran Cloud with tafsir edition or similar (or mock for MVP if complex)
    # Using `tafsir.api` is better but for now let's use AlQuran Cloud 'ar.muyassar' as simplified tafsir
    url = f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/ar.muyassar"
    data = cached_get(url, ttl=86400*7)
    if data and 'data' in data:
        return jsonify({'text': data['data']['text'], 'source': 'تفسير الميسر'})
    return jsonify({'text': 'تفسير غير متاح حالياً.', 'source': ''})

@app.route('/api/vod')
def api_vod():
    """Returns Verse of the Day (JSON) — deterministic per day without polluting global random."""
    surah_idx = get_today_verse_index(len(SURAHS_META))
    s = SURAHS_META[surah_idx]
    ayah_idx = get_today_verse_index(s['verses'])
    a = ayah_idx + 1  # 1-based
    
    # Get Text
    url = f"https://api.alquran.cloud/v1/ayah/{s['id']}:{a}"
    data = cached_get(url)
    text = ''
    if data and data.get('data'):
        text = data['data'].get('text', '')
    
    return jsonify({
        'surah': s['name'],
        'surah_en': s['name_en'],
        'ayah': a,
        'text': text,
        'link': f"/quran/{s['id']}?play={a}"
    })

@app.route('/api/qibla')
def api_qibla():
    """Calculate Qibla direction and distance from given coordinates."""
    try:
        lat = float(request.args.get('lat', 0))
        lng = float(request.args.get('lng', 0))
    except ValueError:
        return jsonify({'error': 'Invalid coordinates'}), 400

    # Kaaba coordinates
    KAABA_LAT = 21.422487
    KAABA_LNG = 39.826206

    # Convert to radians
    lat_r = math.radians(lat)
    lng_r = math.radians(lng)
    k_lat_r = math.radians(KAABA_LAT)
    k_lng_r = math.radians(KAABA_LNG)

    # Calculate Direction (Bearing)
    y = math.sin(k_lng_r - lng_r) * math.cos(k_lat_r)
    x = math.cos(lat_r) * math.sin(k_lat_r) - math.sin(lat_r) * math.cos(k_lat_r) * math.cos(k_lng_r - lng_r)
    bearing = (math.degrees(math.atan2(y, x)) + 360) % 360

    # Calculate Distance (Haversine)
    R = 6371  # Earth radius in km
    dlat = k_lat_r - lat_r
    dlng = k_lng_r - lng_r
    a = math.sin(dlat/2)**2 + math.cos(lat_r) * math.cos(k_lat_r) * math.sin(dlng/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c

    return jsonify({
        'direction': bearing,
        'distance': distance
    })

@app.route('/api/ip-geo')
def api_ip_geo():
    """Server-side IP Geolocation proxy to avoid adblockers."""
    try:
        # Get client IP
        if request.headers.getlist("X-Forwarded-For"):
            ip = request.headers.getlist("X-Forwarded-For")[0]
        else:
            ip = request.remote_addr
            
        # Use ipwho.is (free, no auth)
        url = f"http://ipwho.is/{ip}" if ip != '127.0.0.1' else "http://ipwho.is/"
        data = cached_get(url, ttl=3600)
        
        if data and data.get('success'):
            return jsonify({
                'success': True,
                'latitude': data['latitude'],
                'longitude': data['longitude']
            })
        return jsonify({'success': False, 'error': 'Provider failed'}), 503
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/convert-date')
def api_convert_date():
    """Convert Gregorian date to Hijri with optional regional adjustment."""
    date_str = request.args.get('date')
    # adjustment: 0 = astronomical (default), 1 = +1 day (Saudi/Gulf), -1 = -1 day
    try:
        adjustment = int(request.args.get('adj', 0))
        adjustment = max(-2, min(2, adjustment))  # Clamp to ±2
    except ValueError:
        adjustment = 0

    if not date_str:
        return jsonify({'error': 'Missing date'}), 400

    try:
        y, m, d = map(int, date_str.split('-'))
        if Gregorian:
            # Apply adjustment to the Gregorian date before conversion
            from datetime import date as date_cls, timedelta
            greg = date_cls(y, m, d) + timedelta(days=adjustment)
            h = Gregorian(greg.year, greg.month, greg.day).to_hijri()
            months = ['محرم','صفر','ربيع الأول','ربيع الثاني','جمادى الأولى','جمادى الآخرة','رجب','شعبان','رمضان','شوال','ذو القعدة','ذو الحجة']
            formatted = f"{h.day} {months[h.month - 1]} {h.year} هـ"
            return jsonify({'formatted': formatted, 'day': h.day, 'month': h.month, 'year': h.year})
        else:
            return jsonify({'error': 'Hijri converter library missing'}), 503
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

@app.route('/api/audio-url')
def api_audio_url():
    surah = request.args.get('surah')
    ayah = request.args.get('ayah')
    reciter = request.args.get('reciter', 'ar.alafasy')
    url = f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/{reciter}"
    data = cached_get(url, ttl=86400)
    if data and data.get('data'):
        # Prefer secondary (MP3) or primary
        audio = data['data'].get('audio')
        if not audio:
            audio = data['data'].get('audioSecondary', [None])[0]
        return jsonify({'audio_url': audio})
    return jsonify({'error': 'Not found'}), 404

# ═══════════════════════════════════════════════════════════════
#  SEO & SITEMAP
# ═══════════════════════════════════════════════════════════════

@app.route('/sitemap.xml')
def sitemap():
    base = request.host_url.rstrip('/')
    urls = []
    
    # Static priority pages
    urls.append({'loc': f"{base}/", 'p': '1.0'})
    urls.append({'loc': f"{base}/quran", 'p': '0.9'})
    urls.append({'loc': f"{base}/hadith", 'p': '0.8'})
    urls.append({'loc': f"{base}/prayer-times", 'p': '0.8'})
    urls.append({'loc': f"{base}/adhkar", 'p': '0.7'})
    urls.append({'loc': f"{base}/names", 'p': '0.7'})
    urls.append({'loc': f"{base}/qibla", 'p': '0.6'})
    urls.append({'loc': f"{base}/calendar", 'p': '0.6'})
    
    # Dynamic Surah pages
    for s in SURAHS_META:
        urls.append({'loc': f"{base}/quran/{s['id']}", 'p': '0.7'})

    # Hadith collection pages
    for c in HADITH_COLLECTIONS:
        urls.append({'loc': f"{base}/hadith/{c['id']}", 'p': '0.6'})
        
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for u in urls:
        xml += f"  <url><loc>{u['loc']}</loc><priority>{u['p']}</priority><changefreq>weekly</changefreq></url>\n"
    xml += '</urlset>'
    
    response = make_response(xml)
    response.headers["Content-Type"] = "application/xml"
    return response

@app.route('/robots.txt')
def robots():
    base = request.host_url.rstrip('/')
    txt = f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml"
    response = make_response(txt)
    response.headers["Content-Type"] = "text/plain"
    return response

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    logger.error(f"Internal Server Error: {e}")
    return render_template('404.html'), 500



if __name__ == '__main__':
    logger.info("🕌 Starting Islamic VIP Website on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
