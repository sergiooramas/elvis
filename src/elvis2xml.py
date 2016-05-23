import json
import glob
import codecs
import settings
import argparse
import os

def create_directories(technique, source):
    if not os.path.exists(settings.PATH+"/entities/"+technique+"/"+source+"_xml"):
        os.mkdir(settings.PATH+"/entities/"+technique+"/"+source+"_xml")

def escapeXml(text):
    return text.replace("&","&amp;").replace('"',"&quot;").replace("<","&lt;").replace(">","&gt;")

def getAnnotations(data):
    text = "<?xml version='1.0' encoding='UTF-8'?>\n<Text>"
    accumulated = 0
    for sentence in data:
        previous = 0
        text += '<Sentence index="'+str(sentence['index'])+'">'
        for entity in sentence['entities']:
            uri = entity['uri']
            entityTag = '<Entity uri="%s">' % (escapeXml(uri))
            endTag = '</Entity>'
            text += escapeXml(sentence['text'][previous:entity['startChar']]) + entityTag + escapeXml(sentence['text'][entity['startChar']:entity['endChar']]) + endTag
            previous = entity['endChar']
        text += sentence['text'][previous:]+'</Sentence>'
        sentence['beginIndex'] = accumulated
        accumulated += len(sentence['text']) + 1
        sentence['endIndex'] = accumulated
    text += '</Text>'
    return text

def elvis2xml(technique,source):
    n = 0
    create_directories(technique, source)
    for file in glob.glob(settings.PATH+"/entities/%s/%s/*.json" % (technique,source)):
        data = json.load(codecs.open(file,"r","utf-8"))
        text = getAnnotations(data)
        fw=codecs.open(file.replace("/%s/" % source,"/%s_xml/" % source).replace(".json",".xml"),"w","utf-8")
        fw.write(text)
        fw.close()
        n+=1
        if n%1000 == 0:
            print n

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Transform ELVIS output to XML compatible with GATE.')
    parser.add_argument('technique', help='Entity Linking Tool (spotlight, tagme, babelfy)')
    parser.add_argument('source', help='Source of data to work with (e.g., example)')
    args = parser.parse_args()
    elvis2xml(args.technique, args.source)

