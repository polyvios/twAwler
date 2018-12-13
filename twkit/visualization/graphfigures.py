#!/usr/bin/env python

'''
This tool plots log-log plots of distributions given as x, y pairs in
txt files.  Each filename is the plot label for the corresponding
line.  argv[1] is title of the graph and output file name, rest of
argv are input datasets.

Use with graphs after counting edges:
cat weighted.graph.txt | cut -f 1 -d" " | sort | uniq -c | cut -c 1-8 > weighted.graph.outdegree.txt
cat weighted.graph.txt | cut -f 2 -d" " | sort | uniq -c | cut -c 1-8 > weighted.graph.indegree.txt
cat weighted.graph.txt | cut -f 1,2 -d" " | tr " " "\n" | sort | uniq -c | cut -c 1-8 > weighted.graph.degree.txt
graphfigures.py -t Degre -o degree.png -x Degree weighted.graph.degree.txt
'''

import sys
import optparse
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

parser = optparse.OptionParser()
parser.add_option('-o', '--output', action='store', dest='output', default="output.png", help='Output file')
parser.add_option('-t', '--title', action='store', dest='title', default=None, help='Chart title')
parser.add_option('-x', '--xlabel', action='store', dest='xlabel', default="Degree", help='X axis')
parser.add_option('--dotsize', action='store', dest='dotsize', type=int, default="9", help='Size of each point')
parser.add_option('--width', action='store', dest='width', type=int, default="5", help='Image width in inches')
parser.add_option('--height', action='store', dest='height', type=int, default="4", help='Image height in inches')
parser.add_option('--legendfont', action='store', dest='fontsize', type=int, default="13", help='Legend font size')
parser.add_option('--abs', action='store_true', dest='absolute', default=False, help='Y-axis not normalized')
(options, args) = parser.parse_args()

plt.figure(figsize=(options.width,options.height))

plt.yscale('log')
plt.xscale('log')
for inputfile in args:
  data = np.loadtxt(inputfile)
  title = inputfile.split('/')[-1].split('.')[0]
  sorted_data = np.sort(data)
  n = len(sorted_data)
  if options.absolute:
    yvals=np.arange(n)
    plt.plot(sorted_data, yvals, ".", ms=options.dotsize, label=title)
  else:
    yvals=np.arange(n)/float(n-1)
    plt.plot(sorted_data, 1-yvals, ".", ms=options.dotsize, label=title)

if options.title: plt.title(options.title)
if options.xlabel: plt.xlabel(options.xlabel)
plt.ylabel('PMF')
plt.legend(loc=1,fontsize=options.fontsize)
plt.savefig(options.output, bbox_inches='tight', pad_inches=0)
