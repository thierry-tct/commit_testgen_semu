#! /usr/bin/env python

from __future__ import print_function

import os, sys, json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

from numpy import median as np_median
from numpy import average as np_average
import numpy as np

###### Non Parametic Vargha Delaney A12 ######
# Taken from -- https://gist.github.com/timm/5630491

def a12(lst1,lst2,pairwise=False, rev=True):
    "how often is x in lst1 more than y in lst2?"
    more = same = 0.0
    for i,x in enumerate(lst1):
        second = [lst2[i]] if pairwise else lst2
        for y in second:
            if   x==y : same += 1
            elif rev     and x > y : more += 1
            elif not rev and x < y : more += 1
    return (more + 0.5*same) / (len(lst1) if pairwise else len(lst1)*len(lst2))

def wilcoxon(list1, list2, isranksum=True):
    if isranksum:
        p_value = scipy.stats.ranksums(list1, list2)
    else:
        p_value = scipy.stats.wilcoxon(list1, list2)
    return p_value
#~ def wilcoxon()

def loadJson (filename):
    with open(filename) as fp:
        return json.load(fp)
#~ def loadJson ()

def dumpJson (obj, filename, pretty=True):
    with open(filename, "w") as fp:
        if pretty:
            json.dump(obj, fp, indent=2, sort_keys=True)
        else:
            json.dump(obj, fp)
#~ dumpJson()

def plotBoxes(plotobj, order, imagefile, colors_bw, ylabel="APFD", yticks_range=range(0,101,20), fontsize=26, title=None):
    plt.figure(figsize=(16, 8))
    plt.gcf().subplots_adjust(bottom=0.27)
    #plt.style.use(u'ggplot')
    sns.set_style("ticks")
    #fontsize = 26
    plotobjList = [plotobj[t] for t in order]
    bp = plt.boxplot(plotobjList, labels=order, widths=0.75, patch_artist=True)
    medianValues = []
    for ind,box in enumerate(bp['boxes']):
        box.set(color='black')
        box.set(facecolor = colors_bw[ind])
    for ind,med in enumerate(bp['medians']):
        med.set(color='black', lw=4)
        medianValues.append(med.get_xydata()[1][1])
    for ind,wh in enumerate(bp['whiskers']):
        wh.set(color='black')
    for ind,wh in enumerate(bp['fliers']):
        wh.set(mew=2)
        
    plt.ylabel(ylabel, fontsize=fontsize)
    if len(plotobjList) > 2:
        plt.xticks(fontsize=fontsize, rotation=30, ha='right')
    else:
        plt.xticks(fontsize=fontsize) # do not rotate x ticks
    if yticks_range is not None:
        plt.yticks(yticks_range, fontsize=fontsize)
    else:
        plt.yticks(fontsize=fontsize)
    plt.tight_layout()
    ybot, ytop = plt.gca().get_ylim()
    ypad = (ytop - ybot) / 50
    #ypad = 2
    plt.gca().set_ylim(ybot - ypad, ytop + ypad)
    #sns_plot.set_title('APFD - '+allkonly)
    plt.savefig(imagefile+".pdf", format='pdf')
    plt.close('all')
    return medianValues
#~ def plotBoxes()

colors_bw = ['white', 'whitesmoke', 'lightgray', 'silver', 'darkgrey', 'gray', 'dimgrey', "black"]
colors = ["green", 'blue', 'red', "black", "maroon", "magenta", "cyan"]
linestyles = ['solid', 'solid', 'dashed', 'dashed', 'dashdot', 'dotted', 'solid']
linewidths = [1.75, 1.75, 2.5, 2.5, 3.25, 3.75, 2]
markers = ['o', 'x', '^', 's', '*', '+', 'H', 'v', 'p', 'd']

def plotTrend(name_to_data, image_file, xlabel, ylabel, yticks_range=np.arange(0,1.01,0.2), order=None):
    if order is None:
        order = list(name_to_data)

    # get median
    plotobj = {name: {'x':list(data.keys()), 'y':[y for _,y in data.items()]} for name, data in name_to_data.items()}

    plt.figure(figsize=(13, 9))
    plt.gcf().subplots_adjust(bottom=0.27)
    #plt.style.use(u'ggplot')
    #sns.set_style("ticks")
    sns.set_style("whitegrid")
    plt.rcParams["axes.edgecolor"] = "0.15"
    plt.rcParams["axes.linewidth"]  = 1.25
    #sns.set_context("talk")
    fontsize = 26
    maxlenx = max([len(plotobj[t]['x']) for t in order])
    for ti,tech in enumerate(order):
        plt.plot(plotobj[tech]['x'], plotobj[tech]['y'], color=colors[ti], linestyle=linestyles[ti], linewidth=linewidths[ti], marker=markers[ti], markersize=7.5, label=tech, alpha=0.8)
    plt.ylabel(ylabel, fontsize=fontsize)
    plt.xlabel(xlabel, fontsize=fontsize)
    step = 1 #int(min(maxx, 10))
    plt.xticks(list(range(1, maxlenx+1, step)), fontsize=fontsize-5)
    plt.yticks(yticks_range, fontsize=fontsize-5)
    legendMode=1 if len(order) <= 3 else 2
    if legendMode==1:
        lgd = plt.legend(bbox_to_anchor=(0., 0.98, 1., .102), loc=2, ncol=3, mode="expand", fontsize=fontsize-5, borderaxespad=0.)
    elif legendMode==2:
        lgd = plt.legend(bbox_to_anchor=(0., 0.98, 1.02, .152), loc=2, ncol=3, mode="expand", fontsize=fontsize-5, borderaxespad=0.)
    else:
        assert False, "invalid legend mode (expect either 1 or 2)"
    #plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.00), shadow=True, ncol=3)
    #sns_plot.set_title('APFD - '+allkonly)
    plt.tight_layout()
    ybot, ytop = plt.gca().get_ylim()
    ypad = (ytop - ybot) / 50
    #ypad = 2
    plt.gca().set_ylim(ybot - ypad, ytop + ypad)
    plt.savefig(image_file+".pdf", format='pdf', bbox_extra_artists=(lgd,), bbox_inches='tight')
    plt.close('all')
#~ def plotTrend()

def main():
    assert len(sys.argv) == 2
    input_topdir = sys.argv[1]
    outdir = os.path.join(input_topdir, "OUTPUT")
    
    # load data
    id2rMSobj = {}
    for d in os.listdir(input_topdir):
        if not os.path.isdir(d) or d == "OUTPUT":
            continue
        # load data
        filename = os.path.join(input_topdir, d, 'rMS.json')
        id2rMSobj[d] = loadJson(filename)
    
    if not os.path.isdir(outdir):
        os.mkdir(outdir)
        
    # For each category, get id to rMS
    all_all_alias2rMSlist = {}
    additional_alias2rMSlist = {}
    all_genonly_alias2rMSlist = {}
    for resdict, key in [(all_all_alias2rMSlist, "ALL-ALL"), \
                         (all_genonly_alias2rMSlist, "ALL-GENONLY"), \
                         (additional_alias2rMSlist, "ADDITIONAL")]:
        for d_id, rMSobj in id2rMSobj.items():
            for alias, val in rMSobj[key].items():
                if alias not in resdict:
                    resdict[alias] = []
                resdict[alias].append(val)
    
        # Plotting
        resdict_omb = {k.replace("_cmp", "").replace("_se", ""):v for k,v in resdict.items() if ('semu' not in k or 'omb' in k)}
        resdict_non_omb = {k.replace("_cmp", "").replace("_se", ""):v for k,v in resdict.items() if ('semu' not in k or 'omb' not in k)}
        for omb, data_dict in [("", resdict_non_omb), ("-omb", resdict_omb)]:
            boxplotfile = os.path.join(outdir, key+"-boxplot"+omb)
            linesplotfile = os.path.join(outdir, key+"-lineplot"+omb)
            plotBoxes(data_dict, sorted(list(data_dict)), boxplotfile, ['white']*20, ylabel="Relevant Mutation Score", yticks_range=range(0,101,10), fontsize=26, title=None)
            
            trend_data = {}
            shadow_key = None
            for k in data_dict:
                if k.startswith('shadow'):
                    assert shadow_key is None
                    shadow_key = k
            rank = list(range(len(data_dict[shadow_key])))
            rank.sort(key=lambda x: max([data_dict[k][x] - data_dict[shadow_key][x] for k in set(data_dict) - {shadow_key}]))
            rank = {pos: newpos for newpos, pos in enumerate(rank)}
            for alias, arr in data_dict.items():
                trend_data[alias] = {}
                for pos, val in enumerate(arr):
                    trend_data[alias][rank[pos] + 1] = val
            plotTrend(trend_data, linesplotfile, xlabel="Commit", ylabel="Relevant Mutation Score", yticks_range=range(0,101,10), order=sorted(list(data_dict))) 
    
    print("# DONE!")
#~ def main()

if __name__ == "__main__":
    main()
