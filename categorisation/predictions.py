"""
Contains methods for each device that we have models for that predict category names from these models
"""
import os, json, pickle
import pandas as pd
import numpy as np
from ipwhois import IPWhois
from collections import defaultdict

FILE_PATH = os.path.dirname(os.path.abspath(__file__))
#FEATURES_FILE = os.path.join(FILE_PATH, "data", "FlowFeatures.csv")

NUMBER_COLUMNS = 56     # Columns used in feature vectors for NN prediction
with open(os.path.join(FILE_PATH, 'dicts.json'), 'r') as f:
    FLOW_NUMBER_CUTOFF = json.load(f)["EchoFlowNumberCutoff"] # Number of packets required for a valid flow

HOME_IP = "192.168"



def normaliseColumn(array, colNo):
    """
    Min-max normalise data in array (a N * 54 shape) w.r.t. max/min in FEATURES_FILE
    """
    df = pd.read_csv(FEATURES_FILE, usecols = [x for x in range(2,NUMBER_COLUMNS)], header=None)

    values = array[:, colNo]
    normalized = (values - df.iloc[:,colNo].min()) / (df.iloc[:,colNo].max() - df.iloc[:,colNo].min() + 0.000000000000000001) # pylint: disable=maybe-no-member

    array[:, colNo] = normalized
    #print(array)
    return array

def getIps(rows):
    """ Get a list of IP src/dest pairs out of a burst """
    srcdest = set()

    for row in rows:
        source = row[2]
        destination = row[3]
        srcdest.add((source, destination))
        
    srcdest = list(srcdest)
    return srcdest
    

def getExtIpsCount(rows):
    """ Get a dictionary of external IPs out of a burst with their frequency"""
    ips = defaultdict(int)

    for row in rows:
        source = row[2]
        destination = row[3]
        if HOME_IP not in source:
            ips[source] += 1
        if HOME_IP not in destination:
            ips[destination] += 1
    
    return ips

def getFlowDict(sourcedest, burst):
    """
    Get a dictionary of lists of lengths of packets in the burst
    Keys are the souce-destination pairs of IP addresses
    """
    flowDict = {}

    for pair in sourcedest:
        flowLens = []
        source = pair[0]
        dest = pair[1]

        for row in burst:
            if row[2] == source and row[3] == dest:
                flowLens.append(int(row[5]))
                
        flowDict[pair] = (flowLens)
    
    return flowDict

def getStatistics(listInts):
    """
    Get 18 statistical features out of a list of integers
    """
    result = []
    df = pd.DataFrame()
    df['data'] = listInts

    result.append(df['data'].min())
    result.append(df['data'].max())
    result.append(df['data'].mean())
    result.append(df['data'].mad())
    result.append(df['data'].std())
    result.append(df['data'].var())
    result.append(df['data'].skew())
    result.append(df['data'].kurtosis())
    for value in [0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9]:
        result.append(df['data'].quantile(q=value))
    result.append(len(listInts))

    return result

def getStatisticsFromDict(sourceDest, lengthDict):
    """
    Get a list of 54 element lists
    Each sub-list is made up of three sets of 18 statistics
    These are generated from lengths of packets to, from, and both for each pair of IPs
    """
    result = []
    done = []
    for pair in sourceDest:
        if pair not in done and ((pair[1], pair[0])) in sourceDest:
            if len(lengthDict[pair])>2 and \
                len(lengthDict[(pair[1], pair[0])]) > 2 and \
                len(lengthDict[(pair[1], pair[0])]) + len(lengthDict[pair]) > FLOW_NUMBER_CUTOFF:

                res = getStatistics(lengthDict[pair])
                res2 = getStatistics(lengthDict[(pair[1], pair[0])])
                res3 = getStatistics(lengthDict[pair] + lengthDict[(pair[1], pair[0])])

                done.append((pair[1], pair[0]))

                row = []

                # Ensure data is added in the following order: OUT / IN / BOTH
                if HOME_IP in pair[0]:
                    row.extend(res)
                    row.extend(res2)
                else:
                    row.extend(res2)
                    row.extend(res)
                row.extend(res3)

                result.append(row)

    return result

def addBiases(data):
    """ Adds a column of 1s to data"""
    N, M  = data.shape
    all_X = np.ones((N, M + 1))
    all_X[:, 1:] = data
    return all_X

def getCategoryFromModel(flowStatistics):
    """
    This needs significant re-working depending on what models we use
    """
    data = np.array(flowStatistics, dtype='float32')

    weights1 = np.load(os.path.join(FILE_PATH, "echoModel", "echoPCAweights1.npy"))
    weights2 = np.load(os.path.join(FILE_PATH, "echoModel", "echoPCAweights2.npy"))

    pca = pickle.load( open( os.path.join(FILE_PATH, "echoModel", "echoPCA.p"), "rb" ) )
    preScaler = pickle.load( open( os.path.join(FILE_PATH, "echoModel", "preScaler.p"), "rb" ) )
    postScaler = pickle.load( open( os.path.join(FILE_PATH, "echoModel", "postScaler.p"), "rb" ) )

    normalized = preScaler.transform(data)
    principal = pca.transform(normalized)
    principalNormalized = postScaler.transform(principal)

    all_X = addBiases(principalNormalized)

    hiddenPre = np.matmul(all_X, weights1)
    hiddenPost = np.maximum(hiddenPre, 0)   # pylint: disable=maybe-no-member
    output = np.matmul(hiddenPost, weights2)
    #print(output)

    category = np.argmax(output)

    categoryNames = {1: "Time", 2: "Weather", 3: "Joke", 4: "Song Author", 5: "Conversion", 6: "Day of week", 7: "Timer", 8: "Shopping", 9: "Lights", 10: "Alarms"}
    try:
        result = categoryNames[category]
        return result
    except KeyError:
        return "Unknown"

class Predictor():
    
    def __init__(self):
        with open(os.path.join(FILE_PATH, 'dicts.json'), 'r') as f:
            self.config = json.load(f)
            self.ipDict = self.config["ipDests"]
        
        
    def predictEcho(self, rows):
        """ Given rows of data from a burst from packets table, predict an Echo category"""

        # Get all IP sources and dests
        srcdest = getIps(rows)

        # Get lengths of flows
        flowLengths = getFlowDict(srcdest, rows)

        # Get statistics for each flow
        flowStatistics = getStatisticsFromDict(srcdest, flowLengths )

        # Predict the category
        category = getCategoryFromModel(flowStatistics)

        return category

    def predictHue(self, rows):
        """ TODO: Given rows of data from a burst from packets table, predict a Hue category"""

        return self.predictOther(rows)

    def predictOther(self, rows):
        """ Given rows from a burst with no model, display category as majority destination"""

        percentCutoff = 0.8

        # Of the form {ip: number of times destination in burst}
        ext = getExtIpsCount(rows)

        total = sum(ext.values())

        for key in ext.keys():
            if ext[key]*1.0 / total*1.0 > percentCutoff:
                try:
                    result = self.ipDict[key]
                except KeyError:
                    try:
                        domainObj = IPWhois(key)
                        domainRes = domainObj.lookup_whois()
                        domain = domainRes['nets'][0]['description']
                        if len(domain) > 20:
                            domain = domain[:20]
                        self.ipDict[key] = "Mostly " + domain
                        return "Mostly " + domain
                    except:
                        self.ipDict[key] = "Unknown"
                        return "Unknown"
        return "Unknown"

    def saveIpDict(self):
        self.config["ipDests"] = self.ipDict
        with open(os.path.join(FILE_PATH, 'dicts.json'), 'w') as f:
            json.dump(self.config, f, sort_keys=True, indent=4)

