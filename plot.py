import matplotlib.pyplot as plt
import os
import gen
import numpy as np
import sys
import gzip as gz

def plot_utils(fptr,idir,odir,nfiles):
  '''
    Fn to plot all link utilizations
  '''
  transdur= int(gen.get_param(fptr,"TRANS_DUR"))
  numslices = int(gen.get_param(fptr,"numslices"))
  init_pert = int(gen.get_param(fptr,"Range for Initial Random Wt"))
  iter_dur = int(gen.get_param(fptr,"ITER_DUR"))
  
  out = {}
  for i in range(1,nfiles):
    try:
      fp = gz.open(idir + str(i))
    except:
      break
    lines = fp.readlines()
    #print idir+str(i)
    for line in lines:
      #print line
      line = line.split() 
      link = line[0] + "-" + line[1]
      try:
        out[link].append(line[5])
      except:
        out[link] = []
    fp.close()
  
  #outlink = ["4-7","5-8","6-9"]
  outlink =  out
  #cr = 'Static Traffic on '
  #leg = [cr + "Link 1", cr + "Link 2", cr + 'Link 3'] 
  #fig = plt.figure(num=None, figsize=(8,3.5))
  #fig.subplots_adjust(bottom=0.15)
  p = []
  for link in outlink:
    x = range(0,len(out[link]))
    x = (np.array(x) - 200)*5
    p.append(plt.plot(x,out[link])[0])
    plt.ylim(ymin=0,ymax=1.5)
  #plt.title("#of topos:" + str(numslices) + \
   #" Iter duration:" + str(iter_dur))
   
  #plt.xlim(xmin=1000/iter_dur)
  #plt.xlim(xmin=0)
  plt.xlabel("Iterations",fontsize=18)
  plt.xlabel("Time",fontsize=18)
  plt.ylabel("Offered Load",fontsize=18)
  #plt.legend(p,leg,loc=0)
  plt.savefig(odir+"utilization-" + str(link) + ".eps")
  plt.clf()
      
def plot(fptr,rid = None):
  '''
    Fn to plot output. Get output dir from input config, call
    appropriate plotting fn
  '''
  output_dir = gen.get_param(fptr,"outdir") + "/"
  topo = gen.get_param(fptr,"topo_name") + "/"
  max = 0
  if rid == None:
    idir = output_dir + topo
    dir = os.listdir(idir)
    for d in dir:
      if "run" not in d:
        continue
      cid = int(d.split("run")[1])
      if cid > max:
        max = cid
    rid = max
    
  idir = output_dir + topo + "run"+str(rid) + "/"
  odir = idir.replace("output","plots")
  os.system("mkdir -p " + odir)
  simdur = int(gen.get_param(fptr,"SIM_DUR"))
  iter_dur = int(gen.get_param(fptr,"ITER_DUR"))
  nfiles = simdur/iter_dur
  plot_utils(fptr,idir,odir,nfiles)
  get_moving_avg(fptr,idir,odir,nfiles)
  plot_cmp(fptr,idir,odir,nfiles)
  

def get_moving_avg(fptr,idir,odir,nfiles):
  '''
    Fn to plot max link utilizations
  '''
  window = 20
  transdur= int(gen.get_param(fptr,"TRANS_DUR"))
  numslices = int(gen.get_param(fptr,"numslices"))
  init_pert = int(gen.get_param(fptr,"Range for Initial Random Wt"))
  iter_dur = int(gen.get_param(fptr,"ITER_DUR"))
  
  max = []
  for i in range(1,nfiles):
    try:
      fp = gz.open(idir + str(i))
    except:
      break
    util = 0
    lines = fp.readlines()
    for line in lines:
      line = line.split() 
      if float(line[5]) > util:
        util = float(line[5])
    max.append(util)
    fp.close()
  avgarr = []
  for i in range(window,len(max)):
    tmp = max[i-window:i+1]
    avg = np.average(tmp)
    avgarr.append(avg)
  fp = open(odir+"avgmax"+".txt","w")
  for i in range(1,window): 
    fp.write("%s %.2f 0\n"%(i,max[i]))
  for i in range(window,len(max)): 
    fp.write("%s %.2f %.2f\n"%(i,max[i-1],avgarr[i-window]))
  fp.close()


def plot_cmp(fptr,idir,odir,nfiles):
  odatdir = odir.replace("plots","output")
  print odatdir
  fip = gen.get_input(odatdir+"/input")
  topo_name = gen.get_param(fip,"topo_name")
  init_wt = gen.get_param(fip,"Initial Wt setting")
  algo = gen.get_param(fip,"link weight update")
  tm_name = gen.get_param(fip,"tm_name")
  
  fo = open("tmp","a")
  if algo.lower() == 'keymetric_ecmp':
    fo.write(" km %s\n"%(tm_name))
 
  if algo.lower() == 'static' and init_wt.lower() == 'inv_cap':
    fo.write(" inv_cap %s\n"%(tm_name))

  if algo.lower() == 'static' and init_wt.lower() == 'base_rand':
    fo.write(" thorup %s\n"%(tm_name))
  fo.close()
       
if __name__ == '__main__':
  start = int(sys.argv[1])
  end = int(sys.argv[2])
  #fb = "data/output/exp5/pste/rocketfuel_abilene/run" 
  fb = "data/output/conext/mate/pste/mate/run"

  for i in range(start,end+1):
    file = fb + str(i) + "/input"
    fptr = gen.get_input(file)
    fo = open("tmp","a")
    fo.write("%s "%(i))
    fo.close()
    plot(fptr,i)
