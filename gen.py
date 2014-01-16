import sys
import os
import random as rnd
import numpy as np
import cStringIO as strio
#import sim_create_tm as sim
import topo 
import tmc

'''
  reads input file, puts it in a buffer that can be read as a file
  input - None - by defaut looks for file "input" in dir. May change
  to read file name. 
  output - file buffer
'''

def get_input(file = None):
  if file == None:
    f = open("input")
  else:
    f = open(file)
  lines = f.readlines()
  f.close()
  f = strio.StringIO()
  for line in lines:
    f.write(line)
  return f

def modify_param(fptr,string,new_param):
  f = strio.StringIO()
  lines = fptr.getvalue().split("\n")
  for line in lines:
    if '####' in line:
      f.write(line+"\n")
      continue
    if string.lower() in line.lower():
      line = line.split("#")[0]
      param = line.split("--")[1]
      line = line.split("--")[0] + "-- " + str(new_param) + " # " + str(line.split("#")[1:])
    f.write(line + "\n")
  return f
   
  
'''
  gets required parameter from the file buffer. 
  input - buffer, search string
  output - value of parameter that matches search string in str.
  explicit conversion to int/float/... required.
  follow format style specified in "input"
'''

def get_param(fptr,string):
  print "In get_param, checking for " + string + "... ",
  lines = fptr.getvalue().split("\n")

  for line in lines:
   if '####' in line:
     continue
   if string.lower() in line.lower():
     print line
     if '#' in line:
       line = line.split("#")[0]
     param = line.split("--")[1]
     param = param.replace(" ","")
     #param = line[len(line)-1]
     print "found " + param 
     return param
  return None

def cp_file(fptr,dir,fname):
  fp = open(dir+fname,"w")
  lines = fptr.getvalue().split("\n")
  for line in lines:
    fp.write(line + "\n") 
  fp.close()

def get_pos(arr,key,item):
  '''
    Fn to return position where item will go in sorted array arr.
      "key" is the dictionary key used to sort
  '''
  s = 0
  d = len(arr)-1
  m = d/2

  #print arr,s,d,key,item
  if len(arr) == 0:
    return 0
  if arr[s][key] > item[key]:
    return 0
  if arr[d][key] < item[key]:
    return len(arr)

  while arr[m][key] != item[key]:
    if arr[m][key] > item[key]:
      d = m
    else:
      s = m
    m = (s+d)/2
    if s == m:
      break
    #print s,d,arr[s][key],arr[d][key]
  #print "returning %d between %s and %s"%(m+1,arr[m][key],arr[m+1][key])
  if arr[m][key] > item[key] or arr[m+1][key] < item[key]:
    print "Something smells"
  return m+1

def gen_tm(fptr):
  cnt = 0
  n = {'GRAVITY':1,'BIMODAL':4}
  tmfrac = {'GRAVITY':[0.05,0.03,0.06,0.08],'BIMODAL':[0.06,0.03,0.04,0.05]}
  topo_dir = 'data/topos/'
  TMgenerate = 1
  duplex = 'yes'
  fptr = modify_param(fptr,"topo_dir",topo_dir)
  fptr = modify_param(fptr,"duplex",duplex)
  fptr = modify_param(fptr,"TMgenerate",TMgenerate)
  for tmtype in ['BIMODAL','GRAVITY']:
    fptr = modify_param(fptr,"tmtype",tmtype)
    for frac in tmfrac[tmtype]:
      fptr = modify_param(fptr,"FRAC_UTIL",frac)
      for i in range(0,n[tmtype]):
        fptr = modify_param(fptr,"tm_name",'tm'+str(cnt))
        #sim.initialize(fptr)
        otopo = topo.Topology(fptr) # create topo object #
        otm = tmc.get_TMgen(fptr,otopo.L) # create traffic matrix (TM) object #
        otm.generate(otopo.L) # generate the TM #
        cnt += 1
        print ""
  sys.exit()
