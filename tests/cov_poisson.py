from samcnet.mixturepoisson import *
import numpy as np
import pylab as p
import tables as t
import samcnet.samc as samc
import samcnet.mh as mh

from samcnet.lori import *
from math import exp,log

import scipy.stats as st
import scipy.stats.distributions as di
import scipy
import nlopt
import subprocess as sb
import os
import os.path as path
from scipy.special import gammaln

N = 1000
rho = -0.97
cov = np.array([[1, rho],[rho, 1]])
lams = MVNormal(np.ones(2), cov).rvs(30)

ps = np.empty_like(lams)
for i in xrange(lams.shape[0]):
	for j in xrange(lams.shape[1]):
		ps[i,j] = di.poisson.rvs(5* np.exp(lams[i,j]))


n,gext,grid = get_grid_data(ps, positive=True)
#dist = MPMDist(ps,kappa=5,S=np.eye(2)+np.ones((2,2))*3,kmax=1)

kappa = 10
#S = np.array([[1, -.5],[-.5,1]]) * kappa
S = np.eye(2) * kappa
dist = MPMDist(ps,kappa=kappa,S=S,kmax=1)
mh = mh.MHRun(dist, burn=0, thin=10)
mh.sample(1e2,verbose=False)

gavg = dist.calc_db_g(mh.db, mh.db.root.object, grid).reshape(-1,n)

p.subplot(2,2,1)
p.imshow(gavg, extent=gext, aspect=1, origin='lower')
p.colorbar()
p.plot(ps[:,0], ps[:,1], 'k.')

def log_poisson(k,lam):
	return log(lam) * k - gammaln(k+1) - lam

p.subplot(2,2,2)
######### avg avg
mus = mh.db.root.object.mu.read()
sigmas = mh.db.root.object.sigma.read()
numsamps = mus.shape[0]
mapd = 10
N = 100
avgavg = np.zeros(grid.shape[0])
for i in xrange(numsamps):
	lamdist = MVNormal(mus[i,:,0], sigmas[i])
	lam = lamdist.rvs(N)
	for j in xrange(N):
		avgavg[:] += np.exp(log_poisson(grid[:,0], mapd*np.exp(lam[j,0])) \
					+ log_poisson(grid[:,1], mapd*np.exp(lam[j,1])))
avgavg /= N*numsamps
avgavg = np.log(avgavg).reshape(-1,n)

p.imshow(avgavg, extent=gext, aspect=1, origin='lower')
#p.colorbar()
p.plot(ps[:,0], ps[:,1], 'k.')

##### map lambda
#mapd, maplam = mh.mapvalue[3], mh.mapvalue[5]
#mlg = (log_poisson(grid[:,0], mapd*np.exp(maplam[0])) \
	#+ log_poisson(grid[:,1], mapd*np.exp(maplam[1]))).reshape(-1,n)
#p.imshow(mlg, extent=gext, aspect=1, origin='lower')
#p.plot(ps[:,0], ps[:,1], 'k.')

p.subplot(2,2,3)
######## avg lambda
mapmu, mapsigma = mh.mapvalue[:2]

lamdist = MVNormal(mapmu[:,0], mapsigma)
N = 1000
lam = lamdist.rvs(N)
avglg = np.zeros(grid.shape[0])
print(mapsigma)
for i in xrange(N):
	avglg[:] += np.exp(log_poisson(grid[:,0], mapd*np.exp(lam[i,0])) \
				+ log_poisson(grid[:,1], mapd*np.exp(lam[i,1])))
avglg /= N
avglg = np.log(avglg).reshape(-1,n)

p.imshow(avglg, extent=gext, aspect=1, origin='lower')
#p.colorbar()
p.plot(ps[:,0], ps[:,1], 'k.')

from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from matplotlib.ticker import LinearLocator, FormatStrFormatter

#fig = p.figure()
#ax = fig.gca(projection='3d')
#X = np.linspace(gext[0], gext[1], n)
#Y = np.linspace(gext[0], gext[1], n)
#X, Y = np.meshgrid(X, Y)
#surf = ax.plot_surface(X, Y, avglg, rstride=1, cstride=1, cmap=cm.coolwarm,
        #linewidth=0, antialiased=False)
#fig = p.figure()
#ax = fig.gca(projection='3d')
#surf = ax.plot_surface(X, Y, avgavg, rstride=1, cstride=1, cmap=cm.coolwarm,
        #linewidth=0, antialiased=False)

############ STAN ###############

from samcnet.utils import stan_vec
open('../stan/data.R','w').write(stan_vec(
	samples=ps.astype(np.int), 
	num_samples=ps.shape[0], 
	num_features=2,
	nu = 5,
	S = 5*np.array([[1,-0.9],[-0.9,1]]),
	#S = 4*np.eye(2),
	prior_mu = np.zeros(2),
	lowd = 9,
	highd = 10))
os.chdir('../stan')
sb.check_call( 
    './mpm --data=data.R --iter=5000 --warmup=1000 --refresh=1000 --samples=samples2.csv'.split())
os.chdir('../samcnet')
stan_samps = np.genfromtxt('../stan/samples2.csv', names=True, skip_header=25, delimiter=',')
N = stan_samps.shape[0]
lam = np.vstack(( stan_samps['lam1'], stan_samps['lam2'] )).T
d = stan_samps['d']
avglg = np.zeros(grid.shape[0])
for i in xrange(N):
	avglg[:] += np.exp(log_poisson(grid[:,0], d[i]*np.exp(lam[i,0])) \
				+ log_poisson(grid[:,1], d[i]*np.exp(lam[i,1])))
avglg /= N
avglg = np.log(avglg).reshape(-1,n)

p.subplot(2,2,4)
p.imshow(avglg, extent=gext, aspect=1, origin='lower')
#p.colorbar()
p.plot(ps[:,0], ps[:,1], 'k.')

p.show()