#!/usr/bin/env python

import sys
import os
import random as rnd
import topo
import numpy as np
import tmc
import gen
import flow
import event
import plot
#import profile


def initialize(fptr):
  otopo = topo.Topology(fptr) # create topo object #
  otm = tmc.get_TMgen(fptr,otopo.L) # create traffic matrix (TM) object #
  otm.generate(otopo.L) # generate the TM #

  oflowgen = flow.flowgen(fptr,otm.tm) # create flow generator object #
  oevent = event.event(fptr,otopo,otm) # create event simulator object #
 
  sim_dur = int(gen.get_param(fptr,"SIM_DUR")) # duration of simulation #
  oevent.insert(oflowgen.next(otm.tm)) # insert first event #
  

  #loadev = {"type":"load-surge","time":1000,"surgetype":"random","num":5}
  #oevent.insert(loadev)

  while True:
    currev = oevent.pop() # pop event from queue #
    if currev["time"] > sim_dur: # time #
      break
    oevent.handler(currev,otopo,otm) # handle current event #
    if currev["type"] == "flow-arr": # if event is flow arrival, inseert next -
      oevent.insert(oflowgen.next(otm.tm)) # - arrival in event queue
     

def algo_setting(fptr,algo):
  if algo == 'pste':
    fptr = gen.modify_param(fptr,'initial wt setting','inv_cap')
    fptr = gen.modify_param(fptr,'link weight update','KeyMetric_ecmp')
    #fptr = gen.modify_param(fptr,'numslices',3)

  if algo == 'thorup':
    fptr = gen.modify_param(fptr,'initial wt setting','base_rand')
    fptr = gen.modify_param(fptr,'link weight update','static')
    fptr = gen.modify_param(fptr,'numslices',1)

  if algo == 'inv_cap':
    fptr = gen.modify_param(fptr,'initial wt setting','inv_cap')
    fptr = gen.modify_param(fptr,'link weight update','static')
    fptr = gen.modify_param(fptr,'numslices',1)

  out = gen.get_param(fptr,"outdir")
  fptr = gen.modify_param(fptr,'outdir',out+algo+"/")
  return fptr

def change_topo(fptr,tid,fail=''):
  fptr = gen.modify_param(fptr,'ip_file','tm'+fail+str(tid)+'_ips')
  fptr = gen.modify_param(fptr,'topo_file','tm'+fail+str(tid)+'_topo')
  fptr = gen.modify_param(fptr,'tm_name','tm'+str(tid))
  return fptr 

if __name__ == '__main__':
  fptr = gen.get_input()
       
  #fptr = gen.modify_param(fptr,'duplex','no')
  for algo in ['pste']:#,'inv_cap']:
   fptr = algo_setting(fptr,algo)
   for tid in range(0,1):
      print 'Topo ID %s\n'%(tid)
      for i in range(0,1):
        initialize(fptr)
        plot.plot(fptr)
