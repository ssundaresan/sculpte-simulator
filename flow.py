import sys
import os
import random as rnd
import numpy as np
from numpy import random as rv
import route
import gen
import heapq

class flowgen(object):
  '''
   Flow generator class. Instantiates objects inside
   - for flow arrival, size of flow and throughput assignment.
  '''
  def __init__(self,fptr,tm):
    self.time = 0
    self.flowid = 0

    fsize = gen.get_param(fptr,"Flow Size")
    if fsize.lower() == 'exponential':
      self.sizegen = size_exp(fptr) # object for flow size generation
    if fsize.lower() == 'pareto':
      self.sizegen = size_pareto(fptr) # object for flow size generation
    
    arrprocess = gen.get_param(fptr,"Flow Arrival")
    if arrprocess.lower() == 'poisson': # object for flow arrival
      self.arrival = arr_poisson(fptr,tm,self.sizegen.avgflowsize())

    tput = gen.get_param(fptr,"Flow Tput")
    if tput.lower() == 'standard':
      self.tput = tput_std() # object for throughput assignment

    self.numslices = int(gen.get_param(fptr,"numslices"))
    self.routing = gen.get_param(fptr,"routing")

  def get_sbits(self,num):
    '''
      assign splicing bits to flow
    '''
    sbits = ''
    if self.routing.lower() == 'normal':
      sbits += str(int(rnd.random()*self.numslices))
    if self.routing.lower() == 'splicing':
      for i in range(0,num):
        #sbits += str(rnd.randrange(0,self.numslices,1)) + "-"
        sbits += str(int(rnd.random()*self.numslices)) + "-"
      sbits = sbits[0:len(sbits)-1]
    return sbits
       
  def next(self,tm):
    '''
      Fn to generate next flow
    '''
    arrevent = self.arrival.next(tm)
    s = arrevent["s"]
    d = arrevent["d"]
    arrtime = arrevent["time"]

    flowsize = self.sizegen.next()
    tput = self.tput.next()
    sbits = self.get_sbits(len(tm))
    #sprt = rnd.randrange(0,20000)
    #dprt = rnd.randrange(0,20000)
    sprt = int(rnd.random()*20000)
    dprt = int(rnd.random()*20000)
    nflow = {"id":self.flowid,"type":"flow-arr","s":s,"d":d,"time":arrtime,\
     "size":flowsize,"tput":tput,"sbits":sbits,"sprt":sprt,"dprt":dprt}
    self.flowid += 1

    return nflow 

class size_exp(object):
  '''
    Class for exponentially distributed flow generator. 
    Should make it inherit from parent generic class.
  '''
  def __init__(self,fptr):
    self.param = float(gen.get_param(fptr,"Lambda"))

  def avgflowsize(self):
    return self.param

  def next(self):
    size = rv.exponential(self.param,1)
    return size[0]

class size_pareto(object):
  def __init__(self,fptr):
    self.alpha = 1.3
    self.param = float(gen.get_param(fptr,"Lambda"))
    self.U = 8000
    #self.L = self.param*(self.alpha-1)/self.alpha
    self.L = float(gen.get_param(fptr,"Pareto L"))

  def avgflowsize(self):
    return self.param
    
  def next(self):
    alpha = self.alpha
    U = self.U
    L = self.L
    exp = 1.0/alpha
    if U == None:
      val = L/(math.pow(rnd.random(),exp) )
    else:
      r = rnd.random()
      val = pow((-(r*pow(U,alpha) - r*pow(L,alpha) - pow(U,alpha))/(pow(U,alpha)*pow(L,alpha))),-exp)
    return val

class tput_std(object):
  def __init__(self):
    #self.tputarr = [0.5,1.0,5]
    self.tputarr = [0.5,2,10]
    #self.tputarr = [0.0005]
    self.num = len(self.tputarr)

  def next(self):    
    #rndch = rnd.randrange(0,self.num)
    rndch = rnd.random()
    l = len(self.tputarr) - 1 
    if rndch < 0.3:
      return self.tputarr[0]
    if rndch < 0.9:
      return self.tputarr[min(1,l)]

    return self.tputarr[min(2,l)]
    #return self.tputarr[rndch]

class arr_poisson(object):
  '''
    possion arrival generator
  '''
  def __init__(self,fptr,tm,flowsize):
    self.simdur = float(gen.get_param(fptr,"SIM_DUR"))
    self.flowsize = flowsize
    self.allnextarr = []
    self.initarrivals(tm)

  def initarrivals(self,tm):
    '''
      intialize array with arrival for all s-d pairs. 
    '''
    for s in tm:
      for d in tm:
        if s == d:
          continue
        arrtime = self.interarr(s,d,tm[s][d],0.0)
        arrevent = {"s":s,"d":d,"time":arrtime}
        self.allnextarr.append((arrevent["time"],arrevent))
    
    #self.allnextarr.sort(lambda x,y:cmp(x["time"],y["time"]))
    heapq.heapify(self.allnextarr)
 
  def insert(self,event):
    ''' 
      Fn to insert a new event in the arrival queue. 
    '''
    #inspos = gen.get_pos(self.allnextarr,'time',event)
    #self.allnextarr.insert(inspos,event)
    eventtuple = (event['time'],event)
    heapq.heappush(self.allnextarr,eventtuple)

  def pop(self):
    eventtuple = heapq.heappop(self.allnextarr)
    #print "flow eventtuple " + str(eventtuple)
    event = eventtuple[1]
    return event
  
  def next(self,tm):
    '''
      choose earliest arrival from allnextarr and replace.
    '''
    #arrevent = self.allnextarr.pop(0)
    arrevent = self.pop()
    s = arrevent["s"]
    d = arrevent["d"]
    arrtime = arrevent["time"]
    arrtime = self.interarr(s,d,tm[s][d],arrtime)
    nextevent = {"s":s,"d":d,"time":arrtime}
    #self.allnextarr.append(nextevent) 
    #self.allnextarr.sort(lambda x,y:cmp(x["time"],y["time"]))
    self.insert(nextevent)
    return arrevent

  def interarr(self,s,d,avgtraff,time):
    if float(avgtraff) == 0:
      return self.simdur + 1
    rate = float(avgtraff)/self.flowsize 
    scale = 1.0/rate
    nextarr = rv.exponential(scale,1)
    return nextarr[0] + time
