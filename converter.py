import subprocess
from bs4 import BeautifulSoup
import requests
import re
import sys
from PIL import Image
import requests
import os
import shutil
import collections

#Inputs
url = "https://www.inkitt.com/stories/poetry/253054"
startChapter=1
endChapter=1
hasSumary=True



#Checking usable url and finding main page
regexUrl = re.search("(https:\/\/www\.inkitt\.com)([^\d]*)(\d*)?(.*)",url)
if regexUrl == None:
    print("wrong url")
    sys.exit()
bookLink = regexUrl[1]+regexUrl[2]+regexUrl[3]
print('mainPage:',bookLink)

#Checking aceptable number for start and end chapter
if(startChapter>endChapter or startChapter<1 or endChapter<1):
    print("star or end chapter wrong")
    sys.exit()



#Getting the book information
source = requests.get(bookLink).text
soup = BeautifulSoup(source, 'lxml')

bookTitle = soup.find("h1",class_="story-title story-title--big")
bookTitle = bookTitle.text
print("Getting book information from "+ bookTitle)

ImageDiv = soup.find("div", class_= "story-horizontal-cover__front")
ImageDivStyle = re.search("url\('(.*)'\)",ImageDiv.attrs['style'])
ImageUrl = ImageDivStyle[1]
bookImage = Image.open(requests.get(ImageUrl, stream=True).raw)

author = soup.find('meta',attrs={"name": "author"})
author = author.attrs['content']

path_to_kindlegen = os.getcwd()+"/kindlegen"
mobiName=f"{bookTitle}{str(startChapter)}-{str(endChapter)}"
path_to_book = os.getcwd()+"/books/"+mobiName


#Getting the chapters
chapter = collections.namedtuple("chapter", ["title","content"])
chapters = []

if(hasSumary):
    headerSummary = soup.find("header",class_="story-header")
    headerTitle = headerSummary.find("h2")
    bookSumary= headerSummary.find("p",class_="story-summary")
    chapters.append(chapter(title=headerTitle,content=bookSumary))

for i in range(startChapter,endChapter+1):
    newUrl = bookLink+"/chapters/"+str(i)
    print("Getting chapters from "+ newUrl)

    source = requests.get(newUrl).text
    soup = BeautifulSoup(source, 'lxml')
    chap =soup.find("article",id="story-text-container")

    chapTitle =chap.find("h2",class_="chapter-head-title")
    chapText =chap.div.div.find_all("p")

    chapters.append(chapter(title=chapTitle,content=chapText))



print("")
#Creating past of the book
if not os.path.exists(path_to_book):
    os.makedirs(path_to_book)
    print("create folder",path_to_book,"\n")

#creating opf file
newOpf = ""
print("writing opf")
with open(os.getcwd()+"/base.opf","r") as file:
    newOpf = file.read().replace("TITLEVARIABLE",bookTitle)
    newOpf = newOpf.replace("LANGUAGEVARIABLE","en")
    newOpf = newOpf.replace("AUTHORVARIABLE",author)
    opfFile = open(path_to_book+'/bookOpf.opf', "w")
    opfFile.write(newOpf)
    opfFile.close()

#"creating" css file
print("writing css")
bookImage.save(path_to_book+'/cover.jpg')
shutil.copy2("base.css",path_to_book+"/style.css")


#creating html file
print("writing html")
with open(os.getcwd()+"/base.html","r") as file:
    #updating opf metadata info
    newOpf = file.read().replace("TITLEVARIABLE",bookTitle)
    newOpf = newOpf.replace("LINKVARIABLE",bookLink)
    newOpf = newOpf.replace("AUTHORVARIABLE",author)
    newOpf = newOpf.replace("</body>","")

    opfFile = open(path_to_book+'/bookHtml.html', "w")
    opfFile.write(newOpf)

    #wrinting index
    for index, chap in enumerate(chapters):
        opfFile.write("<a href=\"#link"+str(index)+"\">"+ chap.title.text+"</a><br>")
    opfFile.write("<div class=\"mbp_pagebreak\"></div>")

    
    #wrinting chapters
    for index, chap in enumerate(chapters):
        opfFile.write("<div id=\"link"+str(index)+"\">" )
        opfFile.write( str(chap.title ))
        for j in chap.content:
            opfFile.write( str(j) )
        opfFile.write( "</div>")
        opfFile.write("<div class=\"mbp_pagebreak\"></div>")
    opfFile.close()


#Converting html to mobi
print("converting to mobi")
subprocess.run([path_to_kindlegen,path_to_book+"/bookOpf.opf","-o",mobiName+".mobi"] , stdout=subprocess.PIPE, stderr=subprocess.PIPE)
print("mobi file finish")
