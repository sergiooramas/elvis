import json
import settings
import glob
import codecs
import argparse
import os
import urllib

def load_types():
    f = open(settings.DBPEDIA_PATH+"instance_types_en.nt")
    uri_to_types = dict()
    for line in f:
        data = line.strip().split(" ")
        if data[1].endswith("type>"):
            uri_token, relation, type_token, _ = data
            uri = urllib.unquote(uri_token[1:-1]).decode("utf-8")
            if "dbpedia.org" in type_token:
                type = "DBpedia:"+type_token[type_token.rfind("/")+1:-1]
                uri_to_types.setdefault(uri,[]).append(type)
            elif "schema.org" in type_token:
                type = "Schema:"+type_token[type_token.rfind("/")+1:-1]
                uri_to_types.setdefault(uri,[]).append(type)
    f.close()
    f = open(settings.DBPEDIA_PATH+"instance_types_heuristic_en.nt")
    for line in f:
        data = line.strip().split(" ")
        if data[1].endswith("type>"):
            uri_token, relation, type_token, _ = data
            uri = urllib.unquote(uri_token[1:-1]).decode("utf-8")
            if "dbpedia.org" in type_token:
                type = "DBpedia:"+type_token[type_token.rfind("/")+1:-1]
                uri_to_types.setdefault(uri,[]).append(type)
            elif "schema.org" in type_token:
                type = "Schema:"+type_token[type_token.rfind("/")+1:-1]
                uri_to_types.setdefault(uri,[]).append(type)
    f.close()
    f = open(settings.DBPEDIA_PATH+"yago_types.nt")
    for line in f:
        data = line.strip().split(" ")
        if data[1].endswith("type>"):
            uri_token, relation, type_token, _ = data
            uri = urllib.unquote(uri_token[1:-1]).decode("utf-8")
            type = "Yago:"+type_token[type_token.rfind("/")+1:-1]
            uri_to_types.setdefault(uri,[]).append(type)
    f.close()
    return uri_to_types    

def load_categories():
    f = open(settings.DBPEDIA_PATH+"article_categories_en.nt")
    uri_to_categories = dict()
    for line in f:
        data = line.strip().split(" ")
        if data[1].endswith("subject>"):
            uri_token, relation, type_token, _ = data
            uri = urllib.unquote(uri_token[1:-1]).decode("utf-8")
            uri_to_categories.setdefault(uri,[]).append(type_token[type_token.rfind(":")+1:-1])
    f.close()
    return uri_to_categories

def load_redirections():
    f = open(settings.DBPEDIA_PATH+"transitive-redirects_en.nt")
    redirection_to_uri = dict()
    for line in f:
        data = line.strip().split(" ")
        if data[1].endswith("wikiPageRedirects>"):
            redirection_token, relation, uri_token, _ = data
            uri = urllib.unquote(uri_token[1:-1]).decode("utf-8")
            redirection = urllib.unquote(redirection_token[1:-1]).decode("utf-8")
            redirection_to_uri[redirection] = uri
    f.close()
    return redirection_to_uri

def load_ids():
    f = open(settings.DBPEDIA_PATH+"page_ids_en.nt")
    id_to_dbpedia = dict()
    for line in f:
        data = line.strip().split(" ")
        if data[1].endswith("wikiPageID>"):
            uri_token, relation, id_token, _ = data
            uri = urllib.unquote(uri_token[1:-1]).decode("utf-8")
            id = int(id_token[1:id_token.rfind('"')])
            id_to_dbpedia[id] = uri
    f.close()
    return id_to_dbpedia

def create_directories(technique, source):
    if not os.path.exists(settings.PATH+"/entities/"+technique+"/"+source+"_h"):
        os.mkdir(settings.PATH+"/entities/"+technique+"/"+source+"_h")

def homogenize_ner(technique,source):
    if technique == 'all':
        techniques = ['spotlight','tagme','babelfy']
    else:
        techniques = [technique]
    uri_to_types = load_types()
    if technique == 'all' or technique == 'spotlight' or technique == 'babelfy':
        uri_to_categories = load_categories()
    if technique == 'all' or technique == 'tagme':
        id_to_dbpedia = load_ids()
    redirection_to_uri = load_redirections()
    print "Data loaded"
    for technique in techniques:
        create_directories(technique, source)
        folder = settings.PATH+"/entities/%s/%s" % (technique,source)
        output_folder = settings.PATH+"/entities/%s/%s_h/" % (technique,source)
        filenames = sorted(list(glob.glob(folder+"/*.json")))
        for file in filenames:
            name = file[file.rfind("/")+1:]
            sentences = json.load(codecs.open(file, "r", "utf-8"))
            for sentence in sentences:
                entities = []
                for entity in sentence['entities']:
                    add = True
                    if technique.lower() == "spotlight":
                        uri = entity['uri']
                        if entity['uri'] in uri_to_categories:
                            entity['categories'] = uri_to_categories[entity['uri']]
                        if entity['types'] == "":
                            if uri in uri_to_types:
                                entity['types'] = ",".join(uri_to_types[uri])                        
                    elif technique.lower() == "tagme":
                        entity['types'] = ""
                        if int(entity['id']) in id_to_dbpedia:
                            entity['uri'] = id_to_dbpedia[entity['id']]
                        elif 'uri' in entity:
                            entity['uri'] = "http://dbpedia.org/resource/"+entity['uri'].replace(" ","_")
                        else:
                            entity['uri'] = "NONE"
                            add = False
                        uri = entity['uri']
                        if uri in uri_to_types:
                            entity['types'] = ",".join(uri_to_types[uri])
                        formated_categories = []
                        if 'categories' in entity:
                            for category in entity['categories']:
                                formated_categories.append(category.replace(" ","_"))                        
                        entity['categories'] = formated_categories
                    elif technique.lower() == "babelfy":
                        entity['types'] = ""
                        if "dbpedia" in entity['uri']:
                            entity['uri'] = entity['uri'].replace("\\u0026","&").replace("\\u0027","'")
                            if entity['uri'] in uri_to_categories:
                                entity['categories'] = uri_to_categories[entity['uri']]
                            if entity['uri'] in uri_to_types:
                                entity['types'] = ",".join(uri_to_types[entity['uri']])
                            entity['endChar'] += 1
                    if entity['uri'] in redirection_to_uri:
                        entity['uri'] = redirection_to_uri[entity['uri']]
                    if add:
                        entities.append(entity)
                sentence['entities'] = entities
            json.dump(sentences, codecs.open(output_folder+name, "w", "utf-8"))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Homogenize the output of the Entity Linking systems.')
    parser.add_argument('technique', default="all", help='Entity Linking Tool (spotlight, tagme, babelfy, all) (default=all)')
    parser.add_argument('source', help='Source of data to work with (e.g., example)')
    args = parser.parse_args()
    homogenize_ner(args.technique, args.source)
