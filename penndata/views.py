import requests
from bs4 import BeautifulSoup
from requests.exceptions import ConnectionError
from rest_framework.response import Response
from rest_framework.views import APIView


NEWS_URL = "https://www.thedp.com/"


class News(APIView):
    def get_article(self):
        try:
            resp = requests.get(NEWS_URL)
        except ConnectionError:
            return None

        article = {}

        html = resp.content.decode("utf8")

        soup = BeautifulSoup(html, "html5lib")

        frontpage = soup.find("div", {"class": "col-lg-6 col-md-5 col-sm-12 frontpage-carousel"})

        # adds all variables for news object
        if frontpage:
            title_html = frontpage.find("a", {"class": "frontpage-link large-link"})
        if title_html:
            article["link"] = title_html["href"]
            article["title"] = title_html.get_text()

        subtitle_html = frontpage.find("p")
        if subtitle_html:
            article["subtitle"] = subtitle_html.get_text()

        timestamp_html = frontpage.find("div", {"class": "timestamp"})
        if timestamp_html:
            article["timestamp"] = timestamp_html.get_text()

        image_html = frontpage.find("img")
        if image_html:
            article["imageurl"] = image_html["src"]

        # checks if all variables are there
        if all(v in article for v in ["title", "subtitle", "timestamp", "imageurl", "link"]):
            return article
        else:
            return None

    def get(self, request):
        article = self.get_article()
        if article:
            return Response({"article": article})
        else:
            return Response({"error": "Site could not be reached or could not be parsed."})
