import urllib
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


import scrapy

import lxml.etree as ET

class KrsearchbotSpider(scrapy.Spider):
    name = 'krsearchbot'
    allowed_domains = ['keralarealty.in']
    base_url = 'http://keralarealty.in/properties/search/'

    category_dict = {
        "house": 1,
        "villa": 1,
        "flat": 2,
        "apartment": 2,
        "office": 3,
        "comm_plot": 4,
        "comm_build": 5,
        "hotel": 6,
        "godown": 7,
        "plot": 8
    }

    def __init__(self, category="house", property_for="Sale", district="ERN",
                 *args, **kwargs):
        super(KrsearchbotSpider, self).__init__(*args, **kwargs)
        self.category_id = self.category_dict.get(category, "1")
        self.property_for = property_for
        self.district = district
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:86.0) Gecko/20100101 Firefox/86.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        }

    def start_requests(self):
        query_params = {
            "search[district]": self.district,
            "search[property_for]": self.property_for,
            "search[category_id]": self.category_id,
            "page": 1
        }
        search_url = self.base_url + "?" + urlencode(query_params)
        yield scrapy.Request(search_url)

    def parse(self, response):
        listing_urls = response.xpath("//div[@class='listing_grid']/div/div/a/@href").extract()
        next_url = response.xpath("//div[@class='pagination']/a[@class='next']/@href").get()

        for url in listing_urls:
            yield scrapy.Request(url, headers=self.headers, callback=self.parse_listing)

        if next_url:
            next_page_url = self.get_next_page_url(response.url, next_url)
            yield scrapy.Request(next_page_url, callback=self.parse)

    def parse_listing(self, response):
        property_detail_top = response.xpath("//section[@class='property-detail-top']")
        heading = property_detail_top.xpath("//h1/text()").get()
        price = property_detail_top.xpath("//div[@class='property-meta']/span[@class='prop-price']/text()").get()
        num_bed = property_detail_top.xpath("//li[@class='beds-numb']/span/span/text()").get()
        num_bath = property_detail_top.xpath("//li[@class='bath-numb']/span/span/text()").get()

        details = {
            'heading': heading,
            'price': price,
            'bedrooms': num_bed,
            'bathrooms': num_bath
        }

        features_table_rows = response.xpath("//div[@class='features_table']/div").getall()

        for row in features_table_rows:
            parser = ET.XMLParser(recover=True)
            row_xml = ET.ElementTree(ET.fromstring(row, parser=parser))
            key = row_xml.find(".//div[@class='left']").text.rstrip(":")
            val = row_xml.find(".//div[@class='right']").text
            details.update({key: val})

        description = response.xpath("//div[@class='property-detail-desc body-detail description']/p/text()").get()
        details.update({"description": description})
        details.update({"url": response.url})
        yield details

    def get_next_page_url(self, current_url, next_url):
        parsed_next = urlparse(next_url)
        next_page_num = parse_qs(parsed_next.query)['page'][0]

        parsed_current = urlparse(current_url)
        params = dict(parse_qs(parsed_current.query))
        params = {k: v[0] for k, v in params.items()}

        params['page'] = next_page_num
        new_query = urlencode(params)
        parsed_current = parsed_current._replace(query=new_query)
        return urlunparse(parsed_current)
