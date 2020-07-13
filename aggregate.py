#! /usr/bin/env python

from __future__ import print_function

import os, sys, json
import argparse

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

from numpy import median as np_median
from numpy import average as np_average
import numpy as np
import pandas as pd

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

colors_bw = ['white', 'whitesmoke', 'lightgray', 'silver', 'darkgrey', 'gray', 'dimgrey', "black"] * 2
colors = ["green", 'blue', 'red', "black", "maroon", "magenta", "cyan"] * 2
linestyles = ['solid', 'solid', 'dashed', 'dashed', 'dashdot', 'dotted', 'solid'] * 2
linewidths = [1.75, 1.75, 2.5, 2.5, 3.25, 3.75, 2] * 2
markers = ['o', 'x', '^', 's', '*', '+', 'H', 'v', 'p', 'd'] * 2

def plotTrend(name_to_data, image_file, xlabel, ylabel, yticks_range=np.arange(0,1.01,0.2), order=None):
    if order is None:
        order = list(name_to_data)

    # get median
    plotobj = {}
    for name, data in name_to_data.items():
        plotobj[name] = {'x': [], 'y': []}
        for x, y in sorted(data.items(), key=lambda v: v[0]):
            plotobj[name]['x'].append(x)
            plotobj[name]['y'].append(y)

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
    if len(order) <= 3:
        legendMode = 1
    elif len(order) <= 6:
        legendMode = 2
    else:
        legendMode = 3
    if legendMode==1:
        lgd = plt.legend(bbox_to_anchor=(0., 0.98, 1., .102), loc=2, ncol=3, mode="expand", fontsize=fontsize-5, borderaxespad=0.)
    elif legendMode==2:
        lgd = plt.legend(bbox_to_anchor=(0., 0.98, 1.02, .152), loc=2, ncol=3, mode="expand", fontsize=fontsize-5, borderaxespad=0.)
    elif legendMode==3:
        lgd = plt.legend(bbox_to_anchor=(0., 0.98, 1.02, .282), loc=2, ncol=3, mode="expand", fontsize=fontsize-5, borderaxespad=0.)
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

def plotHeatmap(dataframe, xcol, ycol, datcol, outfile):
    pivot_data = dataframe.pivot(ycol, xcol, datcol)
    plt.figure(figsize=(13, 9))
    plt.gcf().subplots_adjust(bottom=0.27)
    sns.set(font_scale = 0.85)
    ax = sns.heatmap(pivot_data, annot=True, annot_kws={"fontsize":8}, fmt="d", linewidths=.5, cmap="YlGnBu")
    plt.savefig(outfile+".pdf", format='pdf', bbox_inches='tight')
    plt.close('all')
#~ def plotHeatmap()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_topdir", help="topdir containing the data. The output will also be there")
    parser.add_argument("--is_testgen_only", action="store_true", help="enable case of tg_only")
    parser.add_argument("--max_time", type=int, default=2*3600, help="Max test generation time")
    args = parser.parse_args()
    input_topdir = args.input_topdir
    outdir = os.path.join(input_topdir, "OUTPUT")
    is_testgen_only = args.is_testgen_only
    max_time = args.max_time
    
    if not os.path.isdir(outdir):
        os.mkdir(outdir)
        
    if is_testgen_only:
        # load data
        id2test2time = {}
        id2bugtests = {}
        id2difftests = {}
        seen_max_time_sec = 0
        time_set = set()
        for d in os.listdir(input_topdir):
            if not os.path.isdir(d) or d == "OUTPUT":
                continue
            # load data
            test2time_file = os.path.join(input_topdir, d, 'test_to_timestamp.json')
            test2time_obj = loadJson(test2time_file)
            for test, time_stamp in test2time_obj.items():
                time_stamp = int(round(time_stamp))
                seen_max_time_sec = max(seen_max_time_sec, time_stamp)
                if time_stamp <= max_time:
                    time_set.add(time_stamp)
            for b_id in os.listdir(os.path.join(input_topdir,d)):
                if not os.path.isdir(os.path.join(input_topdir,d, b_id)):
                    continue
                id2test2time[b_id] = dict(test2time_obj)
                
                fr_file = os.path.join(input_topdir, d, b_id, "fail_test_checking", "fault_reveling_tests.txt")
                diff_file = os.path.join(input_topdir, d, b_id, "diff_test_checking", "diff_reveling_tests.txt")
                elems = [(fr_file, id2bugtests)]
                if os.path.isfile(diff_file):
                    elems.append((diff_file, id2difftests))
                for _file, i2t in elems:
                    i2t[b_id] = set()
                    with open(_file) as f:
                        for ft in f:
                            i2t[b_id].add(ft.strip())
                
        if seen_max_time_sec > max_time:
            print("# WARNING: seen max time higher than max time ({} VS {})".format(seen_max_time_sec, max_time))
            
        if True:
            # Sample time sec
            time_set = np.linspace(0, max(time_set), num=100)
            
        # compute FD per time
        nbugs = len(id2bugtests)
        ndiffs = len(id2difftests)
        tech2time2fd = {}
        for b_id, test2time in id2test2time.items():
            techs_finding_bug = set()
            for test, time_sec in test2time.items():
                tech, raw_test = test.split(':')
                tech = tech.replace("_cmp", "")
                if tech in techs_finding_bug:
                    # count bug once
                    continue
                if tech not in tech2time2fd:
                    tech2time2fd[tech] = {t: 0 for t in time_set}
                time_sec = int(round(time_sec))
                if time_sec > max_time:
                    continue
                if test in id2bugtests[b_id]:
                    techs_finding_bug.add(tech)
                    for t in time_set:
                        if t >= time_sec:
                            tech2time2fd[tech][t] += 1 
                    
        normalize = True
        
        if not normalize:
            yticks_range = range(0, nbugs, 2)
            ylabel = "Number of Faults Revealed"
        else:
            for tech in tech2time2fd:
                for time_sec in tech2time2fd[tech]:
                    tech2time2fd[tech][time_sec] = tech2time2fd[tech][time_sec] *1.0 / nbugs
            yticks_range = range(0, 1.01, 10)
            ylabel = "Fault Revelation"
                
        # plot Trend
        linesplotfile = os.path.join(outdir, "lineplot")
        plotTrend(tech2time2fd, linesplotfile, xlabel="ellapsed time (s)", ylabel=ylabel, yticks_range=yticks_range, order=sorted(list(tech2time2fd)))
        
        # XXX: Update id2test2time by setting the time of tests without time to the maximum available value
        for b_id, test_set in list(id2bugtests.items()) + list(id2difftests.items()):
            for test in test_set:
                if test not in id2test2time[b_id]:
                    id2test2time[b_id][test] = seen_max_time_sec
        
        # Compute heatmap data
        fr_tech2id2tests = {}
        diff_tech2id2tests = {}
        for metric, data, tech2id2tests in [("FR", id2bugtests, fr_tech2id2tests), ("Differences", id2difftests, diff_tech2id2tests)]:
            heatmap_file = os.path.join(outdir, "heatmap-"+metric)
            # construct dataframe (select the test generated before or at max_time)
            for b_id, test2time in id2test2time.items():
                if b_id not in data:
                    # diff do not have same as FR
                    continue
                for test, time_sec in test2time.items():
                    tech, raw_test = test.split(':')
                    tech = tech.replace("_cmp", "")
                    if tech not in tech2id2tests:
                        tech2id2tests[tech] = {b_id: []}
                    if b_id not in tech2id2tests[tech]:
                        tech2id2tests[tech][b_id] = []
                    time_sec = int(round(time_sec))
                    if time_sec > max_time:
                        continue
                    if test in data[b_id]:
                        tech2id2tests[tech][b_id].append(test)
                        
            for tech in tech2id2tests:
                for b_id in data:
                    if b_id not in tech2id2tests[tech]:
                        tech2id2tests[tech][b_id] = []
            # Get dataframes and plot
            heatmap_df = []
            for tech in tech2id2tests:
                for b_id in tech2id2tests[tech]:
                    heatmap_df.append({"Technique": tech, "ID": b_id, "#Tests": len(tech2id2tests[tech][b_id])})
            heatmap_df = pd.DataFrame(heatmap_df)
            plotHeatmap(heatmap_df, "ID", "Technique", "#Tests", heatmap_file)
    else:
        # load data
        id2rMSobj = {}
        for d in os.listdir(input_topdir):
            if not os.path.isdir(d) or d == "OUTPUT":
                continue
            # load data
            filename = os.path.join(input_topdir, d, 'rMS.json')
            id2rMSobj[d] = loadJson(filename)

        lp_pos_to_id = {}

        # For each category, get id to rMS
        all_all_alias2rMSlist = {}
        additional_alias2rMSlist = {}
        all_genonly_alias2rMSlist = {}
        for resdict, key in [(all_all_alias2rMSlist, "ALL-ALL"), \
                             (all_genonly_alias2rMSlist, "ALL-GENONLY"), \
                             (additional_alias2rMSlist, "ADDITIONAL")]:
            id_list = []
            for d_id, rMSobj in id2rMSobj.items():
                id_list.append(d_id)
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
                medvals = plotBoxes(data_dict, sorted(list(data_dict)), boxplotfile, ['white']*20, ylabel="Relevant Mutation Score", yticks_range=range(0,101,10), fontsize=26, title=None)
                dumpJson (medvals, boxplotfile+"-medians.json")
                trend_data = {}
                shadow_key = None
                for k in data_dict:
                    if k.startswith('shadow'):
                        assert shadow_key is None
                        shadow_key = k
                rank = list(range(len(data_dict[shadow_key])))
                rank.sort(key=lambda x: max([data_dict[k][x] - data_dict[shadow_key][x] for k in set(data_dict) - {shadow_key}]))
                rank = {pos: newpos for newpos, pos in enumerate(rank)}
                if key not in lp_pos_to_id:
                    lp_pos_to_id[key] = {}
                if omb not in lp_pos_to_id[key]:
                    lp_pos_to_id[key][omb] = {}
                for oldpos, newpos in rank.items():
                    lp_pos_to_id[key][omb][newpos] = id_list[oldpos]
                for alias, arr in data_dict.items():
                    trend_data[alias] = {}
                    for pos, val in enumerate(arr):
                        trend_data[alias][rank[pos] + 1] = val
                plotTrend(trend_data, linesplotfile, xlabel="Commit", ylabel="Relevant Mutation Score", yticks_range=range(0,101,10), order=sorted(list(data_dict))) 
                dumpJson (lp_pos_to_id[key][omb], linesplotfile+"-pos_to_id.json")
    print("# DONE!")
#~ def main()

if __name__ == "__main__":
    main()
