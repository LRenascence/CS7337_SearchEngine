import csv
import math
from webCrawler import WebCrawler
from nltk.stem import PorterStemmer


class SearchEngine():
    # import web crawler
    def __init__(self, webCrawler):
        self.webCrawler = webCrawler
        self.thesaurus = {}
        # number of documents
        self.N = len(self.webCrawler.docIDWords)
        self.df = [sum(row) for row in self.webCrawler.frequencyMatrix]

    # implement thesaurus expansion 
    def loadThesaurus(self, thesaurusFile):
        thesaurus = {}
        try:
            with open(thesaurusFile) as csvFile:
                reader = csv.reader(csvFile, delimiter=',')
                for row in reader:
                    word = row[0]
                    alternatives = row[1:]
                    thesaurus[word] = alternatives
            self.thesaurus = thesaurus
            print("load thesaurus file complete")
        except:
            print("Error opening " + thesaurusFile)
    
    # log weighted tf-idf weight of a document or query
    def tf_idf(self, doc):
        w = []

        for d in range(len(doc)):
            if doc[d] > 0:
                w.append((1 + math.log10(doc[d])) * math.log10(self.N / self.df[d]))
            else:
                w.append(0)

        return w

    # normalized list
    def normalize_list(self, input_list):
        # compute the square root of the sum of squares in the list (norm of list)
        l_norm = math.sqrt(sum([l**2 for l in input_list]))

        # normalize list by dividing each element by the norm of list
        if l_norm > 0:
            input_list = [l/l_norm for l in input_list]
        return input_list


    # inplement cosine similarity
    def cosineSimilarity(self, query, doc):
        # compute tf-idf for query and doc
        q_prime = self.tf_idf(query)
        d_prime = self.tf_idf(doc)

        # normalize query and doc
        q_prime = self.normalize_list(q_prime)
        d_prime = self.normalize_list(d_prime)


        # return dot product
        return sum([q_prime[i] * d_prime[i] for i in range(len(q_prime))])

    # implement search engine
    def engine(self, query, k = 5):
        self.webCrawler.crawledURL = list(self.webCrawler.crawledURL)
        # valid query
        # if has invalid word, convert it into valid word
        for word in query.split():
            word = self.webCrawler.validWord(word)

        # init scores
        scores = {}
        for url in self.webCrawler.crawledURL:
            scores[url] = 0
        
        queryWords = query.split()
        # thesaurus expansion
        for word in queryWords:
            if word in self.thesaurus:
                for newWord in self.thesaurus[word]:
                    queryWords.append(newWord)
        
        # if any of the query words appear in the <title> of a document, add 0.1 to its score
        for word in queryWords:
            for url in self.webCrawler.crawledURL:
                if word in self.webCrawler.URLTitle[url][0]:
                    scores[url] += 0.1
        # stem terms in query
        stemmer = PorterStemmer()
        queryWords = [stemmer.stem(q) for q in queryWords]
        # remove words that not in any document
        queryWords = [q for q in queryWords if q in self.webCrawler.allWords]
        print("query is convert into: " + str(queryWords))
        # convert query to list of term frequencies
        queryWords = [queryWords.count(word) for word in self.webCrawler.allWords]
        # get doc-wordFrequency matrix
        docs = [list(x) for x in zip(*self.webCrawler.frequencyMatrix)]
        # run cosine similarity
        for i, (url, score) in enumerate(scores.items()):
            scores[url] += self.cosineSimilarity(queryWords, docs[i])

        # sort by scores in descending order
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        results = [['%06.4f' % score, url, self.webCrawler.URLTitle[url][0],
                    " ".join(self.webCrawler.docIDWords[self.webCrawler.URLTitle[url][1]][:20])]
                     for url, score in sorted_scores if score > 0]
        # print top K results
        self.printResult(results, k)
    
    def printResult(self, results, k):
        # print top K result
        # if no enough results, just print all results
        # if no result, print important webpage
        if results:
            count = 1
            while results and k:
                curResult = results.pop(0)
                print("Result " + str(count))
                print("Score: " + str(curResult[0]))
                print("URL: " + str(curResult[1]))
                if str(curResult[2]) != "":
                    print("Title: " + str(curResult[2]))
                else:
                    print("Title: no title")
                print("First 20 words: " + str(curResult[3]))
                print('-----------------------------')
                k -= 1
                count += 1
        else:
            print("Sorry! Can not find any relative webpage")
            print("Will return some main pages")
            print("---------------------------")
            print("Result 1")
            url = "https://s2.smu.edu/~fmoore/index.htm"
            print("URL: " + str(url))
            print("Title: " + str(self.webCrawler.URLTitle[url][0]))
            print("---------------------------")
            print("Result 2")
            url = "https://s2.smu.edu/~fmoore/schedule.htm"
            print("URL: " + str(url))
            print("Title: " + str(self.webCrawler.URLTitle[url][0]))
            print("---------------------------")
            print("Result 3")
            url = "https://s2.smu.edu/~fmoore/textfiles/index.html"
            print("URL: " + str(url))
            print("Title: " + str(self.webCrawler.URLTitle[url][0]))
            print("---------------------------")
            print("Result 4")
            url = "https://s2.smu.edu/~fmoore/textfiles/extratextfiles/index.php"
            print("URL: " + str(url))
            print("Title: " + str(self.webCrawler.URLTitle[url][0]))