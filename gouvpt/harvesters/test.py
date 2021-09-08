# -*- coding: utf-8 -*-
import requests
from datetime import datetime

url = "https://snig.dgterritorio.gov.pt/rndg/srv/por/q?_content_type=json&fast=index&from=1&resultType=details&sortBy=referenceDateOrd&type=dataset%2Bor%2Bseries&dataPolicy=Dados%20abertos&keyword=DGT"
headers = {'content-type': 'application/json', 'Accept-Charset': 'utf-8'}
res = requests.get(url, headers=headers)
res.encoding = 'utf-8'
metadata = res.json().get("metadata")

for each in metadata[:]:
    #print(each)
    item = {
        "remote_id": each.get("geonet:info", {}).get("uuid"),
        "title": each.get("defaultTitle"),
        "description": each.get("defaultAbstract"),
        "resources": each.get("link"),
        "keywords": each.get("keyword")
    }
    if each.get("publicationDate"):
        item["date"] = datetime.strptime(each.get("publicationDate"), "%Y-%m-%d")

    links = []
    resources = item.get("resources")
    if isinstance(resources, list):
        for url in resources:
            url_parts = url.split('|')
            inner_link = {}
            inner_link['url'] = url_parts[2]
            inner_link['type'] = url_parts[3]
            inner_link['format'] = url_parts[4]
            links.append(inner_link)

    elif isinstance(resources, unicode):
        url_parts = resources.split('|')
        inner_link = {}
        inner_link['url'] = url_parts[2]
        inner_link['type'] = url_parts[3]
        inner_link['format'] = url_parts[4]
        links.append(inner_link)

    item['resources'] = links

    print(item["remote_id"], item['title'])