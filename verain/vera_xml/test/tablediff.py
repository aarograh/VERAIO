#!/usr/bin/env python
import sys;
import string;

def bomb():
  print('End Result: TEST FAILED')
  sys.exit(-1)

if len(sys.argv) < 4:
  print('Usage: \n' + sys.argv[0] + ' [rules] [gold standard] [test results]')
  sys.exit(-1)

fnRules = sys.argv[1]
fnGold = sys.argv[2]
fnRslt = sys.argv[3]
fileRules = open(fnRules,'r')
fileGold = open(fnGold,'r')
fileRslt = open(fnRslt,'r')

header  = fileRules.readline()
if header == '':
  print('Rule file missing header line')
  bomb()
fields = header.split()
headerG = fileGold.readline()
headerR = fileRslt.readline()
if fields != headerG.split():
  print('Gold standard headers are missing or mis-matched')
  bomb()
if fields != headerR.split(): 
  print('Test output headers are missing or mis-matched')
  bomb()

ruleset = fileRules.readline()
if ruleset == '':
  print('Rule file missing rules')
  bomb()
rules = ruleset.split()
fileRules.close()

if len(rules) != len(fields): 
  print('Number of rules does not match number of fields in rule file')
  bomb()

for i in range(rules.count('OMIT')):
  ind = rules.index('OMIT')
  fields.pop(ind)
  rules.pop(ind)

fail = False
ln=1
for lineG in fileGold:
  ln=ln+1
  lineR = fileRslt.readline()
  golds = lineG.split()
  rslts = lineR.split()
  if len(rules) != len(golds):
    print('Gold standard missing fields on line ' + str(ln))
    fail = True
    continue;
  if len(rules) != len(rslts): 
    print('Output missing fields/lines on line ' + str(ln))
    fail = True
    continue;
  case = golds[0]
  for field,rule,gold,rslt in zip(fields,rules,golds,rslts):
    if rule == 'EXACT':
      if gold != rslt:
        print('Mis-match between reference and output on case '+str(case)+' at field '+field)
        fail = True
    else:
      try:
        g = float(gold)
        r = float(rslt)
      except ValueError:
        print('Error converting tokens to floating point on case '+str(case)+' at field '+field)
        fail = True
        continue
      err = abs(g-r)
      if err > float(rule):
        print('Error ' + str(err) + ' exceeds tolerance ' + str(rule) + ' on case '+str(case)+' at field '+field)
        fail = True
    
if fail == True:
  bomb()
print('End Result: TEST PASSED')
sys.exit(0)
