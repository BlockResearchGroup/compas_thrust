from scipy.optimize import fmin_slsqp
from compas.numerical import devo_numpy
from compas.numerical import ga

from compas_thrust.algorithms.problems import initialise_problem

from compas_thrust.algorithms.objectives import f_min_loadpath
from compas_thrust.algorithms.objectives import f_min_loadpath_pen
from compas_thrust.algorithms.objectives import f_min_thrust
from compas_thrust.algorithms.objectives import f_min_thrust_pen
from compas_thrust.algorithms.objectives import f_max_thrust
from compas_thrust.algorithms.objectives import f_target
from compas_thrust.algorithms.objectives import f_constant

from compas_thrust.algorithms.constraints import f_compression
from compas_thrust.algorithms.constraints import f_ub_lb
from compas_thrust.algorithms.constraints import f_joints
from compas_thrust.algorithms.constraints import f_cracks

from compas_thrust.algorithms.equilibrium import reactions

from compas_thrust.algorithms import zlq_from_qid
from compas.utilities import geometric_key

from numpy.random import rand
from numpy import append
from numpy import array

from compas_tna.diagrams import FormDiagram


__author__    = ['Ricardo Maia Avelino <mricardo@ethz.ch>']
__copyright__ = 'Copyright 2019, BLOCK Research Group - ETH Zurich'
__license__   = 'MIT License'
__email__     = 'mricardo@ethz.ch'


__all__ = [
    'optimise_general'
]


def optimise_general(form, solver='slsqp', qmin=1e-6, qmax=10, find_inds = True, tol = 0.001,
                    printout=10, plot=False, indset=None, tension=False, planar=False,
                    translation = None, use_bounds = None, bounds_width = 5.0,
                    summary = True, objective='loadpath', bmax = False):

    # Mapping

    k_i  = form.key_index()
    i_k  = form.index_key()
    i_uv = form.index_uv()
    uv_i = form.uv_index()

    # Set-up of the problem

    args = initialise_problem(form, indset=indset, printout=printout, find_inds=find_inds, tol=tol)
    q, ind, dep, E, Edinv, Ei, C, Ct, Ci, Cit, Cf, U, V, p, px, py, pz, z, free, fixed, lh, sym, k, lb, ub, lb_ind, ub_ind, s, Wfree, x, y = args
    print('lb',lb)
    print('len-lb',len(lb))
    print('ub',ub)
    print('len-ub',len(ub))

    # Problem specifities

    if bmax:
        b = []
        for key in form.vertices_where({'is_fixed': True}):
            try:
                [b_] = form.get_vertex_attributes(key, 'b')
                b.append(b_)
            except:
                pass
        b = array(b)
    else:
        b = None
    if printout and bmax:
        print('Reaction spread: {0}'.format(b))

    try:
        joints = form.attributes['joints']
    except:
        joints = None

    try:
        cracks_lb, cracks_ub = form.attributes['cracks']
    except:
        cracks_lb = []
        cracks_ub = []

    args = (q, ind, dep, E, Edinv, Ei, C, Ct, Ci, Cit, Cf, U, V, p, px, py, pz, z, free, fixed, lh, sym, k, lb, ub, lb_ind, ub_ind, s, Wfree, x, y, b, joints, cracks_lb, cracks_ub)

    # Select Objetive and Constraints

    if objective=='loadpath':
        fobj, fconstr = f_min_loadpath, f_compression
    if objective == 'constr_lp':
        fobj, fconstr = f_min_loadpath, f_ub_lb
    if objective == 'cracks_lp':
        fobj, fconstr = f_min_loadpath, f_cracks
    if objective == 'lp_joints':
        fobj, fconstr = f_min_loadpath_pen, f_joints
    if objective=='target':
        fobj, fconstr =  f_target, f_compression
    if objective == 'min':
        fobj, fconstr = f_min_thrust, f_ub_lb
    if objective == 'min_joints':
        fobj, fconstr = f_min_thrust_pen, f_joints
    if objective=='max':
        fobj, fconstr =  f_max_thrust, f_ub_lb
    if objective == 'feasibility':
        fobj, fconstr = f_constant, f_joints

    # Definition of the Variables and starting point

    if translation:
        x0 = q[ind]
        bounds = [[qmin, qmax]] * k + [[-1*10, translation]] * len(fixed)
        x0 = append(x0[0],z[fixed]).reshape(-1,1)
    else:
        x0 = q[ind]
        bounds = [[qmin, qmax]] * k

    print('Independents:', ind)
    print('Initial stepbefore:', x0)
    f0 = fobj(x0, *args)
    
    if printout:
        print('Gradient Method: Initial Value: {0}'.format(f0))
        print('Initial step:', x0)

    # Solve with the appropriate solver

    if solver == 'slsqp':
        fopt, xopt, exitflag, niter, message = _slsqp(fobj, x0, bounds, printout, fconstr, args)
        while exitflag == 9:
            fopt, xopt, exitflag, niter, message = _slsqp(fobj, xopt, bounds, printout, fconstr, args)
        if exitflag == 0:
            if translation:
                q[ind] = xopt[:k]
                z[fixed] = xopt[k:].reshape(-1,1)
            else:
                q[ind] = xopt[:k]
        else:
            if printout:
                print(message)

    if solver == 'devo':
        fopt, xopt = _diff_evo(fn = fobj, bounds = bounds, population= 500, generations = 100, printout= 10, plot = False, frange=[], args = args)
        xopt = array(xopt).reshape(len(xopt),1)
        niter = 100
        exitflag = 0
        if translation:
            q[ind] = xopt[:k]
            z[fixed] = xopt[k:].reshape(-1,1)
        else:
            q[ind] = xopt[:k]

    if solver == 'ga':
        GA = _ga(fn = fobj, fit_type = 'min', num_var = len(x0), boundaries = bounds, num_pop= 500, num_gen = 300, args = args)
        fopt = float(GA.best_fit)
        best_i = GA.best_individual_index
        xopt = array(GA.current_pop['scaled'][best_i]).reshape(-1,1)
        niter = 100
        exitflag = 0
        if translation:
            q[ind] = xopt[:k]
            z[fixed] = xopt[k:].reshape(-1,1)
        else:
            q[ind] = xopt[:k]

    if solver == 'cvx':
        fopt, xopt = _cvx(fobj,args)

    # Recalculate equilibrium and update form-diagram

    args = (q, ind, dep, E, Edinv, Ei, C, Ct, Ci, Cit, Cf, U, V, p, px, py, pz, z, free, fixed, lh, sym, k, lb, ub, lb_ind, ub_ind, s, Wfree, x, y, b, joints, i_uv, k_i)
    z, _, q, q_ = zlq_from_qid(q[ind], args)

    print('qid',q[ind])

    gkeys = []
    for i in ind:
        u, v = i_uv[i]
        gkeys.append(geometric_key(form.edge_midpoint(u, v)[:2] + [0]))
    form.attributes['indset'] = gkeys

    for i in range(form.number_of_vertices()):
        key = i_k[i]
        form.set_vertex_attribute(key=key, name='z', value=float(z[i]))

    for c, qi in enumerate(list(q_.ravel())):
        u, v = i_uv[c]
        form.set_edge_attribute((u, v), 'q', float(qi))

    lp = 0
    for u, v in form.edges():
        if form.get_edge_attribute((u, v), 'is_symmetry') is False:
            qi = form.get_edge_attribute((u, v), 'q')
            li = form.edge_length(u, v)
            lp += abs(qi) * li**2
    form.attributes['loadpath'] = lp

    form.attributes['iter'] = niter
    form.attributes['exitflag'] = exitflag
    reactions(form, plot = plot)

    if summary:
        print('\n' + '-' * 50)
        print('qid range : {0:.3f} : {1:.3f}'.format(min(q[ind])[0], max(q[ind])[0]))
        print('q range   : {0:.3f} : {1:.3f}'.format(min(q)[0], max(q)[0]))
        print('zb range : {0:.3f} : {1:.3f}'.format(min(z[fixed])[0], max(z[fixed])[0]))
        print('fopt      : {0:.3f}'.format(fopt))
        print('-' * 50 + '\n')

    return fopt, q[ind], z[fixed], exitflag

def feasibility(form):

    # W.I.P.

    return


def _slsqp(fn, qid0, bounds, printout, fieq, args):

    pout = 2 if printout else 0
    opt  = fmin_slsqp(fn, qid0, args=args, disp=pout, bounds=bounds, full_output=1, iter=500, f_ieqcons=fieq)

    return opt[1], opt[0], opt[3], opt[2], opt[4]


def _cobyla(fn, qid0, bounds, printout, fieq, args):

    # pout = 2 if printout else 0
    # opt  = fmin_cobyla(fn, qid0, args=args, disp=pout, bounds=bounds, full_output=1, iter=500, f_ieqcons=fieq)

    # W.I.P

    return None

def _diff_evo(fn, bounds, population, generations, printout, plot, frange, args):

    return devo_numpy(fn=fn, bounds=bounds, population=population, generations=generations, printout=printout,
                      plot=plot, frange=frange, args=args)

def _ga(fn, fit_type, num_var, boundaries, num_gen, num_pop, args):
    
    return ga(fit_function=fn,fit_type = fit_type, num_var = num_var, boundaries = boundaries, num_gen = num_gen, num_pop = num_pop, fargs = args)


def _cvx(fobj,args):

    q, ind, dep, E, Edinv, Ei, C, Ct, Ci, Cit, Cf, U, V, p, px, py, pz, z, free, fixed, lh, sym, k, lb, ub, lb_ind, ub_ind, s, Wfree, x, y, b, joints, i_uv, k_i = args
    
    import matlab.engine

    # file = '/Users/mricardo/Documents/MATLAB/optimisation/discretize/test.mat'

    # savemat(file,{
    #     'm': int(form.number_of_edges()),
    #     'n': int(form.number_of_vertices()),
    #     'ni': len(free),
    #     'C': C,
    #     'Ci': Ci,
    #     'Cf': Cf,
    #     'Cit': Cit,
    #     'x': x,
    #     'y': y,
    #     'xb': x[fixed],
    #     'yb': y[fixed],
    #     'pz': pz[free],
    #     'free': free,
    #     'fixed': fixed,
    #     'p': p,
    #     'E': E,
    #     })

    eng = matlab.engine.start_matlab()
    eng.workspace['m'] = int(len(q))
    eng.workspace['C'] = matlab.double(C.toarray().tolist()) #C.todense()
    eng.workspace['Ci'] = matlab.double(Ci.toarray().tolist()) #Ci.todense()
    eng.workspace['Cf'] = matlab.double(Cf.toarray().tolist()) #Cf.todense()
    eng.workspace['Cit'] = matlab.double(Cit.toarray().tolist()) #Cit.todense()
    eng.workspace['xt'] = matlab.double(x.transpose().tolist())
    eng.workspace['yt'] = matlab.double(y.transpose().tolist())
    eng.workspace['xb'] = matlab.double(x[fixed].tolist())
    eng.workspace['yb'] = matlab.double(y[fixed].tolist())
    eng.workspace['pz'] = matlab.double(pz[free].tolist())
    eng.workspace['E'] = matlab.double(E.tolist()) #E.todense()
    # eng.load('/Users/mricardo/Documents/MATLAB/optimisation/discretize/nosym_02_06_p_140.mat', nargout=0)
    eng.cvx_begin(nargout=0)
    eng.variable('q(double(m))', nargout = 0)
    eng.minimize('matrix_frac(pz,(Cit*diag(q)*Ci)) + xt*transpose(C)*diag(q)*Cf*xb + yt*transpose(C)*diag(q)*Cf*yb',nargout=0)
    eng.eval('q >= 0.0', nargout = 0)
    eng.eval('q <= 100.0', nargout = 0)
    eng.eval('E*q == 0.0', nargout = 0)
    eng.cvx_end(nargout=0)

    fopt = eng.workspace['cvx_optval']
    qopt = array(eng.workspace['q'])
    xopt = qopt[ind]

    return fopt, xopt


