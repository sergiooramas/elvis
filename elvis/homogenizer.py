import json
import glob
import codecs
import argparse
import urllib
import requests
import utils

uri_to_types = {}
uri_to_categories = {}
id_to_dbpedia = {}
redirection_to_uri = {}

DBPEDIA_PATH = "../dbpedia/"
SERVER_URL = "http://elvis.mtg.upf.edu"

session = requests.Session()
session.mount(SERVER_URL, requests.adapters.HTTPAdapter(max_retries=5))

def set_dbpedia_path(path):
    global DBPEDIA_PATH
    DBPEDIA_PATH = path

def set_server_url(url):
    global SERVER_URL
    SERVER_URL = url
    session = requests.Session()
    session.mount(SERVER_URL, requests.adapters.HTTPAdapter(max_retries=5))

def _load_types():
    f = open(DBPEDIA_PATH+"instance_types_en.nt")
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
    f = open(DBPEDIA_PATH+"instance_types_heuristic_en.nt")
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
    f = open(DBPEDIA_PATH+"yago_types.nt")
    for line in f:
        data = line.strip().split(" ")
        if data[1].endswith("type>"):
            uri_token, relation, type_token, _ = data
            uri = urllib.unquote(uri_token[1:-1]).decode("utf-8")
            type = "Yago:"+type_token[type_token.rfind("/")+1:-1]
            uri_to_types.setdefault(uri,[]).append(type)
    f.close()
    return uri_to_types

def _load_categories():
    f = open(DBPEDIA_PATH+"article_categories_en.nt")
    uri_to_categories = dict()
    for line in f:
        data = line.strip().split(" ")
        if data[1].endswith("subject>"):
            uri_token, relation, type_token, _ = data
            uri = urllib.unquote(uri_token[1:-1]).decode("utf-8")
            uri_to_categories.setdefault(uri,[]).append(type_token[type_token.rfind(":")+1:-1])
    f.close()
    return uri_to_categories

def _load_redirections():
    f = open(DBPEDIA_PATH+"transitive-redirects_en.nt")
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

def _load_ids():
    f = open(DBPEDIA_PATH+"page_ids_en.nt")
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

def _load_from_local(technique):
    global redirection_to_uri, uri_to_types, uri_to_categories, id_to_dbpedia
    uri_to_types = _load_types()
    if technique == 'all' or technique == 'spotlight' or technique == 'babelfy':
        uri_to_categories = _load_categories()
    if technique == 'all' or technique == 'tagme':
        id_to_dbpedia = _load_ids()
    redirection_to_uri = _load_redirections()

def _get_redirections(key, use_remote=False):
    global redirection_to_uri
    if use_remote:
        url = SERVER_URL + "/redirects"
        q = session.get(url, data={'key': key})
        resp = q.json()
        return resp['result']
    else:
        return redirection_to_uri[key]

def _get_categories(key, use_remote=False):
    global uri_to_categories
    if use_remote:
        url = SERVER_URL + "/categories"
        q = session.get(url, data={'key': key})
        resp = q.json()
        return resp['result']
    else:
        return uri_to_categories[key]

def _get_id_dbpedia(key, use_remote=False):
    global id_to_dbpedia
    if use_remote:
        url = SERVER_URL + "/ids"
        q = session.get(url, data={'key': key})
        resp = q.json()
        return resp['result']
    else:
        return id_to_dbpedia[key]

def _get_types(key, use_remote=False):
    global uri_to_types
    if use_remote:
        url = SERVER_URL + "/types"
        q = session.get(url, data={'key': key})
        resp = q.json()
        return resp['result']
    else:
        return uri_to_types[key]

def _check_status():
    url = SERVER_URL + "/status"
    try:
        q = session.get(url)
        return q.status_code == 200
    except requests.exceptions.ConnectionError:
        return False

def homogenize(technique,ner_folder,data='server'):
    # Check if remote server is working, otherwise use local files
    remote_working = check_status()
    if not remote_working or data=='local':
        print "Starting to load data from local files"
        _load_from_local(technique)
        print "Data loaded"

    if technique == 'all':
        techniques = ['spotlight','tagme','babelfy']
    else:
        techniques = [technique]

    for technique in techniques:
        output_folder = ner_folder + "_h/" + technique + "/"
        folder = ner_folder + '/' + technique
        utils.create_directories(output_folder)
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
                        ret_categories = _get_categories(entity['uri'],
                                use_remote=remote_working)
                        if ret_categories:
                            entity['categories'] = ret_categories
                        if entity['types'] == "":
                            ret_types = _get_types(uri, use_remote=remote_working)
                            if ret_types:
                                entity['types'] = ",".join(ret_types)
                    elif technique.lower() == "tagme":
                        entity['types'] = ""
                        ret_id_dbpedia = _get_id_dbpedia(entity['id'],
                                 use_remote=remote_working)
                        if ret_id_dbpedia:
                            entity['uri'] = ret_id_dbpedia

                        elif 'uri' in entity:
                            entity['uri'] = "http://dbpedia.org/resource/"+entity['uri'].replace(" ","_")
                        else:
                            entity['uri'] = "NONE"
                            add = False
                        uri = entity['uri']
                        ret_types = _get_types(uri, use_remote=remote_working)
                        if ret_types:
                            entity['types'] = ",".join(ret_types)

                        formated_categories = []
                        if 'categories' in entity:
                            for category in entity['categories']:
                                formated_categories.append(category.replace(" ","_"))
                        entity['categories'] = formated_categories
                    elif technique.lower() == "babelfy":
                        entity['types'] = ""
                        if "dbpedia" in entity['uri']:
                            entity['uri'] = entity['uri'].replace("\\u0026","&").replace("\\u0027","'")
                            ret_categories = _get_categories(entity['uri'], use_remote=remote_working)
                            if ret_categories:
                                entity['categories'] = ret_categories
                            ret_types = _get_types(entity['uri'],
                                    use_remote=remote_working)
                            if ret_types:
                                entity['types'] = ",".join(ret_types)

                            entity['endChar'] += 1
                    ret_redirection = _get_redirections(entity['uri'],
                            use_remote=remote_working)
                    if ret_redirection:
                        entity['uri'] = ret_redirection
                    if add:
                        entities.append(entity)
                sentence['entities'] = entities
            json.dump(sentences, codecs.open(output_folder+name, "w", "utf-8"))
            print name

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Homogenize the output of the Entity Linking systems.')
    parser.add_argument('technique', default="all", help='Entity Linking Tool (spotlight, tagme, babelfy, all) (default=all)')
    parser.add_argument('folder', help='Source of data to work with (e.g., example)')
    parser.add_argument('data', nargs='?', default='server', help='DBpedia files locally or in server (local, server) (default=server)')
    args = parser.parse_args()
    homogenize(args.technique, args.folder, args.data)
