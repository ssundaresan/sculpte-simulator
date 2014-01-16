import gen
import update
import os
import copy
import heapq
import random as rnd
import gzip as gz

class event(object):
  '''
    Class event handles events. Events include flow arrival/departure,
      and updating link weights at each iteration. Other events, like
      link failures will get a handler here.
  '''

  def __init__(self,fptr,otopo,otm):
    self.total_agg_arr = 0 # Accounting flows # 
    self.total_agg_dep = 0 # '' # 
    self.agg_arr = {}
    self.agg_dep = {}
    self.inst_load = {}
    self.routed_flows = 0
    self.queue = []  # the event queue. Contains time of next flow arrival - 
      # - departure, and all iterations. #
    for s in otm.tm:
      self.agg_arr[s] = {} # Accounting flows #
      self.agg_dep[s] = {}
      self.inst_load[s] = {}
      for d in otm.tm[s]:
        self.agg_arr[s][d] = 0
        self.agg_dep[s][d] = 0
        self.inst_load[s][d] = 0
  
    #event = {"type":"","time":-1}
    self.numslices = int(gen.get_param(fptr,"numslices"))
    self.sim_dur = int(gen.get_param(fptr,"SIM_DUR"))
    self.iter_dur = int(gen.get_param(fptr,"ITER_DUR"))
    self.trans_dur = int(gen.get_param(fptr,"TRANS_DUR"))
    self.static_load = gen.get_param(fptr,"STATIC_LOAD")

    for iter in range(self.iter_dur,self.sim_dur,self.iter_dur): #iter events #
      event = {"type":"iter","time":iter}
      self.insert(event)
    self.add_static_load_events(otopo)

    updatetype = gen.get_param(fptr,"Link Weight Update") # link update algo #
    if updatetype.lower() == "keymetric_std":
      self.olinkupdate = update.keymetric_std(fptr,otopo) # link update obj # 
    if updatetype.lower() == "keymetric_ecmp":
      self.olinkupdate = update.keymetric_ecmp(fptr,otopo) # link update obj # 
    if updatetype.lower() == "static":
      self.trans_dur = self.sim_dur

    self.outfile = gen.get_param(fptr,"outdir") # output directory #
    topo_name = gen.get_param(fptr,"topo_name")
    self.outfile += "/" + topo_name + "/"
    try:                                 # check and prepare output dir #
      dir = os.listdir(self.outfile)     
    except:
      print self.outfile
      os.system("mkdir -p " + self.outfile)
      dir = []
    fn = -1
    for i in dir:
      if "run" not in i:
        continue
      i = i.split("run")[1]
      if int(i) > fn:
        fn = int(i)
    fn += 1
    self.outfile += ("run" + str(fn) + "/")
    os.system("mkdir " + self.outfile)
    #print "cp input " + self.outfile  # store input params assoc with this run
    #os.system("cp input " + self.outfile)
    gen.cp_file(fptr,self.outfile,"input")

  def insert(self,event):
    ''' 
      Fn to insert a new event in the event queue. Sort after insert
    '''
    #self.queue.append(event)
    #self.queue.sort(lambda x,y:cmp(x["time"],y["time"]))
    #inspos = gen.get_pos(self.queue,'time',event)
    #self.queue.insert(inspos,event)
    eventtuple = (event["time"],event)
    heapq.heappush(self.queue,eventtuple)
  
  def pop(self):
    '''
      Fn to pop next event to handle
    '''
    #event = self.queue.pop(0)
    eventtuple = heapq.heappop(self.queue)
    event = eventtuple[1]
    return event

  def add_static_load_events(self,otopo):
    if self.static_load == None:
      return
    if self.static_load.lower() == "mate":
      s = "4"
      d = "7"
      load = otopo.L[s][d]["cap"]*0.75
      event = {"type":"static-load","time":0,"s":s,"d":d,"load":load}
      self.insert(event)

      s = "4"
      d = "7"
      load = otopo.L[s][d]["cap"]*-0.34
      event = {"type":"static-load","time":3000,"s":s,"d":d,"load":load}
      self.insert(event)

      s = "5"
      d = "8"
      load = otopo.L[s][d]["cap"]*0.32
      event = {"type":"static-load","time":0,"s":s,"d":d,"load":load}
      self.insert(event)

      s = "5"
      d = "8"
      load = otopo.L[s][d]["cap"]*0.32
      event = {"type":"static-load","time":4600,"s":s,"d":d,"load":load}
      self.insert(event)

      s = "6"
      d = "9"
      load = otopo.L[s][d]["cap"]*0.32
      event = {"type":"static-load","time":0,"s":s,"d":d,"load":load}
      self.insert(event)

  def handler(self,event,otopo,otm=None):
    '''
      Fn to call appropriate handler for current event
    '''
    if event["type"] == 'iter':
      self.iter_handler(event,otopo)

    if event["type"] == 'flow-arr':
      self.flow_arr_handler(event,otopo)
     
    if event["type"] == 'flow-dep':
      self.flow_dep_handler(event,otopo)

    if event["type"] == 'static-load':
      self.static_load_handler(event,otopo)

    if event["type"] == 'link-fail':
      self.link_fail_handler(event,otopo)

    if event["type"] == 'load-surge':
      self.load_surge_handler(otm,event)

  def iter_handler(self,event,otopo):
    '''
      Fn to handle link updates at each iteration
       calls the linkupdate object
    '''
    iter_id = event["time"]/self.iter_dur - 1
    topo_id = iter_id % self.numslices
    print "Iter " + str(iter_id) + " Updating Topo id " + str(topo_id)
    #print "Total arrivals = %s"%(self.total_agg_arr)
    #print "Total departures = %s"%(self.total_agg_dep)
    #print "Total in system = %s"%(self.total_agg_arr - self.total_agg_dep)
    print event["time"],self.sim_dur/self.iter_dur
    check_tm_write = 0
    fttmout = gz.open(self.outfile+'tm_'+str(iter_id),"w")
    for s in self.agg_arr:
      for d in self.agg_arr[s]:
        fttmout.write("%s %s %.0f\n"%(s,d,self.inst_load[s][d]))
    fttmout.close()

    #if event["time"] + self.iter_dur >= self.sim_dur:
      #ftmout = open(self.outfile+ "fin_tm","w")
      #check_tm_write = 1
    #if event["time"] + self.iter_dur == self.trans_dur:
      #ftmout = open(self.outfile+ "trans_tm","w")
      #check_tm_write = 1
    #if check_tm_write:
      #for s in self.agg_arr:
        #for d in self.agg_arr[s]:
          #ftmout.write("%s %s %.0f\n"%(s,d,self.agg_arr[s][d]/event["time"]))
      #ftmout.close()
    if event["time"] > self.trans_dur:
      self.olinkupdate.linkupdate(otopo,topo_id)
      otopo.orouting.sptree(otopo.G[topo_id],topo_id)
    self.write_to_file(otopo,topo_id,iter_id)
    ##print "Post topo %s"%(otopo.G[topo_id])
    ##print ""

  def write_to_file(self,otopo,topo_id,iter_id):
    '''
      Fn to write output of link updates to file
    '''
    fp = gz.open(self.outfile+str(iter_id+1),"w")
    for s in otopo.G[topo_id]:
      for d in otopo.G[topo_id][s]:
        fp.write("%s %s %s %s %s %.3f\n"%(s,d,otopo.G[topo_id][s][d]["wt"],\
         otopo.G[topo_id][s][d]["pt"],otopo.L[s][d]["load"],\
         otopo.L[s][d]["load"]/otopo.L[s][d]["cap"]))
        otopo.G[topo_id][s][d]["pt"] = 0
    fp.close()

  def flow_arr_handler(self,event,otopo):
    '''
      Fn to handle flow arrivals.
        Get route of flow.
        Compute departure time and insert flow departure in queue
        Assign throughput to route. (Divide in case of fluid ecmp)
    '''
    paths = otopo.orouting.assign(otopo.G,event)

    deptime = event["time"] + event["size"]/event["tput"]
    if deptime > self.sim_dur:
      deptime = self.sim_dur
    #nevent = dict(event)
    nevent = copy.deepcopy(event)
    nevent["type"] = "flow-dep"
    nevent["time"] = deptime
    nevent["paths"] = paths

    #self.queue.append(nevent)
    #self.queue.sort(lambda x,y:cmp(x["time"],y["time"]))
    #self.insert(nevent)

    #print "Inserting flow %s into path "%(event),
    #print nevent["paths"]
    div = len(paths)
    tputshare = event["tput"]/float(div)
    #print otopo.L
    ass_flag = 1
    for p in paths:
      for i in range(0,len(p)-1):
        curr_load = otopo.L[p[i]][p[i+1]]["load"]
        cap = otopo.L[p[i]][p[i+1]]["cap"]
        if (curr_load + tputshare)/cap > 1.0:
          ass_flag = 0
          break
    ass_flag = 1
    if ass_flag == 1:
      self.routed_flows += 1
      self.insert(nevent)
      self.agg_arr[event['s']][event['d']] += event['size']
      self.total_agg_arr += event["size"]
      self.inst_load[event['s']][event['d']] += event['tput']
      for p in paths:
        for i in range(0,len(p)-1):
          otopo.L[p[i]][p[i+1]]["load"] += tputshare
      #print "Putting in %s\n"%(paths)


    #print "Handling arrival %s"%(event)
    ##print "Putting it in path %s"%(paths)
    ##print ""
    #print "Resultant L "
    #for i in otopo.L:
      #print i, otopo.L[i]
         
  def flow_dep_handler(self,event,otopo): 
    '''
      Fn to handle flow departure
       De-assign throughput from paths
    '''   
    #print "Taking flow %s off path %s\n"%(event,event["paths"]),
    #print event["paths"]
    paths = event["paths"]
    div = len(paths)
    tputshare = event["tput"]/float(div)
    for p in paths:
      for i in range(0,len(p)-1):
        otopo.L[p[i]][p[i+1]]["load"] -= tputshare

    self.agg_dep[event['s']][event['d']] += event['size']
    self.total_agg_dep += event["size"]
    self.inst_load[event['s']][event['d']] -= event['tput']

    #print "Handling departure %s"%(event)
    ##print "Taking it off path %s"%(paths)
    ##print ""
    #print "Resultant L "
    #for i in otopo.L:
      #print i, otopo.L[i]

  def check_link_in_paths(self,paths,s,d):
    '''
      Fn to see if link (s,d) is in any path in paths.
        Return 1 if it is, else 0
    '''
    #print "checking for %s %s in %s"%(s,d,paths)
    for path in paths:
      for i in range(0,len(path)-1):
        if path[i] == s and path[i+1] == d:
          return 1
    return 0

  def link_fail_handler(self,event,otopo):
    #print "Failure handler",event
    #print "\n %s \n"%(otopo.L)
    s = event['s'] 
    d = event['d']
    time = event["time"]
    tmpeventq = []
    nqueue = copy.deepcopy(self.queue)
    self.queue = []
    for fevent in nqueue:
      fevent = fevent[1]
      if fevent["type"] != 'flow-dep':
        self.insert(fevent)
        continue
      if self.check_link_in_paths(fevent["paths"],s,d) == 0:
        if self.check_link_in_paths(fevent["paths"],d,s) == 0:
          self.insert(fevent)
          continue
      #print "faildep"
      self.flow_dep_handler(fevent,otopo)
      #fevent["size"] = (fevent["time"] - time)*fevent["tput"]
      fevent["time"] = fevent["time"] - fevent["size"]/fevent["tput"]
      tmpeventq.append(fevent)

    #print "\n %s \n"%(otopo.L)
    otopo.L[s].pop(d)
    otopo.L[d].pop(s)
    #print otopo.L
    for topo_id in otopo.G:
      otopo.G[topo_id][s].pop(d)
      otopo.G[topo_id][d].pop(s)
      otopo.orouting.sptree(otopo.G[topo_id],topo_id)
      #print otopo.G[topo_id]
 
    for fevent in tmpeventq:
      #print "failarr"
      self.flow_arr_handler(fevent,otopo) 
    #print otopo.L
  
  def load_surge_handler(self,otm,event):
    type = event["surgetype"]
    if type == 'random':
      n = event['num']
      randsrc = rnd.sample(otm.tm.keys(),n)
      for s in randsrc:
        d = s
        while d == s:
          d = rnd.sample(otm.tm.keys(),1)[0]
        print "%s %s from %s "%(s,d,otm.tm[s][d])
        otm.tm[s][d] *= 2  
        print "to %s "%(otm.tm[s][d])
    if type == 'replace':
      print "replacing %s with "%(otm.FILE),
      id = event['id']
      otm.FILE = otm.FILE_base + "_" + str(id)
      print "%s"%(otm.FILE)
      otm.read()

  def static_load_handler(self,event,otopo):
    s = event["s"] 
    d = event["d"] 
    otopo.L[s][d]["load"] += event["load"]

