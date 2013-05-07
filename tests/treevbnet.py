import sys, os, random
import numpy as np
import scipy as sp
import networkx as nx
import json as js
import tables as t
import zlib
import cPickle
import time as gtime
import pylab as p

from samcnet.samc import SAMCRun
from samcnet.treenet import TreeNet, generateTree, generateData
from samcnet.bayesnetcpd import BayesNetSampler, BayesNetCPD
from samcnet import utils
from samcnet.generator import sampleTemplate
import samcnet.generator as gen

N = 3
comps = 2
iters = 3e5
numdata = 0
burn = 1000
stepscale = 30000
temperature = 1.0
thin = 50
refden = 0.0
numtemplate = 10
priorweight = 0.0

random.seed(12345)
np.random.seed(12345)

groundgraph = generateTree(N, comps)
data = generateData(groundgraph,numdata)
template = sampleTemplate(groundgraph, numtemplate)

random.seed()
np.random.seed()

############### TreeNet ##############

groundtree = TreeNet(N, data=data, graph=groundgraph)
b1 = TreeNet(N, data, template, priorweight, groundtree)
#s1 = SAMCRun(b1,burn,stepscale,refden,thin)
#s1.sample(iters, temperature)

############## bayesnetcpd ############

joint = utils.graph_to_joint(groundgraph)
states = np.ones(len(joint.dists),dtype=np.int32)*2
groundbnet = BayesNetCPD(states, data)
groundbnet.set_cpds(joint)

obj = BayesNetCPD(states, data)
b2 = BayesNetSampler(obj, template, groundbnet, priorweight)
#s2 = SAMCRun(b2,burn,stepscale,refden,thin)
#s2.sample(iters, temperature)
    
#######################################

b2.bayesnet.adjust_factor(1,[2],[])
b2.bayesnet.set_factor(1,[0.9,0.1,0.9,0.1])

b1.add_edge(2,1,0.9,0.1)



