import numpy.random as nr
import gen 

class TMgen(object):
  '''
    Class TMgen is used to create the traffic matrix. The format is 
      "src dst amt" where "amt" is the flow amount in mbps
       To write your own generator, write a class that inherits from
       TMgen, and has a method "gen" that generates the matrix
  '''

  def __init__(self,fptr,topo,tmtype):
    self.tmtype = tmtype
    self.gen_flag = int(gen.get_param(fptr,'TMgenerate'))
    self.FRAC_UTIL= float(gen.get_param(fptr,'FRAC_UTIL'))
    self.tm = {}
    self.topo_name = gen.get_param(fptr,'topo_name')
    #self.base_dir = 'data/traffic/matrices/'
    self.base_dir = gen.get_param(fptr,"tm_dir")
    self.tm_name = gen.get_param(fptr,"tm_name")
    for s in topo:
      self.tm[s] = {}
      for d in topo:
        self.tm[s][d] = 0.0

  def generate(self,topo):
    if 'exp' not in self.base_dir:
      self.base_dir += self.tmtype.lower() + '/'
    self.FILE = self.base_dir + "/" + \
     self.tm_name
    self.FILE_base = self.FILE
    if self.gen_flag == 1: #flag to denote whether to read already generated -
      self.gen(topo) # - TM or to generate new TM
    else:
      self.read()

  def read(self): 
    '''
     Fn to read existing TM
    '''
    ftm = open(self.FILE)
    print "writing to %s"%(self.FILE)
    for line in ftm.readlines():
      line = line.split()
      src = line[0]
      dst = line[1]
      val = line[2]
      self.tm[src][dst] = val

class gravityTMgen(TMgen): 
  '''
    Class to generate TM using gravity model. Traffic from src to dst 
     depends on the outbound bandwidth of src and inbound bandwidth of dst. 
  '''

  def gen(self,topo):
    Cap = {}
    totalcap = 0 
    for src in topo:
      cap = 0 
      for dst in topo[src]:
        cap += topo[src][dst]['cap']
      Cap[src] = cap 
      totalcap += cap 
  
    for src in self.tm: 
      outgoing = Cap[src]
      cap = totalcap - Cap[src]
      for dst in self.tm: 
        if dst != src:
          self.tm[src][dst] = self.FRAC_UTIL * outgoing * Cap[dst]/cap
  
    ftm = open(self.FILE,"w")
    for src in self.tm: 
      for dst in self.tm: 
        ftm.write("%s %s %.0f\n"%(src,dst,self.tm[src][dst]))


class bimodalTMgen(TMgen):
  '''
    Class to generate TM using gravity model. Traffic from src to dst 
     generated according to two "modes" - normal and heavy hitters
  '''

  def gen(self,topo):
    Cap = {}
    totalcap = 0
    for src in topo:
      cap = 0
      for dst in topo[src]:
        cap += topo[src][dst]['cap']
      Cap[src] = cap
      totalcap += cap
  
    for src in Cap:
      self.tm[src] = {}
      for dst in Cap:
        self.tm[src][dst] = 0
    for src in self.tm:
      outgoing = Cap[src]
      SIG = 20.0/(150*150)
      for dst in self.tm:
        if src == dst:
          self.tm[src][dst] = 0
          continue
        if nr.random() < 0.2:
          FRAC = 1.67*self.FRAC_UTIL
        else:
          FRAC = 0.7*self.FRAC_UTIL
        self.tm[src][dst] = \
         nr.normal(1,SIG)*FRAC*outgoing/(float(len(self.tm[src])))
  
    ofile = self.FILE #+ str(i)
    print ofile
    ftm = open(ofile,"w")
    for src in self.tm:
      for dst in self.tm:
        ftm.write("%s %s %.0f\n"%(src,dst,self.tm[src][dst]))


def get_TMgen(fptr,topo):
  '''
    Fn to instantiate object depending on specified TM model
  '''
  tmtype = gen.get_param(fptr,"tmtype")
  if tmtype == 'GRAVITY':
    tm = gravityTMgen(fptr,topo,tmtype)
  if tmtype == 'BIMODAL':
    tm = bimodalTMgen(fptr,topo,tmtype)
  return tm
