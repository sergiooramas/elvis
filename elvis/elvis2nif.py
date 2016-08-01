#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import glob
import settings
import json
import codecs
import urllib
from rdflib import Graph, Literal, Namespace, RDF, URIRef, XSD
import os

class Wrapper():
	def __init__(self, data, name, graph):
		text = " "
		accumulated = 0
		for sentence in data:
			text += sentence['text'] + " "
			for entity in sentence['entities']:
				if 'uri' in entity:
					entity['startChar'] += accumulated
					entity['endChar'] += accumulated
					uri = entity['uri']
					entity['uri'] = uri[:uri.rfind("/")]+urllib.quote_plus(uri[uri.rfind("/")+1:].encode("utf8"))
			sentence['beginIndex'] = accumulated
			accumulated += len(sentence['text']) + 1
			sentence['endIndex'] = accumulated
		self.text = text
		self.sentences = data
		self.name = name
		self.mapping = dict()
		self.graph = graph

	def getClass(self,types):
		ont = "http://nerd.eurecom.fr/ontology#"
		dbpedia2nerd = {
		'ProgrammingLanguage':'ProgrammingLanguage',
		'Person':'Person',
		'VideoGame':'VideoGame',
		'Drug':'Drug',
		'Place':'Location',
		'Album':'Album',
		'Automobile':'Automobile',
		'Film':'Movie',
		'PersonFunction':'Function',
		'Newspaper':'Newspaper',
		'Animal':'Animal',
		'Song':'Song',
		'Book':'Book',
		'Spacecraft':'Spacecraft',
		'Organization':'Organization',
		'SportsEvent':'SportEvent',
		'Magazine':'Magazine',
		'MilitaryConflict':'MilitaryConflict',
		'Weapon':'Weapon',
		'Holiday':'Holiday',
		'MusicalArtist':'MusicalArtist',
		'Organization':'Organization',
		}
		nerd_classes = []
		for t in types:
			if ':' in t:
				slices = t.split(":")
				if 'DBpedia' in slices[0] and slices[1] in dbpedia2nerd:        		
					nerd_classes.append(dbpedia2nerd[slices[1]])
		if len(nerd_classes) > 0:
			selected = ont + nerd_classes[0]
		else:
			selected = 'None'
		return selected


	def nlp2rdf(self):

		# define some namespaces
		NIF =  Namespace("http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#")
		itsrdf = Namespace("http://www.w3.org/2005/11/its/rdf#")
		# generate the triples referencing the document as a whole
		doc_root = "http://mtg.upf.edu/elmd/"+self.name
		doc_uri = doc_root+"#char=0,"+str(len(self.text))
		self.graph.add((URIRef(doc_uri), RDF.type, NIF.String))
		self.graph.add((URIRef(doc_uri), RDF.type, NIF.Context))
		self.graph.add((URIRef(doc_uri), RDF.type, NIF.RFC5147String))
		self.graph.add((URIRef(doc_uri), NIF.beginIndex, Literal("0",datatype=XSD.nonNegativeInteger)))
		self.graph.add((URIRef(doc_uri), NIF.endIndex, Literal(len(self.text),datatype=XSD.nonNegativeInteger)))
		self.graph.add((URIRef(doc_uri), NIF.isString, Literal(self.text,datatype=XSD.string)))

		for sentence in self.sentences:
			sent_uri = doc_root+"#char="+str(sentence['beginIndex'])+","+str(sentence['endIndex'])
			self.graph.add((URIRef(sent_uri), RDF.type, NIF.String))
			self.graph.add((URIRef(sent_uri), RDF.type, NIF.Sentence))
			self.graph.add((URIRef(sent_uri), RDF.type, NIF.RFC5147String))
			self.graph.add((URIRef(sent_uri), NIF.beginIndex, Literal(sentence['beginIndex'],datatype=XSD.nonNegativeInteger)))
			self.graph.add((URIRef(sent_uri), NIF.endIndex, Literal(sentence['endIndex'],datatype=XSD.nonNegativeInteger)))
			self.graph.add((URIRef(sent_uri), NIF.anchorOf, Literal(sentence['text'],datatype=XSD.string)))
			self.graph.add((URIRef(sent_uri), NIF.referenceContext, URIRef(doc_uri)))
			for entity in sentence['entities']:
				if 'uri' in entity and 'dbpedia' in entity['uri']:
					ent_uri = doc_root+"#char="+str(entity['startChar'])+","+str(entity['endChar'])
					self.graph.add((URIRef(ent_uri), RDF.type, NIF.String))
					self.graph.add((URIRef(ent_uri), RDF.type, NIF.Word))
					self.graph.add((URIRef(ent_uri), RDF.type, NIF.RFC5147String))
					self.graph.add((URIRef(ent_uri), NIF.beginIndex, Literal(entity['startChar'],datatype=XSD.nonNegativeInteger)))
					self.graph.add((URIRef(ent_uri), NIF.endIndex, Literal(entity['endChar'],datatype=XSD.nonNegativeInteger)))
					self.graph.add((URIRef(ent_uri), NIF.anchorOf, Literal(entity['label'],datatype=XSD.string)))
					self.graph.add((URIRef(ent_uri), NIF.referenceContext, URIRef(doc_uri)))
					self.graph.add((URIRef(ent_uri), NIF.sentence, URIRef(sent_uri)))
					self.graph.add((URIRef(ent_uri), itsrdf.taIdentRef, URIRef(entity['uri'])))
					nerd_class = self.getClass(entity['types'].split(","))
					if nerd_class != 'None':
						self.graph.add((URIRef(ent_uri), itsrdf.taClassRef, URIRef(nerd_class)))
					self.graph.add((URIRef(ent_uri), itsrdf.taSource, Literal("DBpedia_en_3.9",datatype=XSD.string)))
		return self.graph

def create_directories(technique, source):
    if not os.path.exists(settings.PATH+"/entities/"+technique+"/"+source+"_nif"):
        os.mkdir(settings.PATH+"/entities/"+technique+"/"+source+"_nif")

def elvis2nif(technique,source):
	n = 0
	create_directories(technique, source)
	fw = codecs.open(settings.PATH+"/entities/%s/%s_nif/%s_%s_nif.ttl" % (technique,source,source,technique),"w","utf-8")            
	graph = Graph()
	for file in glob.glob(settings.PATH+"/entities/%s/%s/*.json" % (technique,source)):
		data = json.load(codecs.open(file,"r","utf-8"))
		wrapper = Wrapper(data,file[file.rfind("/")+1:-5],graph)
		graph = wrapper.nlp2rdf()
		n+=1
		if n%1000 == 0:
			print n
	# some prefix beauty
	graph.bind('nif', URIRef("http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#"))
	graph.bind('itsrdf', URIRef("http://www.w3.org/2005/11/its/rdf#"))
		
	# optionally serialize the graph in a given format
	# TODO RDF/json not supported by rdflib
	nif_data = graph.serialize(format='n3')
	fw.write(nif_data.decode("utf-8"))


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Transform ELVIS output to NIF format.')
	parser.add_argument('technique', help='Entity Linking Tool (spotlight, tagme, babelfy)')
	parser.add_argument('source', help='Source of data to work with (e.g., example)')
	args = parser.parse_args()
	elvis2nif(args.technique, args.source)
