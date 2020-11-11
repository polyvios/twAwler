#!/usr/bin/env python3

'''
This tool plots log-log plots of distributions given as x, y pairs in
txt files.  Each filename is the plot label for the corresponding
line.  argv[1] is title of the graph and output file name, rest of
argv are input datasets.

Use with graphs after counting edges:
cat weighted.graph.txt | cut -f 1 -d" " | sort | uniq -c | cut -c 1-8 > weighted.graph.outdegree.txt
cat weighted.graph.txt | cut -f 2 -d" " | sort | uniq -c | cut -c 1-8 > weighted.graph.indegree.txt
cat weighted.graph.txt | cut -f 1,2 -d" " | tr " " "\n" | sort | uniq -c | cut -c 1-8 > weighted.graph.degree.txt
graphfigures.py -t Degree -o degree.png -x Degree weighted.graph.degree.txt
'''

import sys
import optparse
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import powerlaw

#results.power_law.plot_cdf( color= 'r',linestyle='-',label='fit pdf')
#results.power_law.plot_pdf( color= 'g',linestyle='--',label='powerlaw fit')
#results.lognormal.plot_pdf( color= 'r',linestyle='--',label='lognormal fit')
#results.truncated_power_law.plot_pdf( color= 'm',linestyle='--',label='trunc powerlaw fit')
#results.plot_pdf( color= 'b', label='pdf')

if __name__ == '__main__':
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
    
    results = powerlaw.Fit(sorted_data, discrete=True)
    print("xmin: {}".format(results.power_law.xmin))
    print("xmax: {}".format(results.power_law.xmax))
    print("powerlaw alpha: {}".format(results.power_law.alpha))
    print("lognormal mu: {}".format(results.lognormal.mu))
    print("lognormal sigma: {}".format(results.lognormal.sigma))
    print("truncated_power_law alpha: {}".format(results.truncated_power_law.alpha))
    print("truncated_power_law lambda: {}".format(results.truncated_power_law.Lambda))
    R, p = results.distribution_compare('power_law', 'lognormal')
    print("compare powerlaw vs lognormal: R: {}, p: {}".format(R, p))
    R, p = results.distribution_compare('truncated_power_law', 'lognormal')
    print("compare truncated_power_law vs lognormal: R: {}, p: {}".format(R, p))
    R, p = results.distribution_compare('truncated_power_law', 'power_law')
    print("compare truncated_power_law vs powerlaw: R: {}, p: {}".format(R, p))

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
