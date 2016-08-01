#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import glob
import settings
import json
import codecs
import os

def create_directories(source,level):
    if not os.path.exists(settings.PATH+"/entities/agreement"):
        os.mkdir(settings.PATH+"/entities/agreement")
    if not os.path.exists(settings.PATH+"/entities/agreement/"+source+"_"+str(level)):
        os.mkdir(settings.PATH+"/entities/agreement/"+source+"_"+str(level))

def intersects(entity1,entity2):
    intersect = True
    if entity1[0] < entity2[0] and entity1[1] < entity2[0]:
        intersect = False
    elif entity2[0] < entity1[0] and entity2[1] < entity1[0]:
        intersect = False
    return intersect

def aggregation(entities,to_add):
	union = entities
	for e in to_add:
		intersect = False
		for ent in entities:
			if intersects(e, ent):
				intersect = True
				break
		if not intersect:
			union.add(e)
	return union


def agreement(source,level):
	tools = ['babelfy','tagme','spotlight']
	filenames = sorted(list(glob.glob(settings.PATH+"/entities/"+tools[0]+"/"+source+"/*.json")))
	output_folder = settings.PATH+"/entities/agreement/"+source+"_"+str(level)+"/"
	n = 0
	for file in filenames:
		output_sentences = []
		name = file[file.rfind("/")+1:]	
		sentences = json.load(codecs.open(file,"r", "utf-8"))
		ner_file = dict()
		ner_sentences = dict()
		for tool in tools:
			ner_file[tool] = settings.PATH+"/entities/"+tool+"/"+source+"/"+name
			ner_sentences[tool] = json.load(codecs.open(ner_file[tool],"r", "utf-8"))
		i = 0
		for i in range(0,len(sentences)):
			sentence = dict()
			sentence['text'] = sentences[i]['text']
			sentence['index'] = sentences[i]['index']
			sentence['entities'] = []
			entities = dict()
			all_entities = dict()
			for tool in tools:
				entities[tool] = set()
				for entity in ner_sentences[tool][i]['entities']:
					entities[tool].add((entity['startChar'],entity['endChar'],entity['uri']))
					all_entities[(entity['startChar'],entity['endChar'],entity['uri'])] = entity
			agreement3 = entities[tools[0]].intersection(entities[tools[1]]).intersection(entities[tools[2]])
			if level == 3:
				agreement = agreement3
			elif level == 2:
				inter1 = entities[tools[0]].intersection(entities[tools[1]])
				inter2 = entities[tools[0]].intersection(entities[tools[2]])
				inter3 = entities[tools[1]].intersection(entities[tools[2]])
				agreement = inter1.union(inter2).union(inter3)
			for entity_key in agreement:
				entity = all_entities[entity_key]
				if level == 3 or (level == 2 and entity_key in agreement3):
					entity['confidence'] = 3
				else:
					entity['confidence'] = 2
				sentence['entities'].append(entity)
			output_sentences.append(sentence)
		json.dump(output_sentences, codecs.open(output_folder+name,'w','utf-8'))
		n += 1
		if n % 1000 == 0:
			print n

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Create new output with the agreement of the EL tools.')
	parser.add_argument('source', help='Source of data to work with (e.g., example)')
	parser.add_argument('level', help='Minimum level of agreement (2,3)')
	args = parser.parse_args()
	create_directories(args.source,args.level)
	agreement(args.source,int(args.level))
