#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import glob
import codecs
import networkx as nx
import numpy as np
import settings
import argparse

N=10
artists_list = []

def maximal_common(G1,G2,weighted=False):
	common = len(set(G1.nodes()).intersection(set(G2.nodes())))
	size = max(len(G1.nodes()),len(G2.nodes()))
	similarity = common*1.0 / size
	return similarity

def get_top_n(row):
	ordered = np.argsort(row)
	top_list = []
	for index in ordered[:N]:
		top_list.append(artists_list[index].decode("utf-8"))
	return top_list

def compute_similarity(technique,source):
	elvis_files = glob.glob(settings.PATH+"/entities/"+technique+"/"+source+"/*.json")
	output_list = settings.PATH+"/similarity/"+source+"_"+technique+"_similarity_top_"+str(N)+".txt"
	output_matrix = settings.PATH+"/similarity/"+source+"_"+technique+"_similarity_matrix.npy"
	index = []
	graphs = []

	for file in elvis_files:
		G = nx.Graph()
		data = json.load(codecs.open(file,"r","utf-8"))
		filename = file[file.rfind("/")+1:-5]
		G.add_node(filename)
		for sentence in data:
			for entity in sentence['entities']:
				G.add_edge(filename,entity['uri'])
		graphs.append(G)
		artists_list.append(filename)

	sim_matrix = np.zeros((len(graphs),len(graphs)))
	for i in range(0,len(graphs)):
		for j in range(i,len(graphs)):
			mcs = maximal_common(graphs[i], graphs[j])
			sim_matrix[i,j] = mcs
			sim_matrix[j,i] = mcs

	top = np.apply_along_axis(get_top_n, axis=1, arr=sim_matrix)
	fw = codecs.open(output_list,"w","utf-8")
	for index, l in enumerate(top):
		fw.write(artists_list[index].decode("utf-8")+"\t"+"\t".join(l)+"\n")
	
	np.save(output_matrix,sim_matrix)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Compute similarity between documents using Maximal Common Subgraph.')
    parser.add_argument('technique', help='Entity Linking Tool (spotlight, tagme, babelfy, all) (default=all)')
    parser.add_argument('source', help='Source of data to work with (e.g., example)')
    parser.add_argument('N', default=10, help='Top-N most similar entities')
    args = parser.parse_args()
    N = int(args.N)
    compute_similarity(args.technique, args.source)

