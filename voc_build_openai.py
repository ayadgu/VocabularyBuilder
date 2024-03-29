import re
import mobi
import html2text
import nltk
import pycountry
import os 
import PyPDF2
import json
import argparse
import ebooklib

from urllib.request import urlopen
from bs4 import BeautifulSoup
from ebooklib import epub
from collections import Counter
from langdetect import detect

from nltk.tokenize import word_tokenize, RegexpTokenizer
from nltk.corpus import wordnet, stopwords, words
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet as wn
wnl = WordNetLemmatizer()

nltk.download("stopwords", quiet=True, raise_on_error=True)
nltk.download("wordnet", quiet=True, raise_on_error=True)
nltk.download("words", quiet=True, raise_on_error=True)

class BookVocabularyExtractor:
    def __init__(self, data):
        parser = argparse.ArgumentParser(description="Find uncommon words in a document.")
        parser.add_argument('-s', '--source', required=True, help="File path or URL of the document")
        args = parser.parse_args()

        # """Parameter initialization"""
        self.file_path = args.source
        self.directory_path = args.source.split(".")[0]

        self.known_words_path=data['known_words_path']
        self.known_names_path=data['known_names_path']

        with open(f"Input/{self.known_words_path}", encoding="utf8") as f:
            self.known_words = f.read().splitlines()

        with open(f"Input/{self.known_names_path}", encoding="utf8") as f:
            self.known_names = f.read().splitlines()

        print("file_path",self.file_path)
        print("directory_path",self.directory_path)


    def gettextfrompdf(self):
        # Open the PDF file
        pdf_file = open(file, "rb")

        # Create a PDF reader object
        pdf_reader = PyPDF2.PdfReader(pdf_file)

        # Get the number of pages in the PDF file
        num_pages = len(pdf_reader.pages)
        words = []
        # Loop through each page and extract the text
        for page in range(num_pages):
            # Get the page object
            pdf_page = pdf_reader.pages[page]

            # Extract the text from the page
            page_text = pdf_page.extract_text().lower()

            # Split the text into words
            words += page_text.split()

        # Close the PDF file

        pdf_file.close()
        text = " ".join(words)
        return text

    def read_epub(self):
        print(self.file_path)
        book = epub.read_epub(self.file_path)
        content = ""

        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            content += item.get_content().decode('utf-8', 'ignore') + "\n"

        return content

    def get_words_from_file(self):
        print("-----\n")
        print(self.file_path.startswith('http'))
        print(self.file_path.endswith('.pdf'))
        print(self.file_path.endswith('.mobi'))
        print(self.file_path.endswith('.epub'))
        print(self.file_path.endswith('.txt'))

        if self.file_path.startswith('http'):
            # If the input is a URL
            html = urlopen(self.file_path).read()
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text()

        elif self.file_path.endswith('.pdf'):
            text = self.gettextfrompdf()

        elif self.file_path.endswith('.mobi'):
            text = self.mobi_library_function()

        elif self.file_path.endswith('.epub'):
            text = self.read_epub()
            pass

        elif self.file_path.endswith('.txt'):
            with open(self.file_path, 'r', encoding='utf-8') as txt_file:
                text = txt_file.read()

        else:
            raise ValueError("Unsupported file format")

        # Extract words from the text
        # words = re.findall(r'\b\w+\b', text.lower())
        text = text.lower().replace(".", "").replace("--", "")
        words = []
        pattern = r'\b[a-zA-Z]+\b'
        words = re.findall(pattern, text)

        self.words=words
        self.text_du_livre=text
        return

    def mobi_library_function(self):
        tempdir, filepath = mobi.extract(self.file_path)
        file = open(filepath, encoding="utf8")
        content=file.read()
        words =  html2text.html2text(content)
        return words

    def find_uncommon_words(self,words,book_langage='english'):
        # Known Words to filter with
        with open(f"Input/{self.known_words_path}", encoding="utf8") as f:
            known_words = f.read().splitlines()
        
        # Known Names to filter with
        with open(f"Input/{self.known_names_path}", encoding="utf8") as f:
            known_names = f.read().splitlines()
        
        # Count the occurrences of each word
        word_counts = Counter(words)

        # Remove stopwords
        stop_words = set(stopwords.words(self.book_langage.name.lower()))

        filtered_words = [word for word, count in word_counts.items() 
                        if count == 1 and
                        word.isalpha() and
                        word not in stop_words and
                        word.lower() not in (self.known_words or self.known_names) and
                        len(word)>1 ]

        self.uncommon_words = filtered_words 
        # print(filtered_words)

    def create_markdown_document(self):
        markdown_content = f"# Uncommon Words and Meanings\n"
        # print(self.uncommon_words)
        for word in self.uncommon_words[:50]:
            word = wnl.lemmatize(word, "v")
            print(word)
            synsets = self.get_word_syn(word)

            markdown_individual = f""
            if len(synsets) == 0 or not isinstance(synsets, list) :
                # print(f"{word}, {synsets}")
                # or not isinstance(synsets, list)
                continue
            
            markdown_individual+=f"\n## {word.capitalize()}\n"
            for synset in synsets :
                markdown_individual+=f"{synset.definition().capitalize()}\n"
                if synset.examples() != 0 :
                    for example in synset.examples():
                        markdown_individual+=f"- {example}"
                    markdown_individual+=f"\n"
                # print(markdown_individual[:50])
                print(f"{self.directory_path}/Vocabulary/{word.capitalize()}.md")
                with open(f"{self.directory_path}/Vocabulary/{word.capitalize()}.md", "w", encoding="utf-8") as markdown_vocabulary:
                    markdown_vocabulary.write(markdown_individual)
            markdown_content+=f"{markdown_individual}"

        return markdown_content


    def get_word_syn(self,word):
        # Get the synsets (sets of synonyms) for the word from WordNet
        synsets = wordnet.synsets(word)

        if len(synsets) == 0:
            return [],[],[]    
        # Take the first synset as an example
        return synsets
        
    def gettext(self):
        
        text_file = open(self.file, "r")
        text = text_file.read().lower().replace(".", "").replace("--", "")
        
        pattern = r"[a-zA-Z\-\.'/]+"
        words = re.findall(pattern, text)
        
        text_file.close()
        return words


    def find_quotes(words_to_find, text):
        # print(words_to_find)
        # words_to_find = ["chien", "chat", "loup"]
        mot_pattern = "|".join(map(re.escape, words_to_find))
        # print(mot_pattern)
        
        citations_mots =[]

        # citations_mots = re.findall(fr'(.*?({mot_pattern})[\s|.].*?)', text)


        # print(len(citations_mots))
        for citation in citations_mots:
            print(citation[0])


        return
        for citation in text:
            print(citation)
        
        for word in words:
            # Create a regex pattern with the word
            pattern = re.compile(rf'{re.escape(word)}', re.IGNORECASE | re.DOTALL)
            print(pattern)
            # Find all matches in the text using the regex pattern
            matches = pattern.findall(text)
            print(matches)


            # Extract the quoted segments and add them to the quotes list
            quotes.extend(match[1] for match in matches)

        return quotes

    def get_text_language(self,words):
        text_language = detect(" ".join(words))
        # This is a safer way to extract the country code from something
        # like en-GB (thanks ivan_pozdeev)
        # lang_code = text_language[:text_language.index('-')] if '-' in text_language else text_language
        book_langage = pycountry.languages.get(alpha_2=text_language)
        self.book_langage = book_langage


    def create_directory(self):
        try: 
            os.makedirs(self.directory_path, exist_ok = True) 
            os.makedirs(self.directory_path+"/Vocabulary", exist_ok = True) 
            print("Directory '%s' created successfully" % self.directory_path) 
        except OSError as error: 
            print("Directory '%s' can not be created" % self.directory_path) 
        return 
    
    def save_markdown_document(self,markdown_content,word=f"_Glossaire"):
        print(word)
        # Save the content to a Markdown file
        with open(f"{self.directory_path}/{word}.md", "w", encoding="utf-8") as markdown_file:
            markdown_file.write(markdown_content)

    def main(self):
        
        self.create_directory()
        self.get_words_from_file()


        # Find uncommon_words
        self.text_du_livre=self.text_du_livre.replace('\n',"").replace('>','')
        text_du_livre = re.sub('\[\]\(([^)]+)\)', '', self.text_du_livre)
        # text_du_livre = re.sub('.*http.*', '', text_du_livre)
        
        # Find book langage
        # set variable book_langage
        self.get_text_language(self.words[200:500])

        # Find uncommon words
        self.find_uncommon_words(self.words)
        # print(uncommon_words)

        # Save the book raw txt
        with open(f"{self.directory_path}/_raw_text_{self.directory_path}.md", "w", encoding="utf-8") as markdown_file:
            markdown_file.write(text_du_livre)

        # citations = find_quotes(uncommon_words[:10],text_du_livre)

        # Produce markdown_content
        markdown_content = self.create_markdown_document()

        self.save_markdown_document(markdown_content)
        


        raw_list = [str(element) for element in self.uncommon_words]
        delimiter = "\n"
        raw_string = delimiter.join(raw_list)
        # Save the content to a Markdown file
        with open(f"{self.directory_path}/_raw_words {self.directory_path}.md", "w", encoding="utf-8") as markdown_file_raw:
            markdown_file_raw.write(raw_string)   

if __name__ == "__main__":
    with open('config.json') as config_file:
        data = json.load(config_file)

    vocabularyBuilder = BookVocabularyExtractor(data)
    vocabularyBuilder.main()