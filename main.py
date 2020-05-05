import sys
from webCrawler import WebCrawler
from searchEngine import SearchEngine

def main():
    print("Start crawling, please wait")
    crawler = WebCrawler("https://s2.smu.edu/~fmoore/index.htm", 200)
    crawler.setup()
    crawler.crawl()
    crawler.buildTFMatrix()
    crawler.printTFMatrix()
    crawler.topNWords(20)
    crawler.printInfo()
    
    print("Crawling completed, results are save to result.txt and tf_matrix.csv")
    print("Starting query search")

    engine = SearchEngine(crawler)
    engine.loadThesaurus("thesaurus.csv")
    while True:
        query = input("Please input query or stop to terminate query search:")
        # convert to lower case
        query = query.lower()
        if query == "stop":
            print("Thanks for using!")
            break
        engine.engine(query)
        print("Done")
        print('+++++++++++++++++++++++++++++++++++++++++')
    


if __name__ == "__main__":
    main()