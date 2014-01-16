###### THIS IS STILL A WORK IN PROGRESS. 
#### srikanth@gatech.edu

To run, "./simulator"
A standard python installation should suffice.

Configuration in "input" file. Many different scenarios can
be simulated by changing various config parameters. Please note
that for IGP-WO, the link weights have to be fed in through the 
topo file. This simulator does not generate them. I used the
excellent Totem toolset by the UCL folks.

Output in data/output/<topo_name>/run<id>/
  - where <topo_name> is the specified topology name.
  - <id> is the id of the experiment with that topology. starts at 0.
  - to check the result of the last run, go to the largest id.
  - run<id> directory has dump of topology at each iteration, with
    - link loads, utilization, weights, key metrics applied. Note that
    - it only stores the info of the slice updated at that iteration. Only
    - one slice is updated durin one iteration. The state of all the
    - topologies are reflected in the previous n-1 files. It also has a
    - dump of the residual traffic in the network during that iteration.

If you have the matplotlib library and would like a nice plot of the
evolution of all the link loads, enable the call to 'plot' in simulator.py.
The plot will be in data/plots/...

There are 4 main classes, for managing topology, managing the traffic matrix,
generating flows, and managing events.

Topo:
  Structure G stores topology. Stores all slices. 
  Structure L stores link information like capacity, current load, etc.
  Instantiates routing object for routing flows.
  
TMC:
  Generates traffic matrix. Currently implements gravity model and bimodal model.

Flow:
  Generates and populates flows. Instantiates objects for specific kinds of 
  arrival process, size of flow, etc.

Event:
  Handles events. Arrival/departure of flows, link updates at iterations. 
  Arrivals are routed and link loads updated. Departures are taken off links.
  Instantiates specific object for link updates.
   
