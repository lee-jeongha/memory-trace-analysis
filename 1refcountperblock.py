# -*- coding: utf-8 -*-

import argparse
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from load_and_save import save_csv
from plot_graph import plot_frame
import math


"""##**memdf1 = access count**
* x axis : (virtual) memory block address
* y axis : memory block access count
"""
def ref_cnt(inputdf, concat=False):
    if (concat):
        df = inputdf.groupby(by=['blockaddress', 'type'], as_index=False).sum()
        #print(df)
        return df

    else:
        type_cnt = inputdf['type'].value_counts()

        inputdf = inputdf.replace('readi', 'read')
        inputdf = inputdf.replace('readd', 'read')

        df = inputdf.groupby(['blockaddress', 'type'])['blockaddress'].count().reset_index(name='count') # Count rows based on 'blockaddress' & 'type', And name as 'count'

        return df, type_cnt['readi'], type_cnt['readd'], type_cnt['write']

def ref_cnt_per_block(input_filename, chunks=100):
    ## 1. use list of chunk
    """
    memdf = pd.read_csv(input_filename+'.csv', sep=',', chunksize=1000000, header=0, index_col=0, error_bad_lines=False)
    memdf = list(memdf)
    #---
    df1 = pd.DataFrame()
    for i in range(len(memdf)):
        memdf = pd.read_csv(memdf[i], sep=',', header=0, index_col=0, error_bad_lines=False)
        df = address_ref(memdf, concat=False)
        df1 = pd.concat([df1, df])
    """

    ## 2. load separate .csv file
    memdf = pd.DataFrame()
    readi_cnt = 0; readd_cnt = 0; write_cnt = 0

    for i in range(chunks): 
        filename = input_filename+'_'+str(i)+'.csv'

        try:
            df = pd.read_csv(filename, sep=',', header=0, index_col=0, on_bad_lines='skip')
            memdf_chunk, readi_cnt_chunk, readd_cnt_chunk, write_cnt_chunk = ref_cnt(df, concat=False)
            memdf = pd.concat([memdf, memdf_chunk])

            readi_cnt += readi_cnt_chunk;   readd_cnt += readd_cnt_chunk;   write_cnt += write_cnt_chunk

        except FileNotFoundError:
            print("No file named: ", filename)
            break

    memdf = ref_cnt(memdf, concat=True)

    # both read and write
    memdf_rw = memdf.groupby(by=['blockaddress'], as_index=False).sum()
    memdf_rw['type'] = 'read&write'

    memdf = pd.concat([memdf, memdf_rw], sort=True)

    memdf['readi'] = pd.Series([readi_cnt])
    memdf['readd'] = pd.Series([readd_cnt])
    memdf['write'] = pd.Series([write_cnt])

    return memdf

"""**memdf1 graph**"""
def digit_length(n):
    return int(math.log10(n)) + 1 if n else 0

def hist_label(subplot, counts, bars, round_range=0, rotation=90):
    if round_range:
        counts = np.round(counts, round_range)
    else:
        counts = [int(i) for i in counts]
    for idx,rect in enumerate(bars):
        height = rect.get_height()
        subplot.text(rect.get_x() + rect.get_width()/3.25, 0.4*height,
                counts[idx], fontsize=15,
                ha='center', va='bottom', rotation=rotation)

"""memdf1.0 graph"""
def instruction_cnt_graph(title, filename, readi_cnt, readd_cnt, write_cnt):
    x = range(3)
    x_label = ['readi', 'readd', 'write']
    values = [readi_cnt, readd_cnt, write_cnt]
    colors = ['dodgerblue', 'c', 'red']
    handles = [plt.Rectangle((0,0),1,1, color=colors[i]) for i in range(3)]

    cnt_sum = readi_cnt + readd_cnt + write_cnt
    percentile_values = np.divide(values, cnt_sum/100).round(3)

    fig, ax = plot_frame((1, 1), title=title, xlabel='instruction type', ylabel='instruction count', share_yaxis='col')
    
    rects = plt.bar(x, values, color=colors)
    plt.xticks(x, x_label)
    plt.yticks([])
    plt.bar_label(rects, fontsize=20, fmt='%.0f')

    plt.legend(handles, [str(i)+'%' for i in percentile_values], fontsize=15)

    #plt.show()
    plt.savefig(filename+'_instruction.png', dpi=300)

"""memdf1.1 graph"""
def ref_cnt_graph(df, title, filename, ylim : list = None):
    x1 = df['blockaddress'][(df['type']=='read')]
    x2 = df['blockaddress'][(df['type']=='write')]
    x3 = df['blockaddress'][(df['type']=='read&write')]

    y1 = df['count'][(df['type']=='read')]
    y2 = df['count'][(df['type']=='write')]
    y3 = df['count'][(df['type']=='read&write')]

    print("memory footprint(4KB):", len(x3))
    print("memory footprint by reads(4KB):", len(x1))
    print("memory footprint by writes(4KB):", len(x2))

    fig, ax = plot_frame((3, 1), (7, 4), title=title, xlabel='(virtual) memory block address', ylabel='memory block reference count')
    x = [x1, x2, x3]
    y = [y1, y2, y3]
    color = ['blue', 'red', 'green']
    label = ['read', 'write', 'read&write']

    if ylim:
        plt.setp(ax, ylim=ylim)

    #print("read count[min,max]:", y1.min(), y1.max(), digit_length(y1.max()))
    #print("write count[min,max]:", y2.min(), y2.max(), digit_length(y2.max()))

    for i in range(len(x)):
        ax[i].scatter(x[i], y[i], color=color[i], label=label[i], s=3)
        ax[i].legend(loc='upper right', ncol=1, fontsize=20, markerscale=3) #loc = (1.0,0.8)

    #plt.show()
    plt.savefig(filename+'.png', dpi=300)

"""memdf1.2 graph"""
def ref_cnt_distribute_graph(df, title, filename, cnt_ylim : list = None, dist_ylim : list = None):
    y1 = df['count'][(df['type']=='read')]
    y2 = df['count'][(df['type']=='write')]
    y3 = df['count'][(df['type']=='read&write')]

    fig, ax = plot_frame((3, 2), title=title, xlabel='reference count', ylabel='# of memory block', font_size=40, share_yaxis='col')
    y = [y1, y2, y3]
    color = ['blue', 'red', 'green']
    label = ['read', 'write', 'read&write']

    plt.xscale('log')

    bin_list = [1]
    x_lim = max(y1.max(), y2.max(), y3.max())
    bin_list.extend([ 10**i + 1 for i in range(digit_length(x_lim) + 1) ])
    
    for i in range(len(y)):
        """histogram"""
        counts, edges, bars = ax[i][0].hist(y[i], bins=bin_list, density=False, rwidth=3, color=color[i], edgecolor='black', label=label[i])
        ax[i][0].legend(loc='upper right', ncol=1, fontsize=30)
        hist_label(ax[i][0], counts, bars)

        """normalized histogram"""
        counts, edges, bars = ax[i][1].hist(y[i], bins=bin_list, density=True, rwidth=3, color=color[i], edgecolor='black', label=label[i])
        ax[i][1].legend(loc='upper right', ncol=1, fontsize=30)
        hist_label(ax[i][1], counts, bars, 5)

    if cnt_ylim:
        ax[0][0].set_ylim(cnt_ylim)
    if dist_ylim:
        ax[0][1].set_ylim(dist_ylim)

    #plt.show()
    plt.savefig(filename+'_hist.png', dpi=300)

def ref_cnt_distribute(ref_count, filename='output', log_scale=False):
    if not log_scale:
        bin_list = ref_count.unique()
        bin_list = np.append(bin_list, bin_list.max()+1)
        bin_list = np.sort(bin_list)
  
    counts, edges = np.histogram(ref_count, bins=bin_list, density=False)
    relative_counts, edges = np.histogram(ref_count, bins=bin_list, density=True)
    
    counts_list = list(counts)
    print(counts_list.index(counts.max()), counts.max())

    if not log_scale:
        df = pd.DataFrame()
        df['edges'] = edges[:-1]
        df['counts'] = counts
        df['multiply_counts'] = df['edges'] * df['counts']
        df['relative_counts'] = relative_counts
        #df.to_csv('distributes.csv')

    return edges[:-1], counts, df['multiply_counts'].to_numpy(), relative_counts

def ref_cnt_distribute_graph_linear(df, title, filename):
    y1 = df['count'][(df['type']=='read')]
    y2 = df['count'][(df['type']=='write')]
    y3 = df['count'][(df['type']=='read&write')]

    fig, ax = plot_frame((3, 3), title=title, xlabel='reference count', ylabel='# of memory block', font_size=40, share_yaxis='col')
    y = [y1, y2, y3]
    color = ['blue', 'red', 'green']
    label = ['read', 'write', 'read&write']

    for i in range(3):
        edges, counts, multiply_counts, relative_counts = ref_cnt_distribute(y[i], log_scale=False)

        # read&write graph
        ax[i][0].bar(edges, counts, color=color[i], edgecolor=color[i], label=label[i])
        ax[i][1].bar(edges, multiply_counts, color=color[i], edgecolor=color[i], label=label[i])
        ax[i][2].bar(edges, relative_counts, color=color[i], edgecolor=color[i], label=label[i])
    
        ax[i][0].legend(loc='upper right', ncol=1, fontsize=20)
        ax[i][1].legend(loc='upper right', ncol=1, fontsize=20)
        ax[i][2].legend(loc='upper right', ncol=1, fontsize=20)
    
    #plt.show()
    plt.savefig(filename+'_hist.png', dpi=300)

#-----
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="plot reference count per each block")
    parser.add_argument("--input", "-i", metavar='I', type=str, nargs='?', default='input.txt',
                        help='input file')
    parser.add_argument("--output", "-o", metavar='O', type=str, nargs='?', default='output.txt',
                        help='output file')
    parser.add_argument("--chunk_count", "-c", metavar='C', type=int, nargs='?', default=100,
                        help='the number of chunk groups')
    parser.add_argument("--plot_logcnt", "-l", action='store_true',
                        help='plot histogram by instruction type of log file')
    parser.add_argument("--plot_distribution", "-d", action='store_true',
                        help='plot histogram bound by reference count')
    parser.add_argument("--title", "-t", metavar='T', type=str, nargs='?', default='',
                        help='title of a graph')
    args = parser.parse_args()

    memdf1 = ref_cnt_per_block(input_filename=args.input, chunks=args.chunk_count)
    save_csv(memdf1, args.output+'.csv', 0)

    if (args.plot_logcnt):
        instruction_cnt_graph(title=args.title, filename=args.output, readi_cnt=memdf1.iloc[0, 3], readd_cnt=memdf1.iloc[0, 4], write_cnt=memdf1.iloc[0, 5])

    #memdf1 = pd.read_csv(args.output+'.csv', sep=',', header=0, index_col=0, on_bad_lines='skip')
    ref_cnt_graph(memdf1, title=args.title, filename=args.output)

    if (args.plot_distribution):
        plt.clf() # Clear the current figure
        ref_cnt_distribute_graph(memdf1, title=args.title, filename=args.output)
        ref_cnt_distribute_graph_linear(memdf1, title=args.title, filename=args.output)
