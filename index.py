from flask import Flask, request, send_from_directory
from lxml import html
import re
import requests
import json
import os

SEARCHTERMS = 6

app = Flask(__name__,static_url_path='')
#app.config['DEBUG'] = True

@app.route("/")
def root():
    return app.send_static_file('index.html')

@app.route('/static/<path:path>')
def send_stuff(path):
    return send_from_directory('static', path)
    
@app.route("/wikiquery",methods=['GET'])
def process():
    searchterm = request.args['searchterm']
    filesize = os.stat("static/log.txt").st_size
    if(filesize<1048576):
        fout = open("static/log.txt","a")
        fout.write(searchterm + "\n")
        fout.close()
    else:
        fout = open("static/log.txt","w")
        fout.write(searchterm + "\n")
        fout.close()
    x = requests.get("http://en.wikipedia.org/wiki/" + searchterm)
    tree = html.fromstring(x.content)
    title = tree.xpath('//h1[@class="firstHeading"]/text()')
    tosend = {}
    tosend['PLACEHOLDERTEXT'] = "http://en.wikipedia.org/wiki/" + searchterm;
    links = re.findall("<a href=.*</a>",x.content)
    words = []
    linkset = set()
    for i in links:
        tmp = re.search("(?<=<).*(?=<)",i).group(0)
        if tmp not in linkset:
            num = (x.content).count(tmp)
            words.append((num,tmp))
            linkset.add(tmp)
    words.sort(reverse=True)
    
    count = 0
    index = 0
    bad = ["About Wikipedia","Disclaimers","Developers","Talk"]
    while count < SEARCHTERMS:
        link = re.search("href=\"([^\"]*)\"",words[index][1]).group(1)
        link = "https://en.wikipedia.org" + link
        text = re.search("(?<=>).*",words[index][1]).group(0)
        if "/wiki/" in link and len(text) < 30:
            ok = True
            for w in bad:
                if w in text:
                    ok = False
                    break
            if ok:
                text = text.replace("<i>","")
                text = text.replace("</i>","")
                text = text.replace("<b>","")
                text = text.replace("</b>","")
                if(text.strip()!=""):
                    count+=1
                tosend[text] = link
        index += 1
    
    return json.dumps(tosend)
    #x = requests.get("http://en.wikipedia.org/w/api.php?action=query&format=json&list=search&srsearch=\"" + searchterm + "\"")
    #i = 0
    #while "disambiguation" in json.loads(x.text)["query"]["search"][i]["title"]:
    #    i+=1
    #data = json.loads(x.text)["query"]["search"][i]["title"]
    #return data

if __name__ == "__main__":
    app.run(port=os.getenv("PORT"),host='0.0.0.0')
