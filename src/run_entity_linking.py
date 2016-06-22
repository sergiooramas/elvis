import os, subprocess, json, codecs, argparse, glob
import urllib
import settings
import time
from nltk.tokenize import sent_tokenize

def _call(cmd):
    done = False
    tries = 0
    while not done and tries < 10:
        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = p.communicate()
            #print p.returncode
            if stdout != "":
                done = True
            else:
                print "Error"
                tries += 1
            return p.returncode, stdout
        except:
            print "Error"
            tries += 1
            return 0,""

def _dbpedia_annotate(text):
    cmd = ['curl', '-H', 'Accept: application/json', settings.DBPEDIA_SPOTLIGHT_ENDPOINT, '--data-urlencode', 'text=%s' % urllib.quote(text.encode("utf8")),
               '--data', 'confidence=0.2', '--data', 'support=20']
    return _call(cmd)

def _tagme_annotate(text):
    server = "http://tagme.di.unipi.it/tag"
    data = "key="+settings.TAGME_KEY+"&include_categories=true&text="+urllib.quote(text.encode("utf8"))
    cmd = ['curl', '--data', data, server]
    return _call(cmd)
    
def _babelfy_annotate(text):
    server = "https://babelfy.io/v1/disambiguate"
    data = "key="+settings.BABELFY_KEY+"&lang=EN&annType=ALL&text="+urllib.quote(text.encode("utf8"))
    cmd = ['curl', '--data', data, server]
    return _call(cmd)

def create_directories(technique, source):
    if not os.path.exists(settings.PATH+"/entities"):
        os.mkdir(settings.PATH+"/entities")
    if not os.path.exists(settings.PATH+"/entities/"+technique):
        os.mkdir(settings.PATH+"/entities/"+technique)
    if not os.path.exists(settings.PATH+"/entities/"+technique+"/"+source):
        os.mkdir(settings.PATH+"/entities/"+technique+"/"+source)

def spotlight(sentences):
    text = "\n".join(sentences)
    ner_sentences = []
    if text.strip() != "":
        code, data = _dbpedia_annotate(text)
        try:
            data = eval(data)
        except:
            data = []
        accumulated = 0
        index = 0
        for sentence in sentences:
            entities = []
            if 'Resources' in data:
                for resource in data['Resources']:
                    offset = int(resource['@offset'])
                    if offset >= accumulated and offset < accumulated + len(sentence):
                        entity = dict()
                        entity['uri'] = resource['@URI']
                        entity['types'] = resource['@types']
                        entity['startChar'] = offset - accumulated
                        entity['endChar'] = offset - accumulated + len(resource['@surfaceForm'])
                        entity['confidence'] = resource['@similarityScore']
                        entity['label'] = resource['@surfaceForm']
                        entities.append(entity)
                    if offset > accumulated + len(sentence):
                        break
            accumulated += len(sentence) + 1
            ner_sentences.append({"text":sentence.strip(),"entities":entities,"index":index})
            index += 1
    return ner_sentences

def tagme(sentences):
    text = "\n".join(sentences)
    ner_sentences = []
    if text != "":
        code, data = _tagme_annotate(text)
        data = eval(data)
        accumulated = 0
        index = 0
        for sentence in sentences:
            entities = []
            if 'annotations' in data:
                for resource in data['annotations']:
                    if resource['start'] >= accumulated and resource['start'] < accumulated + len(sentence):
                        entity = dict()
                        if 'title' in resource:
                            entity['uri'] = resource['title']
                        entity['id'] = resource['id']
                        if 'dbpedia_categories' in resource:
                            entity['categories'] = resource['dbpedia_categories']
                        entity['startChar'] = resource['start'] - accumulated
                        entity['endChar'] = resource['end'] - accumulated
                        entity['confidence'] = resource['rho']
                        entity['label'] = resource['spot']
                        entities.append(entity)
                    if resource['start'] > accumulated + len(sentence):
                        break
            accumulated += len(sentence) + 1
            ner_sentences.append({"text":sentence.strip(),"entities":entities,"index":index})
            index += 1
    return ner_sentences

def babelfy(sentences):
    text = "\n".join(sentences)
    ner_sentences = []
    if text != "":
        code, data = _babelfy_annotate(text)
        data = eval(data)
        accumulated = 0
        index = 0
        for sentence in sentences:
            entities = []
            for resource in data:
                if resource['charFragment']['start'] >= accumulated and resource['charFragment']['start'] < accumulated + len(sentence):
                    entity = dict()
                    entity['uri'] = resource['DBpediaURL']
                    entity['BabelNetURL'] = resource['BabelNetURL']
                    entity['babelSynsetID'] = resource['babelSynsetID']
                    entity['startChar'] = resource['charFragment']['start'] - accumulated
                    entity['endChar'] = resource['charFragment']['end'] - accumulated
                    entity['confidence'] = resource['score']
                    entity['label'] = text[resource['charFragment']['start']:resource['charFragment']['end']+1]
                    entities.append(entity)
                if resource['charFragment']['start'] > accumulated + len(sentence):
                    break
            accumulated += len(sentence) + 1
            ner_sentences.append({"text":sentence.strip(),"entities":entities,"index":index})
            index += 1
    return ner_sentences

def run_tool(source, technique, notokenize, start_index=0, end_index=None):
    create_directories(technique, source)
    input_filenames = sorted(list(glob.glob(settings.TEXTS_PATH+source+"/*.txt")))
    for input_filename in input_filenames[start_index:end_index]:
        suffix = input_filename[input_filename.rfind("/")+1:-4]
        output_filename = settings.PATH+"/entities/"+technique+"/"+source+"/"+suffix+".json"
        print suffix
        if not os.path.exists(output_filename):  
            if notokenize:
                with codecs.open(input_filename, "r", "utf-8") as f:
                    sentences = [line for line in f]
            else:
                with codecs.open(input_filename, "r", "utf-8") as f:
                    text = f.read()
                sentences = sent_tokenize(text)
            ner_sentences = []
            if technique == 'tagme':
                ner_sentences = tagme(sentences)
            elif technique == 'babelfy':
                ner_sentences = babelfy(sentences)
            elif technique == 'spotlight':
                ner_sentences = spotlight(sentences)
            json.dump(ner_sentences, codecs.open(output_filename, "w", "utf-8"))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Perform Entity Linking.')
    parser.add_argument('technique', default="spotlight", help='Entity Linking Tool (spotlight, tagme, babelfy) (default=spotlight)')
    parser.add_argument('source', help='Source of data to work with (e.g., example)')
    parser.add_argument('-nt', dest='notokenize', action='store_true', help='Disable tokenization')
    parser.add_argument('-s', '--start-index', type=int, default=0, help='start index (default=0)')
    parser.add_argument('-e', '--end-index', type=int, help='end index (default=number of files)')
    args = parser.parse_args()
    start_time = time.time()
    run_tool(args.source, args.technique.lower(), args.notokenize, args.start_index, args.end_index)
    print(time.time() - start_time)

