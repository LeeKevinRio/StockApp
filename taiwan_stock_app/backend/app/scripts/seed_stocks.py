"""
Stock Database Seeder
Populates the database with Taiwan and US stocks
"""
import sys
import os
import logging
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import SessionLocal, engine
from app.models.stock import Stock, Base

logger = logging.getLogger(__name__)

# Create tables if not exist
Base.metadata.create_all(bind=engine)

# Taiwan Stocks (TWSE - 上市)
TAIWAN_TWSE_STOCKS = [
    # 半導體
    ("2330", "台積電", "TSMC", "半導體業", "TWSE"),
    ("2303", "聯電", "UMC", "半導體業", "TWSE"),
    ("2454", "聯發科", "MediaTek", "半導體業", "TWSE"),
    ("3711", "日月光投控", "ASE Technology", "半導體業", "TWSE"),
    ("2379", "瑞昱", "Realtek", "半導體業", "TWSE"),
    ("3034", "聯詠", "Novatek", "半導體業", "TWSE"),
    ("2408", "南亞科", "Nanya Technology", "半導體業", "TWSE"),
    ("6415", "矽力-KY", "Silergy", "半導體業", "TWSE"),
    ("3529", "力旺", "eMemory", "半導體業", "TWSE"),
    ("2449", "京元電子", "King Yuan", "半導體業", "TWSE"),

    # 電子零組件
    ("2317", "鴻海", "Hon Hai", "電子零組件業", "TWSE"),
    ("2382", "廣達", "Quanta", "電子零組件業", "TWSE"),
    ("2357", "華碩", "ASUS", "電子零組件業", "TWSE"),
    ("2324", "仁寶", "Compal", "電子零組件業", "TWSE"),
    ("2353", "宏碁", "Acer", "電子零組件業", "TWSE"),
    ("2301", "光寶科", "Lite-On", "電子零組件業", "TWSE"),
    ("2308", "台達電", "Delta Electronics", "電子零組件業", "TWSE"),
    ("2327", "國巨", "Yageo", "電子零組件業", "TWSE"),
    ("2395", "研華", "Advantech", "電子零組件業", "TWSE"),
    ("3231", "緯創", "Wistron", "電子零組件業", "TWSE"),
    ("2356", "英業達", "Inventec", "電子零組件業", "TWSE"),
    ("2345", "智邦", "Accton", "電子零組件業", "TWSE"),
    ("2377", "微星", "MSI", "電子零組件業", "TWSE"),
    ("2474", "可成", "Catcher", "電子零組件業", "TWSE"),
    ("3008", "大立光", "Largan", "電子零組件業", "TWSE"),
    ("2354", "鴻準", "Foxconn Technology", "電子零組件業", "TWSE"),

    # 金融業
    ("2881", "富邦金", "Fubon Financial", "金融保險業", "TWSE"),
    ("2882", "國泰金", "Cathay Financial", "金融保險業", "TWSE"),
    ("2884", "玉山金", "E.SUN Financial", "金融保險業", "TWSE"),
    ("2885", "元大金", "Yuanta Financial", "金融保險業", "TWSE"),
    ("2886", "兆豐金", "Mega Financial", "金融保險業", "TWSE"),
    ("2887", "台新金", "Taishin Financial", "金融保險業", "TWSE"),
    ("2880", "華南金", "Hua Nan Financial", "金融保險業", "TWSE"),
    ("2883", "開發金", "CDIB Financial", "金融保險業", "TWSE"),
    ("2888", "新光金", "Shin Kong Financial", "金融保險業", "TWSE"),
    ("2890", "永豐金", "SinoPac Financial", "金融保險業", "TWSE"),
    ("2891", "中信金", "CTBC Financial", "金融保險業", "TWSE"),
    ("2892", "第一金", "First Financial", "金融保險業", "TWSE"),
    ("5880", "合庫金", "TCB Financial", "金融保險業", "TWSE"),

    # 傳產 - 塑化
    ("1301", "台塑", "Formosa Plastics", "塑膠工業", "TWSE"),
    ("1303", "南亞", "Nan Ya Plastics", "塑膠工業", "TWSE"),
    ("1326", "台化", "Formosa Chemicals", "塑膠工業", "TWSE"),
    ("6505", "台塑化", "FPCC", "油電燃氣業", "TWSE"),

    # 傳產 - 鋼鐵
    ("2002", "中鋼", "China Steel", "鋼鐵工業", "TWSE"),
    ("2006", "東和鋼鐵", "Tung Ho Steel", "鋼鐵工業", "TWSE"),
    ("2014", "中鴻", "Chung Hung Steel", "鋼鐵工業", "TWSE"),

    # 傳產 - 航運
    ("2603", "長榮", "Evergreen Marine", "航運業", "TWSE"),
    ("2609", "陽明", "Yang Ming Marine", "航運業", "TWSE"),
    ("2615", "萬海", "Wan Hai Lines", "航運業", "TWSE"),
    ("2618", "長榮航", "EVA Airways", "航運業", "TWSE"),
    ("2610", "華航", "China Airlines", "航運業", "TWSE"),

    # 傳產 - 食品
    ("1216", "統一", "Uni-President", "食品工業", "TWSE"),
    ("1227", "佳格", "Standard Foods", "食品工業", "TWSE"),
    ("2912", "統一超", "President Chain Store", "貿易百貨業", "TWSE"),

    # 傳產 - 紡織
    ("1402", "遠東新", "Far Eastern New Century", "紡織纖維", "TWSE"),
    ("1476", "儒鴻", "Eclat Textile", "紡織纖維", "TWSE"),

    # 傳產 - 水泥
    ("1101", "台泥", "Taiwan Cement", "水泥工業", "TWSE"),
    ("1102", "亞泥", "Asia Cement", "水泥工業", "TWSE"),

    # 傳產 - 其他
    ("1605", "華新", "Walsin Lihwa", "電線電纜", "TWSE"),
    ("2105", "正新", "Cheng Shin Rubber", "橡膠工業", "TWSE"),
    ("2207", "和泰車", "Hotai Motor", "汽車工業", "TWSE"),
    ("9904", "寶成", "Pou Chen", "其他業", "TWSE"),
    ("2049", "上銀", "HIWIN", "電機機械", "TWSE"),
    ("1504", "東元", "TECO Electric", "電機機械", "TWSE"),
    ("2404", "漢唐", "Han Tang Technology", "其他電子業", "TWSE"),

    # 通訊網路
    ("2412", "中華電", "Chunghwa Telecom", "通信網路業", "TWSE"),
    ("3045", "台灣大", "Taiwan Mobile", "通信網路業", "TWSE"),
    ("4904", "遠傳", "Far EasTone", "通信網路業", "TWSE"),

    # 生技醫療
    ("4743", "合一", "Oneness Biotech", "生技醫療業", "TWSE"),
    ("6446", "藥華藥", "PharmaEssentia", "生技醫療業", "TWSE"),
    ("1760", "寶齡富錦", "Panion", "生技醫療業", "TWSE"),

    # 觀光餐旅
    ("2707", "晶華", "Grand Hotel", "觀光餐旅業", "TWSE"),

    # 電子通路
    ("2347", "聯強", "Synnex Technology", "電子通路業", "TWSE"),
    ("3702", "大聯大", "WPG Holdings", "電子通路業", "TWSE"),

    # 光電業
    ("2409", "友達", "AU Optronics", "光電業", "TWSE"),
    ("3481", "群創", "Innolux", "光電業", "TWSE"),

    # 其他重要股票
    ("2344", "華邦電", "Winbond", "半導體業", "TWSE"),
    ("2337", "旺宏", "Macronix", "半導體業", "TWSE"),
    ("2388", "威盛", "VIA Technologies", "半導體業", "TWSE"),
    ("3037", "欣興", "Unimicron", "電子零組件業", "TWSE"),
    ("3443", "創意", "Global Unichip", "半導體業", "TWSE"),
    ("5269", "祥碩", "ASMedia Technology", "半導體業", "TWSE"),
    ("3661", "世芯-KY", "Alchip", "半導體業", "TWSE"),
    ("6488", "環球晶", "GlobalWafers", "半導體業", "TWSE"),
]

# Taiwan Stocks (TPEx - 上櫃)
TAIWAN_TPEX_STOCKS = [
    ("3105", "穩懋", "WIN Semiconductors", "半導體業", "TPEx"),
    ("6409", "旭隼", "ASPEED Technology", "半導體業", "TPEx"),
    ("5274", "信驊", "Aspeed Technology", "半導體業", "TPEx"),
    ("6147", "頎邦", "Chipbond", "半導體業", "TPEx"),
    ("3293", "鑫潭", "Altek", "光電業", "TPEx"),
    ("6510", "精測", "Chroma ATE", "電子零組件業", "TPEx"),
    ("8454", "富邦媒", "Momo", "貿易百貨業", "TPEx"),
    ("6592", "和潤企業", "Hotai Finance", "其他業", "TPEx"),
    ("6533", "晶心科", "Andes Technology", "半導體業", "TPEx"),
    ("3163", "波若威", "Brogent", "其他電子業", "TPEx"),
    ("6472", "保瑞", "Bora Pharmaceuticals", "生技醫療業", "TPEx"),
    ("4966", "譜瑞-KY", "Parade Technologies", "半導體業", "TPEx"),
    ("5371", "中光電", "Coretronic", "光電業", "TPEx"),
    ("3264", "欣銓", "Ardentec", "半導體業", "TPEx"),
    ("8150", "南茂", "ChipMOS", "半導體業", "TPEx"),
    ("6568", "宏觀", "Macrovision", "半導體業", "TPEx"),
    ("6531", "愛普*", "ASEH", "半導體業", "TPEx"),
    ("4190", "佐登-KY", "Jordan", "生技醫療業", "TPEx"),
    ("6903", "崇友", "Chung Yu", "電機機械", "TPEx"),
    ("3707", "漢磊", "Episil", "半導體業", "TPEx"),
]

# US Stocks (Major Companies)
US_STOCKS = [
    # Technology - FAANG+
    ("AAPL", "蘋果", "Apple Inc.", "Technology", "NASDAQ"),
    ("MSFT", "微軟", "Microsoft Corporation", "Technology", "NASDAQ"),
    ("GOOGL", "Alphabet A", "Alphabet Inc. Class A", "Technology", "NASDAQ"),
    ("GOOG", "Alphabet C", "Alphabet Inc. Class C", "Technology", "NASDAQ"),
    ("AMZN", "亞馬遜", "Amazon.com Inc.", "Consumer Cyclical", "NASDAQ"),
    ("META", "Meta", "Meta Platforms Inc.", "Technology", "NASDAQ"),
    ("NVDA", "輝達", "NVIDIA Corporation", "Technology", "NASDAQ"),
    ("TSLA", "特斯拉", "Tesla Inc.", "Consumer Cyclical", "NASDAQ"),
    ("NFLX", "Netflix", "Netflix Inc.", "Communication Services", "NASDAQ"),

    # Technology - Semiconductors
    ("AMD", "超微", "Advanced Micro Devices", "Technology", "NASDAQ"),
    ("INTC", "英特爾", "Intel Corporation", "Technology", "NASDAQ"),
    ("QCOM", "高通", "Qualcomm Inc.", "Technology", "NASDAQ"),
    ("AVGO", "博通", "Broadcom Inc.", "Technology", "NASDAQ"),
    ("TXN", "德州儀器", "Texas Instruments", "Technology", "NASDAQ"),
    ("MU", "美光", "Micron Technology", "Technology", "NASDAQ"),
    ("ASML", "艾司摩爾", "ASML Holding", "Technology", "NASDAQ"),
    ("TSM", "台積電ADR", "Taiwan Semiconductor ADR", "Technology", "NYSE"),
    ("LRCX", "科林研發", "Lam Research", "Technology", "NASDAQ"),
    ("AMAT", "應材", "Applied Materials", "Technology", "NASDAQ"),
    ("KLAC", "科磊", "KLA Corporation", "Technology", "NASDAQ"),
    ("MRVL", "邁威爾", "Marvell Technology", "Technology", "NASDAQ"),
    ("ON", "安森美", "ON Semiconductor", "Technology", "NASDAQ"),
    ("ARM", "安謀", "Arm Holdings", "Technology", "NASDAQ"),

    # Technology - Software & Internet
    ("CRM", "賽富時", "Salesforce Inc.", "Technology", "NYSE"),
    ("ORCL", "甲骨文", "Oracle Corporation", "Technology", "NYSE"),
    ("ADBE", "Adobe", "Adobe Inc.", "Technology", "NASDAQ"),
    ("NOW", "ServiceNow", "ServiceNow Inc.", "Technology", "NYSE"),
    ("SNOW", "Snowflake", "Snowflake Inc.", "Technology", "NYSE"),
    ("PLTR", "Palantir", "Palantir Technologies", "Technology", "NYSE"),
    ("UBER", "Uber", "Uber Technologies", "Technology", "NYSE"),
    ("SHOP", "Shopify", "Shopify Inc.", "Technology", "NYSE"),
    ("SQ", "Block", "Block Inc.", "Technology", "NYSE"),
    ("PYPL", "PayPal", "PayPal Holdings", "Technology", "NASDAQ"),
    ("COIN", "Coinbase", "Coinbase Global", "Financial Services", "NASDAQ"),
    ("CRWD", "CrowdStrike", "CrowdStrike Holdings", "Technology", "NASDAQ"),
    ("ZS", "Zscaler", "Zscaler Inc.", "Technology", "NASDAQ"),
    ("PANW", "Palo Alto", "Palo Alto Networks", "Technology", "NASDAQ"),
    ("DDOG", "Datadog", "Datadog Inc.", "Technology", "NASDAQ"),
    ("NET", "Cloudflare", "Cloudflare Inc.", "Technology", "NYSE"),
    ("MDB", "MongoDB", "MongoDB Inc.", "Technology", "NASDAQ"),
    ("TEAM", "Atlassian", "Atlassian Corporation", "Technology", "NASDAQ"),
    ("ZM", "Zoom", "Zoom Video Communications", "Technology", "NASDAQ"),
    ("DOCU", "DocuSign", "DocuSign Inc.", "Technology", "NASDAQ"),
    ("TWLO", "Twilio", "Twilio Inc.", "Technology", "NYSE"),
    ("U", "Unity", "Unity Software", "Technology", "NYSE"),
    ("RBLX", "Roblox", "Roblox Corporation", "Technology", "NYSE"),

    # AI & Robotics
    ("AI", "C3.ai", "C3.ai Inc.", "Technology", "NYSE"),
    ("SMCI", "超微電腦", "Super Micro Computer", "Technology", "NASDAQ"),
    ("PATH", "UiPath", "UiPath Inc.", "Technology", "NYSE"),
    ("BBAI", "BigBear.ai", "BigBear.ai Holdings", "Technology", "NYSE"),

    # Finance
    ("JPM", "摩根大通", "JPMorgan Chase & Co.", "Financial Services", "NYSE"),
    ("BAC", "美國銀行", "Bank of America", "Financial Services", "NYSE"),
    ("WFC", "富國銀行", "Wells Fargo & Co.", "Financial Services", "NYSE"),
    ("GS", "高盛", "Goldman Sachs Group", "Financial Services", "NYSE"),
    ("MS", "摩根士丹利", "Morgan Stanley", "Financial Services", "NYSE"),
    ("C", "花旗集團", "Citigroup Inc.", "Financial Services", "NYSE"),
    ("AXP", "美國運通", "American Express", "Financial Services", "NYSE"),
    ("V", "Visa", "Visa Inc.", "Financial Services", "NYSE"),
    ("MA", "萬事達卡", "Mastercard Inc.", "Financial Services", "NYSE"),
    ("BRK.B", "波克夏B", "Berkshire Hathaway B", "Financial Services", "NYSE"),
    ("SCHW", "嘉信理財", "Charles Schwab", "Financial Services", "NYSE"),
    ("BLK", "貝萊德", "BlackRock Inc.", "Financial Services", "NYSE"),

    # Healthcare & Pharma
    ("JNJ", "嬌生", "Johnson & Johnson", "Healthcare", "NYSE"),
    ("UNH", "聯合健康", "UnitedHealth Group", "Healthcare", "NYSE"),
    ("PFE", "輝瑞", "Pfizer Inc.", "Healthcare", "NYSE"),
    ("ABBV", "艾伯維", "AbbVie Inc.", "Healthcare", "NYSE"),
    ("MRK", "默克", "Merck & Co.", "Healthcare", "NYSE"),
    ("LLY", "禮來", "Eli Lilly and Co.", "Healthcare", "NYSE"),
    ("TMO", "賽默飛", "Thermo Fisher Scientific", "Healthcare", "NYSE"),
    ("ABT", "亞培", "Abbott Laboratories", "Healthcare", "NYSE"),
    ("DHR", "丹納赫", "Danaher Corporation", "Healthcare", "NYSE"),
    ("BMY", "必治妥", "Bristol-Myers Squibb", "Healthcare", "NYSE"),
    ("AMGN", "安進", "Amgen Inc.", "Healthcare", "NASDAQ"),
    ("GILD", "吉利德", "Gilead Sciences", "Healthcare", "NASDAQ"),
    ("MRNA", "莫德納", "Moderna Inc.", "Healthcare", "NASDAQ"),
    ("REGN", "再生元", "Regeneron Pharmaceuticals", "Healthcare", "NASDAQ"),
    ("VRTX", "福泰製藥", "Vertex Pharmaceuticals", "Healthcare", "NASDAQ"),
    ("ISRG", "直覺外科", "Intuitive Surgical", "Healthcare", "NASDAQ"),
    ("NVO", "諾和諾德", "Novo Nordisk", "Healthcare", "NYSE"),

    # Consumer
    ("WMT", "沃爾瑪", "Walmart Inc.", "Consumer Defensive", "NYSE"),
    ("COST", "好市多", "Costco Wholesale", "Consumer Defensive", "NASDAQ"),
    ("PG", "寶僑", "Procter & Gamble", "Consumer Defensive", "NYSE"),
    ("KO", "可口可樂", "Coca-Cola Co.", "Consumer Defensive", "NYSE"),
    ("PEP", "百事可樂", "PepsiCo Inc.", "Consumer Defensive", "NASDAQ"),
    ("MCD", "麥當勞", "McDonald's Corporation", "Consumer Cyclical", "NYSE"),
    ("SBUX", "星巴克", "Starbucks Corporation", "Consumer Cyclical", "NASDAQ"),
    ("NKE", "耐吉", "Nike Inc.", "Consumer Cyclical", "NYSE"),
    ("HD", "家得寶", "Home Depot", "Consumer Cyclical", "NYSE"),
    ("LOW", "勞氏", "Lowe's Companies", "Consumer Cyclical", "NYSE"),
    ("TGT", "塔吉特", "Target Corporation", "Consumer Defensive", "NYSE"),
    ("DIS", "迪士尼", "Walt Disney Co.", "Communication Services", "NYSE"),
    ("CMCSA", "康卡斯特", "Comcast Corporation", "Communication Services", "NASDAQ"),
    ("T", "AT&T", "AT&T Inc.", "Communication Services", "NYSE"),
    ("VZ", "威瑞森", "Verizon Communications", "Communication Services", "NYSE"),
    ("TMUS", "T-Mobile", "T-Mobile US", "Communication Services", "NASDAQ"),

    # Industrial
    ("BA", "波音", "Boeing Co.", "Industrials", "NYSE"),
    ("CAT", "開拓重工", "Caterpillar Inc.", "Industrials", "NYSE"),
    ("DE", "乾傑", "Deere & Company", "Industrials", "NYSE"),
    ("GE", "奇異", "General Electric", "Industrials", "NYSE"),
    ("HON", "漢威聯合", "Honeywell International", "Industrials", "NYSE"),
    ("UPS", "聯合包裹", "United Parcel Service", "Industrials", "NYSE"),
    ("RTX", "雷神", "RTX Corporation", "Industrials", "NYSE"),
    ("LMT", "洛克希德馬丁", "Lockheed Martin", "Industrials", "NYSE"),
    ("NOC", "諾斯洛普", "Northrop Grumman", "Industrials", "NYSE"),

    # Energy
    ("XOM", "艾克森美孚", "Exxon Mobil Corporation", "Energy", "NYSE"),
    ("CVX", "雪佛龍", "Chevron Corporation", "Energy", "NYSE"),
    ("COP", "康菲石油", "ConocoPhillips", "Energy", "NYSE"),
    ("SLB", "斯倫貝謝", "Schlumberger Limited", "Energy", "NYSE"),
    ("OXY", "西方石油", "Occidental Petroleum", "Energy", "NYSE"),

    # Electric Vehicles & Clean Energy
    ("RIVN", "Rivian", "Rivian Automotive", "Consumer Cyclical", "NASDAQ"),
    ("LCID", "Lucid", "Lucid Group", "Consumer Cyclical", "NASDAQ"),
    ("NIO", "蔚來", "NIO Inc.", "Consumer Cyclical", "NYSE"),
    ("XPEV", "小鵬", "XPeng Inc.", "Consumer Cyclical", "NYSE"),
    ("LI", "理想", "Li Auto Inc.", "Consumer Cyclical", "NASDAQ"),
    ("F", "福特", "Ford Motor Company", "Consumer Cyclical", "NYSE"),
    ("GM", "通用汽車", "General Motors", "Consumer Cyclical", "NYSE"),
    ("ENPH", "Enphase", "Enphase Energy", "Technology", "NASDAQ"),
    ("SEDG", "SolarEdge", "SolarEdge Technologies", "Technology", "NASDAQ"),
    ("FSLR", "第一太陽能", "First Solar", "Technology", "NASDAQ"),
    ("PLUG", "普拉格能源", "Plug Power", "Industrials", "NASDAQ"),

    # China Tech ADRs
    ("BABA", "阿里巴巴", "Alibaba Group", "Consumer Cyclical", "NYSE"),
    ("JD", "京東", "JD.com Inc.", "Consumer Cyclical", "NASDAQ"),
    ("PDD", "拼多多", "PDD Holdings", "Consumer Cyclical", "NASDAQ"),
    ("BIDU", "百度", "Baidu Inc.", "Communication Services", "NASDAQ"),
    ("NTES", "網易", "NetEase Inc.", "Communication Services", "NASDAQ"),
    ("BILI", "嗶哩嗶哩", "Bilibili Inc.", "Communication Services", "NASDAQ"),
    ("TCEHY", "騰訊", "Tencent Holdings ADR", "Communication Services", "OTC"),

    # ETFs
    ("SPY", "SPDR S&P 500", "SPDR S&P 500 ETF", "ETF", "NYSE"),
    ("QQQ", "納指100 ETF", "Invesco QQQ Trust", "ETF", "NASDAQ"),
    ("IWM", "羅素2000 ETF", "iShares Russell 2000 ETF", "ETF", "NYSE"),
    ("DIA", "道瓊ETF", "SPDR Dow Jones Industrial", "ETF", "NYSE"),
    ("VOO", "Vanguard S&P 500", "Vanguard S&P 500 ETF", "ETF", "NYSE"),
    ("VTI", "Vanguard全市場", "Vanguard Total Stock Market", "ETF", "NYSE"),
    ("ARKK", "ARK創新ETF", "ARK Innovation ETF", "ETF", "NYSE"),
    ("SOXX", "半導體ETF", "iShares Semiconductor ETF", "ETF", "NASDAQ"),
    ("XLF", "金融ETF", "Financial Select Sector SPDR", "ETF", "NYSE"),
    ("XLE", "能源ETF", "Energy Select Sector SPDR", "ETF", "NYSE"),
    ("XLK", "科技ETF", "Technology Select Sector SPDR", "ETF", "NYSE"),
    ("XLV", "醫療ETF", "Health Care Select Sector SPDR", "ETF", "NYSE"),
    ("SOXL", "半導體3倍做多", "Direxion Semiconductor Bull 3X", "ETF", "NYSE"),
    ("SOXS", "半導體3倍做空", "Direxion Semiconductor Bear 3X", "ETF", "NYSE"),
    ("TQQQ", "納指3倍做多", "ProShares UltraPro QQQ", "ETF", "NASDAQ"),
    ("SQQQ", "納指3倍做空", "ProShares UltraPro Short QQQ", "ETF", "NASDAQ"),
]


def seed_stocks():
    """Seed the database with stocks"""
    db = SessionLocal()

    try:
        count = 0

        # Add Taiwan TWSE stocks
        for stock_id, name, english_name, industry, market in TAIWAN_TWSE_STOCKS:
            stock = Stock(
                stock_id=stock_id,
                name=name,
                english_name=english_name,
                industry=industry,
                market=market,
                market_region='TW'
            )
            db.merge(stock)
            count += 1

        # Add Taiwan TPEx stocks
        for stock_id, name, english_name, industry, market in TAIWAN_TPEX_STOCKS:
            stock = Stock(
                stock_id=stock_id,
                name=name,
                english_name=english_name,
                industry=industry,
                market=market,
                market_region='TW'
            )
            db.merge(stock)
            count += 1

        # Add US stocks
        for stock_id, name, english_name, sector, market in US_STOCKS:
            stock = Stock(
                stock_id=stock_id,
                name=name,
                english_name=english_name,
                sector=sector,
                market=market,
                market_region='US'
            )
            db.merge(stock)
            count += 1

        db.commit()
        logger.info(f"Stock seeding completed!")
        logger.info(f"   - Processed: {count} stocks")
        logger.info(f"   - Taiwan stocks (TWSE): {len(TAIWAN_TWSE_STOCKS)}")
        logger.info(f"   - Taiwan stocks (TPEx): {len(TAIWAN_TPEX_STOCKS)}")
        logger.info(f"   - US stocks: {len(US_STOCKS)}")

    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding stocks: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_stocks()
