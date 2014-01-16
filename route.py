# Dijkstra's algorithm for shortest paths # David Eppstein, UC Irvine, 4 April 2002 
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/117228
import sys
import gen
sys.path.append("support")
from priodict import *

class short_paths:
  '''
    Class for generic shortest path scheme. Contains dijkstra's for calculating
    - shortest path tree from a source and shortest paths.
    Inherited classes implement actual path selection
  '''

  def __init__(self,G):
    self.Darr = {}
    self.Parr = {}
    for i in range(0,len(G)):
      self.Darr[i] = {}
      self.Parr[i] = {}

    for i in range(0,len(G)):
      self.get_sptree(G[i],i)

  def Dijkstra(self,G,start,end=None):
    D = {}	# dictionary of final distances
    P = {}	# dictionary of predecessors
    Q = priorityDictionary()   # est.dist. of non-final vert.
    Q[start] = 0
  
    for v in Q:
      D[v] = Q[v]
      if v == end: break
      for w in G[v]:
        vwLength = D[v] + G[v][w]['wt']
        if w in D:
          if vwLength < D[w]:
            print G
            raise ValueError,"Dijkstra: found better path to already-final vertex"
        else:
          if w not in Q or vwLength < Q[w]:
            Q[w] = vwLength
            P[w] = []
            P[w].append(v)
          if vwLength == Q[w] and v not in P[w]:
            P[w].append(v)
    return (D,P)

  def paths(self,topo,topo_id,s,d,flow,recompute=0):
    if recompute:
      D,P = self.Dijkstra(topo,s)
    else:
      D = self.Darr[topo_id][s]
      P = self.Parr[topo_id][s]

    if d not in D:
      return []
    paths = self.shortestPath(D,P,s,d,flow)
    for i in range(0,len(paths)):
      paths[i].reverse() 
    return paths 

  def all_sd_paths(self,topo,topo_id,recompute=0):
    allpaths = {}
    for s in topo:
      if recompute:
        D,P = self.Dijkstra(topo,s)
      else:
        D = self.Darr[topo_id][s]
        P = self.Parr[topo_id][s]
      #D,P = self.Dijkstra(topo,s)
      allpaths[s] = {}
      for d in topo:
        if s == d: continue
        paths = self.shortestPath(D,P,s,d,flow=0)
        for i in range(0,len(paths)):
          paths[i].reverse() 
        allpaths[s][d] = paths 
    return allpaths
  
  def get_sptree(self,topo,topo_id):
    for s in topo:
      self.Darr[topo_id][s],self.Parr[topo_id][s] = self.Dijkstra(topo,s)


class noecmproute(short_paths):
  '''
    No ECMP routing. Greedy shortest path algo
  '''
  #### Overwrite Dijkstra's in parent class####
  def Dijkstra(self,G,start,end=None):
    D = {}  # dictionary of final distances
    P = {}  # dictionary of predecessors
    Q = priorityDictionary()   # est.dist. of non-final vert.
    Q[start] = 0
  
    for v in Q:
      D[v] = Q[v]
      if v == end: break
      
      for w in G[v]:
        vwLength = D[v] + G[v][w]['wt']
        if w in D:
          if vwLength < D[w]:
            raise ValueError,"Dijkstra: found better path to already-final vertex"
        elif w not in Q or vwLength < Q[w]:
          Q[w] = vwLength
          P[w] = v
    
    return (D,P)

  def shortestPath(self,D,P,start,end,flow):
    Path = []
    if len(P) == 0:
      return [[]]
    while 1:
      Path.append(end)
      if end == start:
         break
      end = P[end]
    #Path.reverse()
    return [Path]
    

class ecmproute(short_paths):
  '''
    ECMP routing. Path chosen by hashing flow.
  '''
  def shortestPath(self,D,P,start,end,flow):
    #D,P = Dijkstra(G,start,end)
    Path = []
    if len(P) == 0:
      return [[]]
    while 1:
      Path.append(end)
      if end == start:
         break
      #h = hashlib.new('MD5',flow)
      #hsh = int(int(h.hexdigest(),16)%len(P[end]))
      hsh = hash(flow)%len(P[end])
      end = P[end][hsh]
      #end = P[end][hash(flow)%len(P[end])]
    #Path.reverse()
    return [Path]


class fluidecmproute(short_paths):
  '''
    Fluid ECMP routing. All shortest paths returned.
  '''
  def shortestPath(self,D,P,start,end,flow):
    #print "start %s end %s P %s"%(start,end,P)
    Paths = self.get_all_paths(P,start,end) 
    for path in Paths:
      path.append(start)
    return Paths
  
  def get_all_paths(self,P,s,e):
    if e not in P:
      return [[]]
    if s == e:
      return [[s]]
    allpaths = []
    for p in P[e]:
      paths = self.get_all_paths(P,s,p)
      for path in paths:
        curr = [e]
        curr.extend(path)
        allpaths.append(curr)
    return allpaths

#  def paths(self,topo,s,d,flow):
#    D,P = self.Dijkstra(topo,s)
#    paths = self.shortestPath(D,P,s,d,flow)
#    for i in range(0,len(paths)):
#      paths[i].reverse() 
#    print paths


class route(object):
  '''
    Class for implementing fancy routing schemes like splicing, 
    - k choose n splicing, etc. Each scheme inherits (nothing?)
    from this class.
  '''
  def __init__(self,fptr,G):
    short_paths = gen.get_param(fptr,"Short Paths")
    if short_paths.upper() == 'SP':
      self.oshort_paths = noecmproute(G)
    if short_paths.upper() == 'ECMPSP':
      self.oshort_paths = ecmproute(G)
    if short_paths.upper() == 'FLUIDECMPSP':
      self.oshort_paths = fluidecmproute(G)

  def sptree(self,G,topo_id):
    self.oshort_paths.get_sptree(G,topo_id)

class singleslice(route):
  '''
    Single slice routing. Flows get assigned a slice which they 
    - stay on.
  '''
  def assign(self,G,event):
    flow = "s" + str(event["s"]) + "d" + str(event["d"]) 
    flow += str(event["sprt"]) + str(event["dprt"])
    s = event["s"]
    d = event["d"]
    topo_id = int(event["sbits"].split("-")[0])
    paths = self.oshort_paths.paths(G[topo_id],topo_id,s,d,flow)
    return paths

  def deassign(self,G,topo_id,s,d,event):
    paths = event["paths"]

