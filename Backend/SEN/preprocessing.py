import json
import os
import glob
import sys
import zipfile

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer,WordNetLemmatizer
import re
import wordninja
import numpy as np
import csv
import argparse
import os
import shutil
import copy
import pandas as pd
import os
from os import walk


def clean_str(string, TREC=False):
    """
    Tokenization/string cleaning for all datasets.
    Every dataset is lower cased.
    Original taken from https://github.com/dennybritz/cnn-text-classification-tf
    """
    string = re.sub(r"[^A-Za-z0-9(),!?\'\`#]", " ", string)
    string = re.sub(r"#SemST", "", string)
    string = re.sub(r"#([A-Za-z0-9]*)", r"# \1 #", string)
    #string = re.sub(r"# ([A-Za-z0-9 ]*)([A-Z])(.*) #", r"# \1 \2\3 #", string)
    #string =  re.sub(r"([A-Z])", r" \1", string)
    string = re.sub(r"\'s", " \'s", string)
    string = re.sub(r"\'ve", " \'ve", string)
    string = re.sub(r"n\'t", " n\'t", string)
    string = re.sub(r"\'re", " \'re", string)
    string = re.sub(r"\'d", " \'d", string)
    string = re.sub(r"\'ll", " \'ll", string)
    string = re.sub(r",", " , ", string)
    string = re.sub(r"!", " ! ", string)
    string = re.sub(r"\(", " ( ", string)
    string = re.sub(r"\)", " ) ", string)
    string = re.sub(r"\?", " ? ", string)
    string = re.sub(r"\s{2,}", " ", string)
    return string.strip() if TREC else string.strip().lower()

def unzip_single_file(zip_file_name, output_file_name, output_file_path):
    """
        If the outFile is already created, don't recreate
        If the outFile does not exist, create it from the zipFile
    """
    if not os.path.isfile(output_file_path):
        with open(output_file_path, 'wb') as out_file:
            with zipfile.ZipFile(zip_file_name) as zipped:
                for info in zipped.infolist():
                    if output_file_name in info.filename:
                        with zipped.open(info) as requested_file:
                            out_file.write(requested_file.read())
                            return

def load_glove_embeddings():
    PROJECT_ROOT = os.path.abspath(__file__)
    BASE_DIR = os.path.dirname(PROJECT_ROOT)
    glove_zip_file = BASE_DIR+"\\glove.6B.zip"
    glove_vectors_file = "glove.6B.300d.txt"
    glove_vectors_file_path= BASE_DIR+"\\glove.6B.300d.txt"

    from six.moves.urllib.request import urlretrieve

    # large file - 862 MB
    if (not os.path.isfile(glove_zip_file) and
            not os.path.isfile(glove_vectors_file_path)):
        print("don't have the file, downloading it - may take a few minutes")
        urlretrieve("http://nlp.stanford.edu/data/glove.6B.zip",
                    glove_zip_file)

    unzip_single_file(glove_zip_file, glove_vectors_file,glove_vectors_file_path)
    print("finished downloading")

    word2emb = {}
    WORD2VEC_MODEL = BASE_DIR+"\\glove.6B.300d.txt"

    fglove = open(WORD2VEC_MODEL,encoding="utf8")
    for line in fglove:
        cols = line.strip().split()
        word = cols[0]
        embedding = np.array(cols[1:],dtype="float32")
        word2emb[word]=embedding
    fglove.close()
    return word2emb

def split(word, word2emb):
    if word in word2emb:
        return [word]
    return wordninja.split(word)


def preprocessing(dataPath, toRemveStopWords=True):
    PROJECT_ROOT = os.path.abspath(__file__)
    BASE_DIR = os.path.dirname(PROJECT_ROOT)
    wnl = WordNetLemmatizer()
    ps = PorterStemmer()
    stop_words = set(stopwords.words('english'))


    #Creating Normalization Dictionary
    with open(BASE_DIR+"\\noslang_data.json", "r") as f:
        data1 = json.load(f)

    data2 = {}
    with open(BASE_DIR+"\\emnlp_dict.txt","r") as f:
        lines = f.readlines()
        for line in lines:
            row = line.split('\t')
            data2[row[0]] = row[1].rstrip()

    normalization_dict = {**data1,**data2}



    word2emb = load_glove_embeddings()

    for k in ["train", "test"]:
        n_count = 0
        s_words = 0
        # new_lines = []
        old_lines = []
        new_data_path=dataPath+"\\"+k+".csv"
        data = pd.read_csv(new_data_path, header=0)
        # lines=data['Claim']
        # with open(new_data_path, "r", encoding="utf8") as fp:
        # lines = fp.readlines()
        i=0
        for i in range(len(data['Sentence'])):
            # x = line.split("\t")
            line=data['Sentence'][i]
            old_sent = copy.deepcopy(line)
            old_lines.append(old_sent)
            sent = clean_str(line)
            word_tokens = sent.split(' ')

            # Normalization
            normalized_tokens = []
            for word in word_tokens:
                if word in normalization_dict.keys():
                    normalized_tokens.append(normalization_dict[word])
                    n_count += 1
                else:
                    normalized_tokens.append(word)

            # Word Ninja Splitting
            normalized_tokens_s = []
            for word in normalized_tokens:
                normalized_tokens_s.extend(split(word, word2emb))

            final_tokens = normalized_tokens_s

            if toRemveStopWords == True:
                # Stop Word Removal
                filtered_tokens = []
                for w in normalized_tokens_s:
                    if w not in stop_words:
                        filtered_tokens.append(w)
                    else:
                        s_words += 1

                # Stemming using Porter Stemmer
                stemmed_tokens = []
                for w in filtered_tokens:
                    stemmed_tokens.append(ps.stem(w))
                final_tokens = stemmed_tokens

            new_sent = ' '.join(final_tokens)
            # x[1] = new_sent
            # if (len(x) == 3):
            #     if correct == 0:
            #         x.append('NONE\n')
            #         correct += 1
            #     else:
            #         x.append('FAVOR\n')
            data['Sentence'][i]=new_sent
            # new_line = '\t'.join(x)
            # new_lines.append(new_line)



        # Write to a txt file
        data.to_csv(dataPath+"//"+k + "_clean.csv", index=False)
        # with open(dataPath+"//"+k + "_clean.csv", "w") as wf:
        #     lines_to_add=[]
        #     lines_to_add.append("Claim\tSentence\tStance\n")
        #     for line in new_lines:
        #         lines_to_add.append(line)
        #     wf.writelines(lines_to_add)

def run_preprocessing():
    import os
    PROJECT_ROOT = os.path.abspath(__file__)
    BASE_DIR = os.path.dirname(PROJECT_ROOT)
    arr = os.listdir(BASE_DIR+"\\topics")
    for topic in arr:
        preprocessing(BASE_DIR+"\\topics\\"+topic)
