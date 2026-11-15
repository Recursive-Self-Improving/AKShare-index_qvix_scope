"""Date-level official identities; Sina reconstruction method remains unknown."""
_CSI = "https://oss-ch.csindex.com.cn/static/html/csindex/public/uploads/indices/detail/files/zh_CN/"
IDENTITIES = {
    "sh000001": {"official_name": "上证综合指数", "base_date": "1990-12-19", "release_date": "1991-07-15",
                 "citation": _CSI + "000001factsheet.pdf"},
    "sh000016": {"official_name": "上证50指数", "base_date": "2003-12-31", "release_date": "2004-01-02",
                 "citation": _CSI + "000016factsheet.pdf"},
    "sh000300": {"official_name": "沪深300指数", "base_date": "2004-12-31", "release_date": "2005-04-08",
                 "citation": _CSI + "000300factsheet.pdf"},
    "sz399006": {"official_name": "创业板指数P", "base_date": "2010-05-31", "release_date": "2010-06-01",
                 "citation": "https://www.szse.cn/disclosure/notice/general/t20100531_500454.html"},
    "sz399673": {"official_name": "创业板50指数", "base_date": "2010-05-31", "release_date": "2014-06-18",
                 "citation": "https://www.szse.cn/www/disclosure/notice/general/t20140617_501247.html"},
    "sh000680": {"official_name": "上证科创板综合指数", "base_date": "2019-12-31", "release_date": "2025-01-20",
                 "citation": _CSI + "000680factsheet.pdf", "return_note": "包括股息，与科创50价格指数不同"},
    "sh000688": {"official_name": "上证科创板50成份指数", "base_date": "2019-12-31", "release_date": "2020-07-23",
                 "citation": _CSI + "000688factsheet.pdf"},
}
