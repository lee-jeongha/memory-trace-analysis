# -*- coding: utf-8 -*-

import argparse
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import pandas as pd
import numpy as np
from load_and_save import save_csv
from plot_graph import plot_frame


"""memdf2.1
* x axis : ranking by references count
* y axis : reference count
"""
def ref_count_rank(df):
    # ranking
    read_rank = df['count'][(df['type']=='read')].rank(ascending=False)
    df.loc[(df['type']=='read'), ['type_rank']] = read_rank

    write_rank = df['count'][(df['type']=='write')].rank(ascending=False)
    df.loc[(df['type']=='write'), ['type_rank']] = write_rank

    rw_rank = df['count'][(df['type']=='read&write')].rank(ascending=False)
    df.loc[(df['type']=='read&write'), ['type_rank']] = rw_rank

    return df

"""memdf2.2
* x axis : ranking by % of reference count (in percentile form)
* y axis : % of reference count
"""
def ref_count_percentile_rank(df):
    total_read = df['count'][(df['type']=='read')].sum()
    total_write = df['count'][(df['type']=='write')].sum()
    total_rw = df['count'][(df['type']=='read&write')].sum()

    # percentage
    df['type_pcnt'] = df['count']
    df.loc[(df['type']=='read'), ['type_pcnt']] /= total_read
    df.loc[(df['type']=='write'), ['type_pcnt']] /= total_write
    df.loc[(df['type']=='read&write'), ['type_pcnt']] /= total_rw

    # ranking in percentile form
    read_rank = df['type_pcnt'][(df['type']=='read')].rank(ascending=False, pct=True)
    df.loc[(df['type']=='read'), ['type_pcnt_rank']] = read_rank

    write_rank = df['type_pcnt'][(df['type']=='write')].rank(ascending=False, pct=True)
    df.loc[(df['type']=='write'), ['type_pcnt_rank']] = write_rank

    rw_rank = df['type_pcnt'][(df['type']=='read&write')].rank(ascending=False, pct=True)
    df.loc[(df['type']=='read&write'), ['type_pcnt_rank']] = rw_rank

    return df

"""zipf"""
def func_powerlaw(x, m, c):
    return x ** m * c

def zipf_fitting(freqs):
    from scipy.optimize import curve_fit

    target_func = func_powerlaw

    freqs = freqs[freqs != 0]
    y = freqs.sort_values(ascending=False).to_numpy()
    x = np.array(range(1, len(y) + 1))

    popt, pcov = curve_fit(target_func, x, y, maxfev=2000)
    #print(popt)

    return popt

"""memdf2.1 graph"""
def popularity_graph(df, title, filname, xlim : list = None, ylim : list = None, zipf=False):
    #read
    x1 = df['type_rank'][(df['type']=='read')]
    y1 = df['count'][(df['type']=='read')]
    #write
    x2 = df['type_rank'][(df['type']=='write')]
    y2 = df['count'][(df['type']=='write')]
    #read&write
    x3 = df['type_rank'][(df['type']=='read&write')]
    y3 = df['count'][(df['type']=='read&write')]

    if zipf:
        fig, ax = plot_frame((1, 1), title=title, xlabel='ranking', ylabel='memory block access count', log_scale=True)

        if xlim:
            plt.setp(ax, xlim=xlim)
        if ylim:
            plt.setp(ax, ylim=ylim)

        #scatter
        ax.scatter(x1, y1, color='blue', label='read', s=3)
        ax.scatter(x2, y2, color='red', label='write', s=3)
        ax.scatter(x3, y3, color='green', label='read&write', s=3)

        #curve fitting
        s_best1 = zipf_fitting(y1)
        s_best2 = zipf_fitting(y2)
        s_best3 = zipf_fitting(y3)
        ax.plot(x1, func_powerlaw(x1, *s_best1), color="skyblue", lw=2, label="curve_fitting: read")
        ax.plot(x2, func_powerlaw(x2, *s_best2), color="salmon", lw=2, label="curve_fitting: write")
        ax.plot(x3, func_powerlaw(x3, *s_best3), color="limegreen", lw=2, label="curve_fitting: read&write")
  
        """ax.annotate(str(round(s_best1[0],5)), xy=(10, func_powerlaw(10, *s_best1)), xycoords='data',
                     xytext=(-10.0, -70.0), textcoords="offset points", color="steelblue", size=13,
                     arrowprops=dict(arrowstyle="->", ls="--", color="steelblue", connectionstyle="arc3,rad=-0.2"))
        ax.annotate(str(round(s_best2[0],5)), xy=(80, func_powerlaw(80, *s_best2)), xycoords='data',
                     xytext=(-80.0, -30.0), textcoords="offset points", color="indianred", size=13,  # xytext=(-30.0, -50.0)
                     arrowprops=dict(arrowstyle="->", ls="--", color="indianred", connectionstyle="arc3,rad=-0.2"))
        ax.annotate(str(round(s_best3[0],5)), xy=(100, func_powerlaw(100, *s_best3)), xycoords='data',
                     xytext=(-10.0, -50.0), textcoords="offset points", color="olivedrab", size=13,  # xytext=(-80.0, -50.0)
                     arrowprops=dict(arrowstyle="->", ls="--", color="olivedrab", connectionstyle="arc3,rad=-0.2"))"""
        print(s_best1, s_best2, s_best3)

        # legend
        ax.legend(loc='lower left', ncol=1, fontsize=15, markerscale=3)

    else:
        fig, ax = plot_frame((2, 1), title=title, xlabel='ranking', ylabel='memory block access count', log_scale=True)

        if xlim:
            plt.setp(ax, xlim=xlim)
        if ylim:
            plt.setp(ax, ylim=ylim)

        # read/write graph
        ax[0].scatter(x1, y1, color='blue', label='read', s=3)
        ax[0].scatter(x2, y2, color='red', label='write', s=3)
        ax[0].legend(loc='lower left', ncol=1, fontsize=20, markerscale=3)

        # read+write graph
        ax[1].scatter(x3, y3, color='green', label='read&write', s=3)
        ax[1].legend(loc='lower left', ncol=1, fontsize=20, markerscale=3)

    #plt.show()
    plt.savefig(filname+'.png', dpi=300)


"""memdf2.2 graph"""
def pareto_graph(df, title, filname):
    fig, ax = plot_frame((1, 1), title=title, xlabel='rank (in % form)', ylabel='% of reference count')

    ax.grid(True, color='black', alpha=0.5, linestyle='--')

    #read
    y1 = df['type_pcnt'][(df['type']=='read')].sort_values(ascending=False).cumsum()
    x1 = np.arange(len(y1))
    x1 = (x1 / len(y1))
    #write
    y2 = df['type_pcnt'][(df['type']=='write')].sort_values(ascending=False).cumsum()
    x2 = np.arange(len(y2))
    x2 = (x2 / len(y2))
    #read&write
    y3 = df['type_pcnt'][(df['type']=='read&write')].sort_values(ascending=False).cumsum()
    x3 = np.arange(len(y3))
    x3 = (x3 / len(y3))

    y1_top20 = int(len(y1)*0.2);    y2_top20 = int(len(y2)*0.2);    y3_top20 = int(len(y3)*0.2)
    y1_list = y1.values.tolist();   y2_list = y2.values.tolist();   y3_list = y3.values.tolist()
    print(y1_list[y1_top20], y2_list[y2_top20], y3_list[y3_top20])

    #scatter
    ax.scatter(x1, y1, color='blue', label='read', s=3)
    ax.scatter(x2, y2, color='red', label='write', s=3)
    ax.scatter(x3, y3, color='green', label='read&write', s=3)

    # legend
    ax.legend(loc='lower right', ncol=1, fontsize=20, markerscale=3)
    
    ax.xaxis.set_major_locator(MaxNLocator(6)) 
    ax.yaxis.set_major_locator(MaxNLocator(6))

    #plt.show()
    plt.savefig(filname+'_pareto.png', dpi=300)

#-----
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="plot popularity graph")
    parser.add_argument("--input", "-i", metavar='I', type=str, nargs='?', default='input.txt',
                        help='input file')
    parser.add_argument("--output", "-o", metavar='O', type=str, nargs='?', default='output.txt',
                        help='output file')
    parser.add_argument("--zipf", "-z", action='store_true',
                        help='calculate zipf parameter')
    parser.add_argument("--plot_pareto", "-p", action='store_true',
                        help='plot pareto graph')
    parser.add_argument("--title", "-t", metavar='T', type=str, nargs='?', default='',
                        help='title of a graph')
    args = parser.parse_args()

    """##**memdf2 = tendency of memory block access**"""
    memdf2 = pd.read_csv(args.input+'.csv', sep=',', header=0, index_col=0, on_bad_lines='skip')

    memdf2 = ref_count_rank(memdf2)
    memdf2 = ref_count_percentile_rank(memdf2)

    memdf2 = memdf2[['blockaddress', 'count', 'type', 'type_rank', 'type_pcnt', 'type_pcnt_rank']]
    save_csv(memdf2, args.output+'.csv', 0)

    popularity_graph(memdf2, title=args.title, filname=args.output, zipf=args.zipf)
    
    if (args.plot_pareto):
        plt.cla()
        pareto_graph(memdf2, title=args.title, filname=args.output)
