import scrapy
import re

"""
Basic Devanagari: \u0900 to \u097F
Vedic Extensions: \u1CD0 to \u1CFF
Extended Devanagari: \uA8E0 to \uA8FF
"""

hindi_pattern = r"[\u0900-\u097F\u1CD0-\u1CFF\uA8E0-\uA8FF]+"  # Devanagari + Vedic + Extended Devanagari Unicode blocks
compiled = re.compile(pattern=hindi_pattern, flags=re.IGNORECASE)


class HindiSpider(scrapy.Spider):
    name = 'HindiSpider'
    start_urls = [
        # 'https://hi.wikipedia.org/wiki/%E0%A4%AE%E0%A5%81%E0%A4%96%E0%A4%AA%E0%A5%83%E0%A4%B7%E0%A5%8D%E0%A4%A0',
        # 'https://hi.wikipedia.org/wiki/%E0%A4%B6%E0%A5%8D%E0%A4%B0%E0%A5%87%E0%A4%A3%E0%A5%80:%E0%A4%87%E0%A4%A4%E0%A4%BF%E0%A4%B9%E0%A4%BE%E0%A4%B8',
        'https://www.aajtak.in/',
        'https://www.amarujala.com/?src=mainmenu',
        'https://ndtv.in/',
        'https://ndtv.in/cricket/zim-vs-ind-2nd-t20i-abhishek-sharma-bat-s-10minute-tsunami-thats-how-zimbabwe-was-robbed-in-two-parts-hindi-6054491#pfrom=home-khabar_moretop'
        'https://storymirror.com/read/hindi/story/%E0%A4%86%E0%A4%B0%E0%A5%8D%E0%A4%9F%E0%A4%BF%E0%A4%95%E0%A4%B2/tag',
        'https://www.achhikhabar.com/hindi-stories/',
        'https://hindi.webdunia.com/kids-stories/story-done-compare-yourself-with-others-118060900051_1.html',
        'https://www.sarita.in/story/social-story',
        'https://www.bhaskar.com/',
        'https://www.indiatv.in/',
        'https://www.livehindustan.com/uttar-pradesh/news',
        'https://www.jagran.com/'

        ]

    def parse(self, response):
        # Extract text from <p> tags
        for paragraph in response.css('p'):
            txt = re.findall(compiled, paragraph.get())
            if len(txt) > 2:
                yield {
                    'text': " ".join(txt)
                }

        # Follow links to other pages
        for href in response.css('a::attr(href)'):
            url = response.urljoin(href.extract())
            yield scrapy.Request(url, callback=self.parse)
