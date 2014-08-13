#! /usr/bin/env python 

import os
import sys
import difflib

def filter_text( lines ):
  filtered_lines = []
  for line in lines :
    if line[0] != '*' :
      newline = ' '.join(line.split()).replace("\n","")
      if newline != '' :
        filtered_lines.append(newline)
  return filtered_lines


def strip_comments( lines ):
  filtered_lines = []
  for line in lines :
    loc = line.find('#')
    newline = line
    if loc != -1 :
      newline = line[0:loc]
    if newline != '' :
      filtered_lines.append(newline)

  return filtered_lines


if len(sys.argv) != 3 :
  raise Exception("Use: "+sys.argv[0]+" filename1 filename2")

text_file1 = open(sys.argv[1],'r')
text_file2 = open(sys.argv[2],'r')
raw_data1 = text_file1.readlines()
raw_data2 = text_file2.readlines()
text_file1.close()
text_file2.close()


filtered_data1a = strip_comments(raw_data1)
filtered_data1 = filter_text(filtered_data1a)
filtered_data2a = strip_comments(raw_data2)
filtered_data2 = filter_text(filtered_data2a)

#if filter_text(raw_data1) == filter_text(raw_data2) :
if filtered_data1 == filtered_data2 :
  print 'Files are the same'
  sys.exit(0)
else :
  for line in difflib.context_diff(filtered_data1, filtered_data2, fromfile=sys.argv[1], tofile=sys.argv[2]):
    print line
  print '\n\nFiles are NOT the same\n'
  sys.exit(1)

## Perform for each line
#for line in filter_text(raw_data) :
#  print line
