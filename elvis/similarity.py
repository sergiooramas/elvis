import json
import glob
import codecs
import networkx as nx
import numpy as np
import argparse
import utils

N=10
artists_list = []

def set_n(n):
	global N
	N = n

def _maximal_common(G1,G2,weighted=False):
	common = len(set(G1.nodes()).intersection(set(G2.nodes())))
	size = max(len(G1.nodes()),len(G2.nodes()))
	similarity = common*1.0 / size
	return similarity

def _get_top_n(row):
	ordered = np.argsort(row)[::-1]
	top_list = []
	for index in ordered[1:N]:
		top_list.append(artists_list[index].decode("utf-8"))
	return top_list

def compute_similarity(technique,input_folder,save=False,output_folder='similarity/'):
	elvis_files = glob.glob(input_folder+"/*.json")
	prefix = "_".join(input_folder.split('/'))
	utils.create_directories(output_folder)
	output_matrix = output_folder+"/"+prefix+"_similarity_matrix.npy"
	output_index = output_folder+"/"+prefix+"_artists_list.tsv"
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
			mcs = _maximal_common(graphs[i], graphs[j])
			sim_matrix[i,j] = mcs
			sim_matrix[j,i] = mcs

	if save:
		np.save(output_matrix,sim_matrix)
		fw=open(output_index,'w')
		fw.write("\n".join(artists_list))
		fw.close()
	return sim_matrix, artists_list

def top_n(sim_matrix,artists_list,n=N,save=False,input_folder='',output_folder='similarity/'):
	set_n(n)
	top = np.apply_along_axis(_get_top_n, axis=1, arr=sim_matrix)
	if save:
		prefix = "_".join(input_folder.split('/'))
		output_list = output_folder+"/"+prefix+"_similarity_top_"+str(n)+".txt"
		fw = codecs.open(output_list,"w","utf-8")
		for index, l in enumerate(top):
			fw.write(artists_list[index].decode("utf-8")+"\t"+"\t".join(l)+"\n")
	
	return top


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Compute similarity between documents using Maximal Common Subgraph.')
    parser.add_argument('technique', help='Entity Linking Tool (spotlight, tagme, babelfy, all) (default=all)')
    parser.add_argument('source', help='Source of data to work with (e.g., example)')
    parser.add_argument('N', default=10, type=int, help='Top-N most similar entities')
    args = parser.parse_args()
    matrix,artists_list=compute_similarity(args.technique, args.source, True)
    top_n(matrix, artists_list, args.N, True, input_folder=args.source)

