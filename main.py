import sys
from webCrawler import WebCrawler

def main():
    crawler = WebCrawler("https://s2.smu.edu/~fmoore/index.htm", 100)
    crawler.setup()
    crawler.crawl()
    crawler.buildTFMatrix()
    crawler.printTFMatrix()
    crawler.topNWords(20)
    crawler.printInfo()


if __name__ == "__main__":
    main()