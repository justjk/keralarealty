import scrapy


class KrsearchbotSpider(scrapy.Spider):
    name = 'krsearchbot'
    allowed_domains = ['keralarealty.in/properties/search']
    start_urls = ['http://keralarealty.in/properties/search/']

    def parse(self, response):
        pass
