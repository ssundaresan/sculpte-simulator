import sys
import os
import random as rnd
import numpy as np
import route
import gen

class Topology:
  '''
    This class has the topology. Functions to read and configure the topology.
    Has sub-classes:
       routing - to route flows through the network
  '''
  nodeips = {} #### ip to node id dictionary
  nodes = {} #### node id to ip dictionary
  G = {} #### the logical topology
  L = {} #### the physical topology

  def count_nlinks(self):
    '''
      Fn to count number of unidirectional links
    '''
    cnt = 0
    for s in self.L:
      cnt += len(self.L[s])
    return cnt
 
  def get_node_ips(self,IP_FILE):
    '''
      Fn to read IP file and get node to ip mapping
    '''
    try:
      fips = open(IP_FILE,"r")
    except:
      print "IP file " + IP_FILE + " not found. Exiting.\n"
      sys.exit(1)
    for line in fips.readlines():
      if "#" in line:
        continue
      line = line.split()
      if line[0] not in self.nodes:
        nrec = {'ip':line[1]}
        self.nodes[line[0]] = nrec
      if line[1] not in self.nodeips:
        self.nodeips[line[1]] = line[0]

  def get_initwt(self,wt,cap,type):
    '''
      Fn to assign initial weights to links.
        choices are:
           base_rand - which will perturb base weights from topo file
           rand - random weight between 0 and INIT_WT_RND_RANGE
           inv_cap - Inverse capacity
    '''
    INIT_WT_RND_RANGE = self.init_wt_rnd_range
    if type == 'base_rand':
      return rnd.randint(int(wt)-INIT_WT_RND_RANGE,int(wt)+INIT_WT_RND_RANGE)
    if type == 'rand':
      return rnd.randint(0,INIT_WT_RND_RANGE)
    if type == 'inv_cap':
      cap = int(float(cap))
      wt = int(1000000/cap)
      return rnd.randint(int(wt)-INIT_WT_RND_RANGE,int(wt)+INIT_WT_RND_RANGE)

  
  def create_full_topo(self,TOPO_FILE):
    '''
      Fn to read and create topology. See $TOPO_FILE and the $IP_FILE for format
        data structure G is populated with $numslices topologies
    '''
    link_format = {0:"s",1:"d",2:"wt1",3:"wt2",5:"cap",4:"fmy"}
    #self.initwttype = 'base_rand'
    tos = self.numslices
    #G = {}
    try:
      ftopo = open(TOPO_FILE,"r")
    except:
      print "Topo file not found. Exiting.\n"
      sys.exit(1)
  
    for ct in range(0,tos):
      self.G[ct] = {}
    for line in ftopo.readlines():
      if "#" in line:
        continue
      line = line.split()
      link = {}
      for field in link_format:
        link[link_format[field]] = line[field]
      if link["s"] not in self.nodes or link["d"] not in self.nodes:
        print "Fatal error in Topo file %s %s Exiting.\n"%(link["s"],link["d"])
        sys.exit(1)
  
      if link["s"] not in self.G[0]:
        self.L[link["s"]] = {}
        for ct in range(0,tos):
          self.G[ct][link["s"]] = {}
      if link["d"] not in self.G[0][link["s"]]:
        lrec = {'fmy':link["fmy"],'cap':float(link["cap"]),'load':0.0}
        self.L[link["s"]][link["d"]] = lrec
        for ct in range(0,tos):
          initwt = self.get_initwt(link["wt1"],link["cap"],self.initwttype)
          srec = {'wt':initwt,'pt':0}
          self.G[ct][link["s"]][link["d"]] = srec

  
      #### bi-directional links ####
      if link["d"] not in self.G[0]:
        self.L[link["d"]] = {}
        for ct in range(0,tos):
          self.G[ct][link["d"]] = {}

      if self.duplex.lower() == 'no':
        continue

      if link["s"] not in self.G[0][link["d"]]:
        lrec = {'fmy':link["fmy"],'cap':float(link["cap"]),'load':0.0}
        self.L[link["d"]][link["s"]] = lrec
        for ct in range(0,tos):
          initwt = self.get_initwt(link["wt2"],link["cap"],self.initwttype)
          srec = {'wt':initwt,'pt':0}
          self.G[ct][link["d"]][link["s"]] = srec
    #return G

  def get_routing_scheme(self,fptr,routing):
    '''
      Fn to create routing object
    '''
    if routing.lower() == 'splicing':
      self.orouting = route.splice()
    if routing.lower() == 'normal':
      self.orouting = route.singleslice(fptr,self.G)

  def __init__(self,fptr):
    topo_dir = gen.get_param(fptr,"topo_dir")
    IP_FILE = topo_dir + gen.get_param(fptr,"ip_file")
    TOPO_FILE = topo_dir + gen.get_param(fptr,"topo_file")
    numslices = int(gen.get_param(fptr,"numslices"))
    self.init_wt_rnd_range = int(gen.get_param(fptr,"Range for initial Random Wt"))
    self.initwttype = gen.get_param(fptr,"Initial Wt setting")
    self.duplex = gen.get_param(fptr,"duplex")
    routing = gen.get_param(fptr,"Routing")

    self.numslices = numslices
    self.get_node_ips(IP_FILE)
    self.create_full_topo(TOPO_FILE)
    self.get_routing_scheme(fptr,routing)

