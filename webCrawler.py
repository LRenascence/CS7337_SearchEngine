import requests
import re
from bs4 import BeautifulSoup
import hashlib
import string
from nltk.stem import PorterStemmer
from http import HTTPStatus
from prettytable import PrettyTable

class WebCrawler:
    def __init__(self, startURL, N):
        self.startURL = startURL
        self.toDoURL = [self.startURL]
        self.visitedURL = set()
        self.domain = ""
        self.URLTitle = {}
        self.crawledURL = set()
        self.brokenURL = set()
        self.docIDWords = {}
        self.robotsRule = []
        self.outOfURL = set()
        self.duplicateURL = set()
        self.invalidURL = set()
        self.nonTextURL = set()
        self.limit = N
        self.allWords = set()
        self.frequencyMatrix = []
        self.topN = 0
        self.topNWordsDict = {}

    def getDomain(self):
        domain = self.startURL.replace("index.htm", "")
        self.domain = domain

    def setup(self):
        self.getDomain()
        self.getRobotsRule()

    def crawl(self):
        pageCount = 0
        stemmer = PorterStemmer()
        # crawl the website until there is no page to crawl or reach the number of limitation
        while pageCount < self.limit and self.toDoURL:
            curURL = self.toDoURL.pop(0)     
            # open the URL
            try:
                url = requests.get(curURL)
            # catch the broken URL and do next loop
            except requests.exceptions.RequestException as e:
                self.brokenURL.add(curURL)
                continue
            # check 404 error
            if url.status_code == HTTPStatus.NOT_FOUND:
                self.brokenURL.add(curURL)
                continue
            # successfully open the URL, pageCount + 1
            pageCount += 1
            pagetext = url.text
            soup = BeautifulSoup(pagetext, "html.parser")
            # mark the URL visited
            self.visitedURL.add(curURL)
            # if have "noindex", skip
            meta = soup.find("meta", attrs={"name": "robots"})
            if meta and "noindex" in meta["content"].lower():
                self.invalidURL.add(curURL)
                continue
            # get the title, if there is no title, use the URL
            curTitle = soup.title.string if soup.title is not None else ""
            curTitle = curTitle.lower()
            # generate unique docID with hash using content text
            curDocID = hashlib.sha256(soup.text.encode("utf-8")).hexdigest()
            # check if is a duplicate page, if so, skip
            if self.isDuplicate(curDocID):
                self.duplicateURL.add(curURL)
                continue
            # store the map URL - (title, docID)
            self.URLTitle[curURL] = (curTitle, curDocID)

            # new version
            curDomain = re.split('/', curURL)
            curDomain = curDomain[:-1]
            curDomain = "/".join(curDomain)
            # if this is a text file, need to crawl the words and links
            if any(curURL.endswith(suffix) for suffix in ['/', 'html', 'txt', 'htm', 'php']):
                # add this URL to self.crawledURL
                self.crawledURL.add(curURL)
                # get the context text
                content = soup.text
                # remove the punctuation
                content = [content]
                content = ''.join(w for w in content[0] if w not in string.punctuation)
                # split content into words
                words = content.split()
                # store the valid word into self.docIDWords
                self.docIDWords[curDocID] = []
                for word in words:
                    word = word.lower()
                    word = self.validWord(word)
                    # stemming the word
                    word = stemmer.stem(word)
                    if word:
                        self.docIDWords[curDocID].append(word)
                
                # crawl the links
                for link in soup.find_all('a'):
                    newURL = link.get('href')
                    # check if is is valid(still in domain, under Robots.txt rule)
                    if any(newURL.startswith(prefix) for prefix in self.robotsRule):
                        self.invalidURL.add(self.domain + newURL)
                        continue
                    if newURL.startswith("http"):
                        self.outOfURL.add(newURL)
                        continue
                    

                    newURL = curDomain + "/" + newURL
                    #print(newURL)
                    if newURL not in self.visitedURL:
                        # append the newURL into self.toDoURL
                        self.toDoURL.append(newURL)
                    """
                    # old version
                    # if current URL is "https://s2.smu.edu/~fmoore/textfiles/index.html"
                    # we need a new domain, " https://s2.smu.edu/~fmoore/textfiles/"
                    # for these test files
                    if curURL == "https://s2.smu.edu/~fmoore/textfiles/index.html":
                        newURL = "https://s2.smu.edu/~fmoore/textfiles/" + newURL
                    # if not, use normal domain
                    else:
                        newURL = self.domain + newURL
                    # do not crawl visited URL
                    if newURL not in self.visitedURL:
                        # append the newURL into self.toDoURL
                        self.toDoURL.append(newURL)
                    """
            else:
                self.nonTextURL.add(curURL)
                
    def validWord(self, word):
        # return a valid word or empty string
        # start with a-z
        while word and word[0] not in string.ascii_lowercase:
            word = word[1:]
        return word

    def getRobotsRule(self):
        curURL = self.domain + "robots.txt"    
        # open the URL
        try:
            url = requests.get(curURL)
        # catch the broken URL and do next loop
        except requests.exceptions.RequestException as e:
            print("No robots file")
            return 
        pagetext = url.text
        soup = BeautifulSoup(pagetext, "html.parser")
        text = soup.text
        self.robotsRule = re.findall("Disallow: /(.*)/", text)
         
    def isDuplicate(self, hashkey):
        return True if hashkey in self.docIDWords.keys() else False
    
    def buildTFMatrix(self):
        # get all unique stemming words
        for doc in self.docIDWords:
            for word in self.docIDWords[doc]:
                self.allWords.add(word)
        self.crawledURL = list(self.crawledURL)
        self.allWords = list(self.allWords)
        self.allWords.sort()
        # build frequency matrix
        self.frequencyMatrix = [[] for i in self.allWords]
        for word in range(len(self.allWords)):
            wordFreCount = []
            for url in self.crawledURL:
                wordList = self.docIDWords[self.URLTitle[url][1]]
                wordFreCount.append(wordList.count(self.allWords[word]))
            """
            # old version
            for wordList in self.docIDWords.values():
                wordFreCount.append(wordList.count(self.allWords[word]))
            """
            self.frequencyMatrix[word] = wordFreCount

    def printTFMatrix(self):
        outputTFMatrix = ","
        # print first row
        for doc in range(len(self.docIDWords.keys())):
            outputTFMatrix += "Doc" + str(doc) + ","
        outputTFMatrix += "\n"
        # print frequency
        for word in range(len(self.frequencyMatrix)):
            outputTFMatrix += self.allWords[word] + "," + ",".join([str(frequency) for frequency in self.frequencyMatrix[word]]) + "\n"

        f = open("tf_matrix.csv", "wt")
        f.write(outputTFMatrix)
        f.close()

    def topNWords(self, topN):
        wordFre = {}
        self.topN = topN
        # get all  words frequency and doc frequency
        for word in range(len(self.allWords)):
            totalFrequency = sum(self.frequencyMatrix[word])
            docFrequency = sum([1 for x in self.frequencyMatrix[word] if x > 0])
            wordFre[self.allWords[word]] = (totalFrequency, docFrequency)
        # sort by words frequency and pick top N
        wordCount = 0
        for key, value in sorted(wordFre.items(), key=lambda e: e[1][0], reverse=True):
            if wordCount >= topN:
                break
            self.topNWordsDict[key] = value
            wordCount += 1

    def printInfo(self):
        f = open("result.txt", "wt")
        f.write("Domain URL: " + self.domain + "\n")
        f.write("Total number of words: " + str(len(self.allWords)) + "\n")
        f.write("-------------------------\n")
        f.write("Crawled URL: \n")
        for i in self.crawledURL:
            f.write(str(i) + "\n")
        f.write("-------------------------\n")
        f.write("Duplicate URL: \n")
        for i in self.duplicateURL:
            f.write(str(i) + "\n")
        f.write("-------------------------\n")
        f.write("Broken URL: \n")
        for i in self.brokenURL:
            f.write(str(i) + "\n")
        f.write("-------------------------\n")
        f.write("Out of domain URL: \n")
        for i in self.outOfURL:
            f.write(str(i) + "\n")
        f.write("-------------------------\n")
        f.write("Invalid URL: \n")
        for i in self.invalidURL:
            f.write(str(i) + "\n")
        f.write("-------------------------\n")
        f.write("Non text URL: \n")
        for i in self.nonTextURL:
            f.write(str(i) + "\n")
        f.write("-------------------------\n")
        f.write("URL and Title:\n")
        x = PrettyTable()
        x.field_names = ["URL", "Title",]
        for i in self.URLTitle:
            x.add_row([str(i), str(self.URLTitle[i][0])])
        f.write(str(x) + "\n")
        f.write("-------------------------\n")
        f.write("top " + str(self.topN) + " words:\n")
        x = PrettyTable()
        x.field_names = ["Word", "Frequency", "Document frequency"]
        for i in self.topNWordsDict:
            x.add_row([str(i), str(self.topNWordsDict[i][0]), str(self.topNWordsDict[i][1])])
        f.write(str(x))

        f.close()
