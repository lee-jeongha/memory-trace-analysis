# -*- coding: utf-8 -*-

import argparse
import pandas as pd
import numpy as np
from load_and_save import save_csv

"""##**memaccess**"""

def get_access_block_num(input_filename, chunks=100):
    blk_num_df = pd.DataFrame()

    for i in range(chunks): 
        filename = input_filename+'_'+str(i)+'.csv'

        try:
            df = pd.read_csv(filename, sep=',', header=0, index_col=0, on_bad_lines='skip')
            df = df.drop_duplicates(keep='first', subset='blockaddress')
            blk_num_df = pd.concat([blk_num_df, df])
            blk_num_df = blk_num_df.drop_duplicates(keep='first', subset='blockaddress')
        except FileNotFoundError:
            print("No file named: ", filename)
            break
    
    blk_num_df = blk_num_df.drop_duplicates(keep='first', subset='blockaddress')
    blk_num_df['acc_blk_num'] = np.arange(len(blk_num_df))

    return blk_num_df[['blockaddress', 'acc_blk_num']]

def set_unique_block_num(df, blk_num_df):
    # df['acc_blk'] = df['blockaddress'].rank(method='dense')
    df = df.join(blk_num_df.set_index('blockaddress'), on='blockaddress')

    df['blk_readi'] = df['acc_blk_num']
    df['blk_readd'] = df['acc_blk_num']
    df['blk_write'] = df['acc_blk_num']

    df.loc[(df.type!='readi'), 'blk_readi'] = np.NaN
    df.loc[(df.type!='readd'), 'blk_readd'] = np.NaN
    df.loc[(df.type!='write'), 'blk_write'] = np.NaN

    df = df[['blk_readi', 'blk_readd', 'blk_write']]

    return df

#-----
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="assign unique number to accessed memory area")
    parser.add_argument("--input", "-i", metavar='I', type=str, nargs='?', default='input.txt',
                        help='input file')
    parser.add_argument("--output", "-o", metavar='O', type=str, nargs='?', default='output.txt',
                        help='output file')
    parser.add_argument("--chunk_count", "-c", metavar='C', type=int, nargs='?', default=100,
                        help='the number of chunk groups')
    parser.add_argument("--blk_num", "-b", metavar='B', type=str, nargs='?', default=None,
                        help='unique block number assigned in order of access')
    args = parser.parse_args()

    if not args.blk_num:
        blk_num_df = get_access_block_num(args.input, args.chunk_count)
        save_csv(blk_num_df, args.output+'_blk-num'+'.csv', 0)

    for i in range(args.chunk_count):
        chunk = pd.read_csv(args.input+'_'+str(i)+'.csv', sep=',', header=0, index_col=0, on_bad_lines='skip')
    
        chunk = set_unique_block_num(chunk, blk_num_df)
        save_csv(chunk, args.output+'.csv', i)
        #save_csv(chunk, args.output+'_'+str(i)+'.csv', 0)
        print(i)
    print('done!!')
