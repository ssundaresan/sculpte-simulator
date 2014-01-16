import route
import gen 
import sys
import copy
import numpy as np

class keymetric_base(object):
  '''
    Class keymetric to perturb link weight using key metrics
  '''
  def __init__(self,fptr,otopo):
    self.oroute = route.fluidecmproute(otopo.G) # obj oroute uses fluid ecmp
     # -  model this ensures we get all paths that pass through a (s,d) pair #
    self.nkeymetric = int(gen.get_param(fptr,"Number of Key metrics"))
    self.links_to_avoid = gen.get_param(fptr,"Links to avoid criterion")
    #if self.links_to_avoid.lower() == 'topn': 
    self.perc_nlinks_to_avoid = float(gen.get_param(fptr,"Maximum percentage of links to avoid"))
    if self.links_to_avoid.lower() in ['skew','combo','rescap','rescapnorm'] : 
      self.skew_threshold = float(gen.get_param(fptr,"Skew threshold"))
      self.maxrescap = float(gen.get_param(fptr,"Max residual capacity"))
      #max_nlinks_to_avoid = int(gen.get_param(fptr,"Maximum number of links to avoid"))
    totnlinks = otopo.count_nlinks()
    max_nlinks_to_avoid = self.perc_nlinks_to_avoid * totnlinks
    nperclinks = int(np.ceil(self.perc_nlinks_to_avoid*totnlinks))
    self.max_nlinks_to_avoid = max(nperclinks,max_nlinks_to_avoid)
    print 'Max nlinks to avoid %s'%(self.max_nlinks_to_avoid)

    self.thres_theta = float(gen.get_param(fptr,"Threshold theta"))
 
  def get_nranked_util_link(self,otopo,rank):
    '''
      Fn to get the top n utilized links
    '''
    arr = []
    for s in otopo.L:
      for d in otopo.L[s]:
        load = otopo.L[s][d]["load"]
        cap = otopo.L[s][d]["cap"]
        rec = {"s":s,"d":d,"load":load,"cap":cap}
        arr.append(rec)
    arr.sort(lambda x,y:cmp(x["load"]/x["cap"],y["load"]/y["cap"]))
    arr.reverse()
    links = []
    for i in range(0,rank):
      links.append(arr[i])
    return links

  def get_nranked_skew_link(self,otopo):
    '''
      Fn to get the top skew links
    '''
    links = []
    max_load_links = self.get_nranked_util_link(otopo,self.max_nlinks_to_avoid)
    max_load_util = max_load_links[0]['load']/max_load_links[0]['cap']
    for link in max_load_links:
      util = link["load"]/link["cap"]
      if util/max_load_util > self.skew_threshold:
        links.append(link)
      else:
        break
    self.nlinks_to_avoid = len(links)
    #print 'links to avoid ',links
    return links

  def get_nranked_combo_link(self,otopo):
    '''
      Fn to get the top skew + residual cap links
    '''
    links = self.get_nranked_skew_link(otopo)
    if len(links) > self.max_nlinks_to_avoid/2:
      links = links[0:self.max_nlinks_to_avoid/2]
    arr = []
    for s in otopo.L:
      for d in otopo.L[s]:
        load = otopo.L[s][d]["load"]
        cap = otopo.L[s][d]["cap"]
        rec = {"s":s,"d":d,"load":load,"cap":cap}
        arr.append(rec)
    arr.sort(lambda x,y:cmp(x["cap"]-x["load"],y["cap"]-y["load"]))
    for i in range(0,self.max_nlinks_to_avoid):
      if arr[i] not in links:
        links.append(arr[i])
    self.nlinks_to_avoid = len(links)
    return links

  def get_nranked_rescap_link(self,otopo):
    '''
      Fn to get the top residual cap links
    '''
    links = self.get_nranked_util_link(otopo,self.max_nlinks_to_avoid/2)
    maxutil = float(links[0]['load'])/links[0]['cap']
    rescaplim = links[0]['load']*self.maxrescap
    for link in links:
      linkrescap = link['cap']*maxutil - link['load']
      if linkrescap > rescaplim:
        links.remove(link)
    arr = []
    for s in otopo.L:
      for d in otopo.L[s]:
        load = otopo.L[s][d]["load"]
        cap = otopo.L[s][d]["cap"]
        rec = {"s":s,"d":d,"load":load,"cap":cap}
        arr.append(rec)
    arr.sort(lambda x,y:cmp((x["cap"]-x["load"]),(y["cap"]-y["load"])))
    for i in range(0,self.max_nlinks_to_avoid):
      if arr[i] not in links:
        links.append(arr[i])
    self.nlinks_to_avoid = len(links)
    #links.sort(lambda x,y:cmp((x["cap"]-x["load"]),(y["cap"]-y["load"])))
    return links

  def get_nranked_rescapnorm_link(self,otopo):
    '''
      Fn to get the top residual cap links
    '''
    links = self.get_nranked_util_link(otopo,1)
    maxutil = float(links[0]['load'])/links[0]['cap']
    print 'Maxutil %.3f'%(maxutil)
    arr = []
    for s in otopo.L:
      for d in otopo.L[s]:
        load = otopo.L[s][d]["load"]
        cap = otopo.L[s][d]["cap"]
        rec = {"s":s,"d":d,"load":load,"cap":cap}
        arr.append(rec)
    arr.sort(lambda x,y:cmp(((maxutil*x["cap"])-x["load"]),((maxutil*y["cap"])-y["load"])))
    maxrescap = self.maxrescap*arr[0]['cap']
    print 'Maxrescap %.1f'%(maxrescap)
    for i in range(0,self.max_nlinks_to_avoid):
      if arr[i] not in links:
        if maxutil*arr[i]['cap']-arr[i]['load'] > maxrescap:
          break
        links.append(arr[i])
    self.nlinks_to_avoid = len(links)
    return links
  
  def get_links_to_avoid(self,otopo):#,rank):
    '''
      Fn to get links to avoid
    '''
    links = []
    if self.links_to_avoid.lower() == 'skew': 
      links = self.get_nranked_skew_link(otopo)#,rank)
    if self.links_to_avoid.lower() == 'combo': 
      links = self.get_nranked_combo_link(otopo)#,rank)
    if self.links_to_avoid.lower() == 'rescap': 
      links = self.get_nranked_rescap_link(otopo)#,rank)
    if self.links_to_avoid.lower() == 'rescapnorm': 
      links = self.get_nranked_rescapnorm_link(otopo)#,rank)
    if self.links_to_avoid.lower() == 'topn': 
      rank = self.max_nlinks_to_avoid
      links = self.get_nranked_util_link(otopo,rank)
    return links 
    
  def get_paths_thru_link(self,otopo,topo_id,sc,dc):
    '''
      Fn to return all shortest paths through (s,d) pair current slice
       uses fluid ecmp routing
    '''
    print "Current topo %s, congested link %s-%s"%(topo_id,sc,dc)
    allpaths = self.oroute.all_sd_paths(otopo.G[topo_id],topo_id,1)  
    #print "allpaths"
    #for n in allpaths:
      #print "%s %s"%(n,allpaths[n])
    sdpaths = []
    for s in allpaths:
      for d in allpaths[s]:
        for path in allpaths[s][d]:
          if sc not in path or dc not in path:
            continue
          ks = path.index(sc)
          kd = path.index(dc)
          if ks == kd-1:
            sdpaths.append(path)
    return sdpaths

  def get_cost_of_path(self,topo,path):
    '''
      Fn to return cost of path in current topo
    '''
    cost = 0
    for i in range(0,len(path)-1):
      cost += topo[path[i]][path[i+1]]["wt"]
    if len(path) == 0:
      print "cost for null path is %s"%(cost)
    return cost

  def get_key_metric(self,otopo,topo_id,sdpaths,links_to_avoid):
    '''
      Calculates keymetric for link, with the top n utilized links
       taken out of the topology. 
       For all shortest paths through the link (in sdpaths), the one with
        the smallest key metric is chosen
       If there are no alternate paths without the links to avoid, then
        the kmetric is 0, which the calling function should interpret as
        meaning that at least 1 link in links_to_avoid is essential
    '''
    carr = []
    tmp_disc_links = []
    s=''
    d=''
    cmin = -1
    ncost = 0
    npath = ''
    tmptopo = copy.deepcopy(otopo.G[topo_id])
    ##print "topo before cull %s"%(tmptopo)
    ##print "links to avoid %s"%(links_to_avoid)
    for link in links_to_avoid:
      ##print "culling link %s"%(link)
      tmp_disc_links.append({"s":link["s"],"d":link["d"],\
       "l":tmptopo[link["s"]].pop(link["d"])})
    for path in sdpaths:
      #print "path ",path
      costorig  = self.get_cost_of_path(otopo.G[topo_id],path)
      altpath = self.oroute.paths(tmptopo,topo_id,path[0],path[len(path)-1],0,1)
      if len(altpath) > 0:
        costnew = self.get_cost_of_path(tmptopo,altpath[0])
      else:
        costnew = 0
      costdiff = costnew - costorig 
      if costnew == 0:
        continue 
      if costdiff < cmin or cmin < 0:
        cmin = costdiff
        s = path[0]
        d = path[len(path)-1]
        ncost = costnew
        ocost = costorig
        npath = altpath
        opath = path
      if cmin == -1:
        path = sdpaths[0] 
        s = path[0]
        d = path[len(path)-1]

    km = cmin + 1
    if km:
      print 'orig path is %s'%(opath)
      print "path with lowest km is %s"%(npath)
    else:
      print "topo disconnect"
    #print "getting npath %s %s in culled topo %s"%(s,d,tmptopo)
    #print "orig path %s cost %s"%(opath,ocost)
    #print "path in culled topo %s cost %s"%(npath,ncost)
    return km,ncost,s,d
    
  def check_condition(self,otopo,topo_id):
    '''
      Checks condition of defined "good" load balance.
       returns 1 if satisifed, else returns 0
    '''
    max_load_link = self.get_nranked_util_link(otopo,1)
    print "Max load link %s"%(max_load_link)
    if (max_load_link[0]["load"]/max_load_link[0]["cap"]) <= self.thres_theta:
      print "Max load under threshold"
      return 1
    else:
      print "Max load over threshold"
      return 0
    
  def linkupdate(self,otopo,topo_id):
    '''
      Fn to determine check for condition on link update.
       If condition satisfies, nothing is done.
       If condition fails, then links are updated.
    '''
    val = self.check_condition(otopo,topo_id)
    if val == 1:
      return
    else:
      self.update(otopo,topo_id)

  def check_link_in_list(self,arr,s,d):
    '''
      Fn to see if link (s,d) is in array of links arr.
        Return 1 if it is, else 0
    '''
    for rec in arr:
      if rec["s"] == s and rec["d"] == d:
        return 1
    return 0

  def check_link_in_paths(self,paths,s,d):
    '''
      Fn to see if link (s,d) is in any path in paths.
        Return 1 if it is, else 0
    '''
    for path in paths:
      for i in range(0,len(path)-1):
        if path[i] == s and path[i+1] == d:
          return 1,path
    return 0,[]

  def get_path_km(self,otopo,topo_id):
    '''
      Fn to find the maximal set of links that can be avoided. this is
      - is done by starting with the max allowed - nlinks_to_avoid. 
      - if the topo without that set becomes disconnected for all the paths
      - that pass through the most utilized link, then nlinks_to_avoid is 
      - reduced by 1 by removing the least loaded of the links in that set. #
    '''

    i = 0
    s = '' # the src/dst of the path with lowest km
    d = ''
    ##print "number of links to avoid = %s"%(self.nlinks_to_avoid)
    links_to_avoid = self.get_links_to_avoid(otopo)
    self.nlinks_to_avoid = len(links_to_avoid)
    for i in range(0,self.nlinks_to_avoid):
      #links_to_avoid = self.get_nranked_util_link(otopo,self.nlinks_to_avoid)
      links_to_avoid = self.get_links_to_avoid(otopo)#,self.nlinks_to_avoid)
      print "links to avoid %s"%(links_to_avoid)
      sc = links_to_avoid[i]["s"]
      dc = links_to_avoid[i]["d"]
      sdpaths = self.get_paths_thru_link(otopo,topo_id,sc,dc)
      ##print "rank %s all paths through %s,%s - %s"%(i,sc,dc,sdpaths)
      if len(sdpaths) == 0:
        return 0,0,'','','','',[]
      while (len(links_to_avoid)-i):
        km,ncost,s,d = self.get_key_metric(otopo,topo_id,sdpaths,links_to_avoid)
        if km != 0:
          break
        links_to_avoid = links_to_avoid[0:len(links_to_avoid)-1]
      if km != 0:
        break
    return km,ncost,sc,dc,s,d,links_to_avoid

class keymetric_ecmp(keymetric_base):
  def update(self,otopo,topo_id):
    km,ncost,sc,dc,s,d,links_to_avoid = self.get_path_km(otopo,topo_id)
    km -= 1
    if km == -1:
      return
    if km == 0:
      otopo.G[topo_id][sc][dc]["wt"] += 1
      otopo.G[topo_id][sc][dc]["pt"] = 1
      print "km 0 link %s %s has km %s"%(sc,dc,1)
      return
    if km > 0:
       km_int = 0
       origcost = ncost - km
       tmptopo = copy.deepcopy(otopo.G[topo_id])
       tmp_links = []
       for link in links_to_avoid:
         tmp_links.append(tmptopo[link["s"]].pop(link["d"]))
       for i in range(len(links_to_avoid)-1,-1,-1):
         link = links_to_avoid[i]
         tmptopo[link["s"]][link["d"]] = tmp_links[i]
         altpath = self.oroute.paths(tmptopo,topo_id,s,d,0,1)
         #check,path = self.check_link_in_paths(altpath,link["s"],link["d"])
         cost = self.get_cost_of_path(tmptopo,altpath[0])
         print "altpath = %s, cost = %s"%(altpath,cost)
         #km_int = cost - origcost
         km_int = ncost - cost 
         otopo.G[topo_id][link["s"]][link["d"]]["wt"] += km_int
         otopo.G[topo_id][link["s"]][link["d"]]["pt"] = km_int
         print "in loop: link %s %s has km %s ncost %s cost %s path %s"%(link["s"],link["d"],km_int,ncost,cost,altpath)
           
#      otopo.G[topo_id][sc][dc]["wt"] += km
#      otopo.G[topo_id][sc][dc]["pt"] = km
#      print "link %s %s has km %s"%(sc,dc,km)
#      while 1:
#        npaths = self.oroute.paths(otopo.G[topo_id],topo_id,s,d,0,1)
#        print "checking for %s %s in %s"%(sc,dc,npaths)
#        check,path = self.check_link_in_paths(npaths,sc,dc)
#        if check: 
#          break
#        else:
#          for link in links_to_avoid:
#            check,path = self.check_link_in_paths(npaths,link["s"],link["d"])
#            if check == 1:
#              cost = self.get_cost_of_path(otopo.G[topo_id],path)
#              km = ncost-cost
#              otopo.G[topo_id][link["s"]][link["d"]]["wt"] += km
#              otopo.G[topo_id][link["s"]][link["d"]]["pt"] = km
#              npaths = self.oroute.paths(otopo.G[topo_id],topo_id,s,d,0,1)
#              print "in loop: link %s %s has km %s ncost %s cost %s path %s"%(link["s"],link["d"],km,ncost,cost,path)
#              continue
          
      

class keymetric_std(keymetric_base):
  def update(self,otopo,topo_id):
    '''
      Fn update applies keymetric to all links.
       first it finds the maximum set of highly utilized links it can avoid.
       that set is upper bound by nlinks_to_avoid.
       then it applies the minimum required key metric to all the links
        in that set so that the alternate path without those links becomes
        the shortest path.
    '''
    km,ncost,sc,dc,s,d,links_to_avoid = self.get_path_km(otopo,topo_id)
    if km == 0:
      return

    otopo.G[topo_id][sc][dc]["wt"] += km
    otopo.G[topo_id][sc][dc]["pt"] = km
    print "link %s %s has km %s"%(sc,dc,km)

    # part 2 - the key metric is applied to all links in links_to_avoid
    # - so that the path without any of them becomes shortest path. 
    # - the key metric iscalculated for each separately. #
    while 1:
      npaths = self.oroute.paths(otopo.G[topo_id],topo_id,s,d,0,1)
      print "all paths in current topo %s"%(npaths)
      flag = 0
      for npath in npaths:
        for i in range(0,len(npath)-1):
          if self.check_link_in_list(links_to_avoid,npath[i],npath[i+1]):
            sc = npath[i]
            dc = npath[i+1]
            cost = self.get_cost_of_path(otopo.G[topo_id],npath)
            km = ncost-cost + 1
            if km <= 0:
              print "Critical error: key metric < 1"
              sys.exit(1)
            otopo.G[topo_id][sc][dc]["wt"] += km
            otopo.G[topo_id][sc][dc]["pt"] = km
            print "link %s %s has km %s"%(sc,dc,km)
            flag = 1
            break
        if flag == 1:
           break
      if flag == 0:
         break

