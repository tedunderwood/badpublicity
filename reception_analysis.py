# -*- coding: utf-8 -*-
# reception_analysis.py
# Ted Underwood, Dec 2019

# This file constructs a matrix where each row is a book, and
# each column is a site of reception. In most cases the columns
# are publications, and the cells will be filled with the wordcount
# of the length of their review. There are also special cases, e.g.
# Pulitzer Prize or bestseller lists, where the book was either
# included (1) or not (0). Price and average sentiment as indicated
# by the BRD are also included as columns.

import pandas as pd
import numpy as np
import csv, re, glob
from difflib import SequenceMatcher
from scipy.stats import zscore
from collections import Counter

wordcountregex = re.compile('\d*0w[.]?')

def get_ratio(stringA, stringB):

    m = SequenceMatcher(None, stringA, stringB)

    thefilter = m.real_quick_ratio()
    if thefilter < 0.5:
        return thefilter

    else:
        return m.ratio()

def makeint(wordcount):
    wordcount = wordcount[ : -1]
    try:
        intwords = int(wordcount)
    except:
        intwords = 50
    return intwords

# triplets2process = []

# with open('pairing_meta.tsv', encoding = 'utf-8') as f:
#     reader = csv.DictReader(f, delimiter = '\t')
#     for row in reader:
#         triplets2process.append(row)

def gather_reviewdata(folderpath):
    '''
    Given a folder, this loads all the .tsv files,
    normalizes prices at the year level, and
    concatenates the results.
    '''

    folderpaths = glob.glob(folderpath + '*.tsv')

    revframes = []

    for fpath in folderpaths:
        filename = fpath.split('/')[-1]
        year = int(fpath.replace('.tsv', '')[-4:])
        revdf = pd.read_csv(fpath, sep = '\t')
        revdf = revdf.assign(volyear = year)

        prices = np.array(revdf['price'])
        nonzeroprices = np.nonzero(prices)
        nonzeroprices = prices[nonzeroprices]
        pricemean = np.mean(nonzeroprices)
        prices[prices == 0] = pricemean
        zprices = zscore(prices)

        revdf = revdf.assign(normedprice = zprices)
        revdf['bookindex'] = revdf['bookindex'].astype(str)

        for idx in revdf.index:
            revdf.at[idx, 'bookindex'] = str(year) + '+' + str(revdf.at[idx, 'bookindex'])

        revframes.append(revdf)

    masterframe = pd.concat(revframes)
    print(masterframe.shape)

    return masterframe

reviews = gather_reviewdata('../../downloads/release1/')

reviews_by_book = reviews.groupby(['bookindex'])

pubframe = pd.read_csv('brd_pubs_indexed.tsv', sep = '\t')

pubs = [x.replace('.', '') for x in pubframe['code']]
pubs.extend(['other pubs', 'Boston Transcript', 'A L A Bkl', 'The Times [London] Lit Sup', 'New Repub', 'Cleveland', 'Wis Lib Bul', 'Pittsburgh', 'Survey', 'Books (N Y Herald Tribune)', 'New Statesman', 'Int Bk R', 'N Y Evening Post', 'Bookm', 'Sat R of Lit', 'Books', 'Pratt', 'Nation and Ath', 'Boston Transcript', 'NY Evening Post', 'Living Age'])
pubs = list(set(pubs))

bestseller_df = pd.read_csv('bestsellers.tsv', sep = '\t')
bestsellers = set()
for idx, row in bestseller_df.iterrows():
    bestsellers.add((row['bookauthor'], row['booktitle']))

prizelists = set()
pulitzer_df = pd.read_csv('pulitzer.tsv', sep = '\t')
for idx, row in pulitzer_df.iterrows():
    prizelists.add((row['bookauthor'], row['booktitle']))

modlib_df = pd.read_csv('modernlibrary.tsv', sep = '\t')
for idx, row in modlib_df.iterrows():
    prizelists.add((row['bookauthor'], row['booktitle']))


wordcounts = dict()
sentiments = dict()

bookrange = list(set(reviews['bookindex']))
booktable = dict()
for idx, value in enumerate(bookrange):
    booktable[value] = idx

bookmatrix = dict()

for p in pubs:
    wordcounts[p] = []
    bookmatrix[p] = np.zeros(len(bookrange))

bookmatrix['sentiment'] = np.zeros(len(bookrange))
bookmatrix['price'] = np.zeros(len(bookrange))
bookmatrix['bestsellers'] = np.zeros(len(bookrange))
bookmatrix['prizelists'] = np.zeros(len(bookrange))

missingpubs = Counter()

for bookidx, df in reviews_by_book:
    firstrow = df.iloc[0, : ]
    matrix_index = booktable[bookidx]

    bookmatrix['sentiment'][matrix_index] = firstrow['avgsentiment']
    bookmatrix['price'][matrix_index] = firstrow['normedprice']

    key = (firstrow['bookauthor'], firstrow['booktitle'])
    if key in prizelists:
        bookmatrix['prizelists'][matrix_index] = 1.0
    if key in bestsellers:
        bookmatrix['bestsellers'][matrix_index] = 1.0

    alreadychosen = set()

    for subidx, row in df.iterrows():
        thispub = row['publication']
        if pd.isnull(thispub):
            continue
        else:
            thispub = thispub.replace('.', '')

        themax = 0
        winner = 'other'
        for p in pubs:
            if p in alreadychosen:
                continue
            ratio = get_ratio(p, thispub)
            if ratio > themax and ratio > 0.5:
                themax = ratio
                winner = p

        if winner == 'other':
            missingpubs[thispub] += 1
            winner = 'other pubs'
        else:
            alreadychosen.add(winner)

        if not pd.isnull(row['citation']):
            citationparts = row['citation'].split()
            if len(citationparts) > 0 and wordcountregex.fullmatch(citationparts[-1]):
                thesewords = makeint(citationparts[-1])
                if thesewords < 3000:
                    wcount = thesewords
                else:
                    wcount = 3000
                    # we impose a cap on super-long reviews because I'm skeptical
            else:
                wcount = float('nan')

        if not pd.isnull(wcount):
            bookmatrix[winner][matrix_index] = wcount
            wordcounts[winner].append(wcount)

with open('publicationstats.tsv', mode = 'w', encoding = 'utf-8') as f:
    f.write('pubname\twcount\tnumrevs\n')

for p in pubs:
    if p == 'other pubs' or len(wordcounts[p]) < 2:
        continue
    print(p)
    wcount = round(np.nanmean(wordcounts[p]), 1)
    print(wcount)
    numrevs = len(wordcounts[p])
    print(numrevs)
    print()
    with open('publicationstats.tsv', mode = 'a', encoding = 'utf-8') as f:
        f.write(p + '\t' + str(wcount) + '\t' + str(numrevs) + '\n')

bigpubs = ['sentiment', 'price', 'bestsellers', 'prizelists']

for p in pubs:
    if sum(bookmatrix[p]) > 50000:
        bigpubs.append(p)

with open('bookmatrix.tsv', mode = 'w', encoding = 'utf-8') as f:
    f.write('\t'.join([x.replace(' ', '').replace('.', '') for x in bigpubs]) + '\n')
    for i in range(len(bookrange)):
        outlist = [str(bookmatrix[x][i]) for x in bigpubs]
        outrow = '\t'.join(outlist) + '\n'
        f.write(outrow)











