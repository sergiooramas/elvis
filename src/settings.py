import os

relative_path = os.getcwd()
PATH = relative_path[:relative_path.rfind("/")]
DBPEDIA_PATH = PATH+"/dbpedia/"
TEXTS_PATH = PATH+"/texts/"
DBPEDIA_SPOTLIGHT_ENDPOINT = "http://spotlight.sztaki.hu:2222/rest/annotate"
BABELFY_KEY = ""
TAGME_KEY = ""
