# -*- coding: utf-8 -*-
# publisher_analysis.py
# Ted Underwood, Jan 2020

# This script is based on ../analysis/aggregate_publishers.py
# It differs in covering more than one year, and in considering
# the possibility that publishers' names will be misspelled or
# omitted from our master list.

import pandas as pd
import numpy as np
import glob
from collections import Counter
from difflib import SequenceMatcher
from scipy.stats import zscore

def get_ratio(stringA, stringB):

    m = SequenceMatcher(None, stringA, stringB)

    thefilter = m.real_quick_ratio()
    if thefilter < 0.5:
        return thefilter

    else:
        return m.ratio()

publishers = ['Appleton', 'Baker', 'Barnes', 'Benziger', 'Bobbs', "Brentano's", 'Cassell',
    'Century', 'Collier-Fox', 'Crowell', 'Ditson', 'Dodd', 'Doran', 'Doubleday', 'Dutton',
    'Elder', 'Estes', 'Ginn', 'Goodspeed', 'Harcourt', 'Harper', 'Heath', 'Holt', 'Houghton', 'Knopf',
    'Lane', 'Lippincott', 'Little', 'Liveright', 'Longmans', 'Macmillan', 'McBride', 'McClure', 'Morrow',
    'McGraw', 'Moffat', 'Oxford', 'Page', 'Pott', 'Putnam', 'Scribner', 'Simmons', 'Stokes', 'Viking',
    'Walton', 'Warne', 'Wessels', 'Wilde', 'Wiley', 'Winston', 'Yale', 'Farrar', 'Small', 'Macaulay', 'Cosmopolitan']

def compress_reviewdata(folderpath):
    '''
    Given a folder, this loads all the .tsv files, aggregates them at the book level, and
    concatenates the results.
    '''

    folderpaths = glob.glob(folderpath + '*.tsv')

    bookframes = []

    for fpath in folderpaths:
        filename = fpath.split('/')[-1]
        year = int(fpath.replace('.tsv', '')[-4:])
        reviewdf = pd.read_csv(fpath, sep = '\t')
        bookdf = reviewdf.groupby('bookindex').first().reset_index()
        bookdf = bookdf.assign(volyear = year)

        prices = np.array(bookdf['price'])
        nonzeroprices = np.nonzero(prices)
        nonzeroprices = prices[nonzeroprices]
        pricemean = np.mean(nonzeroprices)
        prices[prices == 0] = pricemean
        zprices = zscore(prices)

        bookdf = bookdf.assign(normedprice = zprices)

        bookframes.append(bookdf)

    masterframe = pd.concat(bookframes)
    print(masterframe.shape)

    return masterframe

pulitzerwinners = {'FERBER, EDNA.', 'WHARTON, MRS EDITH NEWBOLD (JONES).', 'TARKINGTON, BOOTH.',
    'CATHER, WILLA SIBERT.', 'LEWIS, SINCLAIR.', 'BROMFIELD, LOUIS.', 'WILDER, THORNTON NIVEN.',
    'PETERKIN, JULIA E. (MRS CHARLES P. PETERKIN).', 'WILSON, MARGARET.'}

pubdata = dict()
pubdata['pulitzer'] = dict()
pubdata['pulitzer']['sentiment'] = []
pubdata['pulitzer']['wordcount'] = []
pubdata['pulitzer']['price'] = []
pubdata['pulitzer']['numreviews'] = []

pubdata['bestsellers'] = dict()
pubdata['bestsellers']['sentiment'] = []
pubdata['bestsellers']['wordcount'] = []
pubdata['bestsellers']['price'] = []
pubdata['bestsellers']['numreviews'] = []

bestseller_df = pd.read_csv('bestsellers.tsv', sep = '\t')
bestsellers = set()
for idx, row in bestseller_df.iterrows():
    bestsellers.add((row['bookauthor'], row['booktitle']))

df = compress_reviewdata('../../downloads/release1/')
alienpublishers = Counter()

for idx, row in df.iterrows():
    thispublisher = 'unknown'

    for p in publishers:
        if not pd.isnull(row['publisher']) and p in row['publisher']:
            thispublisher = p
            break

    if not pd.isnull(row['publisher']) and thispublisher == 'unknown':
        pubwords = row['publisher'].split()
        for w in pubwords:
            if len(w) > 4:
                for p in publishers:
                    ratio = get_ratio(w, p)
                    if ratio > 0.8:
                        thispublisher = p
                        break

    if not pd.isnull(row['publisher']) and thispublisher == 'unknown':
        for w in pubwords:
            alienpublishers[w] += 1

    p = thispublisher
    if p not in pubdata:
        pubdata[p] = dict()
        pubdata[p]['sentiment'] = []
        pubdata[p]['wordcount'] = []
        pubdata[p]['price'] = []
        pubdata[p]['numreviews'] = []
    pubdata[p]['sentiment'].append(row['avgsentiment'])
    pubdata[p]['price'].append(row['normedprice'])
    pubdata[p]['wordcount'].append(row['wordcount'])
    pubdata[p]['numreviews'].append(row['numreviewsofbk'])

    if row['bookauthor'] in pulitzerwinners:
        pubdata['pulitzer']['sentiment'].append(row['avgsentiment'])
        pubdata['pulitzer']['price'].append(row['normedprice'])
        pubdata['pulitzer']['wordcount'].append(row['wordcount'])
        pubdata['pulitzer']['numreviews'].append(row['numreviewsofbk'])

    key = (row['bookauthor'], row['booktitle'])
    if key in bestsellers:
        pubdata['bestsellers']['sentiment'].append(row['avgsentiment'])
        pubdata['bestsellers']['price'].append(row['normedprice'])
        pubdata['bestsellers']['wordcount'].append(row['wordcount'])
        pubdata['bestsellers']['numreviews'].append(row['numreviewsofbk'])

with open('publishers.tsv', mode = 'w', encoding = 'utf-8') as f:
    f.write('publisher\twordcount\tprice\tsentiment\tnumreviews\tnumbooks\n')
    for p, data in pubdata.items():
        sentiment = np.median(np.array(data['sentiment']))
        wordcount = np.median(np.array(data['wordcount']))
        prices = np.array(data['price'])
        nonzeroprices = np.nonzero(prices)
        nonzeroprices = prices[nonzeroprices]
        price = np.median(nonzeroprices)
        numreviews = np.mean(data['numreviews'])
        numbooks = len(data['numreviews'])

        f.write(p + '\t' + str(wordcount) + '\t' + str(price) + '\t' + str(sentiment) + '\t' + str(numreviews) + '\t' + str(numbooks) + '\n')

df.to_csv('allbooks.tsv', sep = '\t', index = False)

with open('publisher_books.tsv', mode = 'w', encoding = 'utf-8') as f:
    f.write('publisher\twordcount\tprice\tsentiment\tnumreviews\n')
    for p, data in pubdata.items():
        if p == 'unknown':
            continue
        for i in range(len(data['sentiment'])):
            price = data['price'][i]
            wordcount = data['wordcount'][i]
            sentiment = data['sentiment'][i]
            numreviews = data['numreviews'][i]

            f.write(p + '\t' + str(wordcount) + '\t' + str(price) + '\t' + str(sentiment) + '\t' + str(numreviews) + '\n')
