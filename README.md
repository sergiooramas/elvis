# ELVIS (Entity Linking Voting and Integration System)
Framework to homogenize and combine the output of different entity linking tools, using the level of agreement between different tools as a confidence score.

You can run different Entity Linking tools (e.g. Tagme, Babelfy, DBpeida-Spotlight) from the same script and then convert the ouput fo the different systems into a uniform format. Then, you can combine the information from the different systems into a unique output where the number of tools that agree on the identification of entities is used as a confidence score.

The system does a batch process on a folder of text files. run_entity_linking.py runs a specific entity linking tool on every text file. For each text file, it tokenizes the text and run the entity linking tool with the whole text. Then entities are splitted in sentences in the output files. There is one output file for each input text file.

After running Entity Linking you can homogenize the output by runnin homogenize_output.py. It takes data from DBpedia to improve the level of information of every entity, and to provide a common output for all the systems. It adds type and categories information, resolve redirections within DBpedia, and solve character encoding issues.

Finally, the homogenized outputs of the different tools can be combined in a new output called agreement output by running create_agreement.py. Here, the system filter the entities where more than one tool have agreed in URI and offset. This script receives a parameter called level. If level 3 is selected, only entities where the 3 tools agreeed are selected, instead if level 2 is selected, only entities where at least 2 tools agreed are selected.

The system works with three Entity Linking tools, namely Tagme, Babelfy and DBpedia Spotlight. However, it is easily extensible and other tools can be used.

## Needed files

To run the output homogenizer you have to download the following files from <a href="http://dbpedia.org/Downloads2015-04">DBpedia</a>.

<a target="_blank" href="http://downloads.dbpedia.org/2015-04/core-i18n/en/article-categories_en.nt.bz2">article_categories_en.nt</a><br/>
<a target="_blank" href="http://downloads.dbpedia.org/2015-04/core-i18n/en/instance-types_en.nt.bz2">instance_types_en.nt</a><br/>
<a target="_blank" href="http://downloads.dbpedia.org/2015-04/core-i18n/en/instance_types_sdtyped-dbo_en.nt.bz2">instance_types_heuristic_en.nt</a><br/>
<a target="_blank" href="http://downloads.dbpedia.org/2015-04/core-i18n/en/page-ids_en.nt.bz2">page-ids_en.nt</a><br/>
<a target="_blank" href="http://downloads.dbpedia.org/2015-04/core-i18n/en/transitive-redirects_en.nt.bz2">transitive-redirects_en.nt</a><br/>
<a href="http://downloads.dbpedia.org/2015-04/links/yago_types.nt.bz2">yago_types.nt</a><br/>

## Configuration

In src/settings.py you should select the path for source texts and dbpedia files. In addition you have to add your API KEYS for the different Entity Linking tools.

## Execution

First you run the entity linking tool with the script run_entity_linking.py for the different tools. It will create a folder in entities/ folder for the specified tool and set of texts. Inside this folder there will be a file for every file in the source folder. 

Then you run the script homogenize_output.py to harmonize the output obtained from the different systems. It will create a new folder inside every tool folder with the suffix _h. 

Finally, you have to run create_agreement.py to obtain the agreement output. It will create a new folder inside the entities/agreement/ folder with the agreement output.

## Example

Delete the entities/ folder.
Download DBpedia files.
Configure the settings.py file, adding the API Keys of the different tools.
Run the following pipeline of scripts:

python run_entity_linking.py spotlight example
python run_entity_linking.py tagme example
python run_entity_linking.py babelfy example
python homogenize_output.py all example
python create_agreement.py example_h 2

Then you will find the final agreement output in the entities/agreement/ folder.

Note that homogenize_output.py will take some time as it has to load a lot of information from DBpedia in memory.

## References

If you use this code for research purposes, please cite our paper:

Sergio Oramas, Luis Espinosa-Anke, Mohamed Sordo, Horacio Saggion, and Xavier Serra. 2016. ELMD : An automatically generated entity linking gold standard in the music domain. In In Proceedings of the 10th International Conference on Language Resources and Evaluation, LREC 2016.

## License

This project is licensed under the terms of the MIT license.
