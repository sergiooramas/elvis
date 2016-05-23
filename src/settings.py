import os

relative_path = os.getcwd()
PATH = relative_path[:relative_path.rfind("/")]
#DBPEDIA_PATH = PATH+"/dbpedia/"
DBPEDIA_PATH = "../../KnowledgeExtraction/dbpedia/"
TEXTS_PATH = PATH+"/texts/"
DBPEDIA_SPOTLIGHT_ENDPOINT = "http://spotlight.sztaki.hu:2222/rest/annotate"
#BABELFY_KEY = ""
#TAGME_KEY = ""
BABELFY_KEY = "fd04a614-db0e-47a3-a6c6-451803a560ea"
TAGME_KEY = "454388ab362a716acb8201077dc8377b"
