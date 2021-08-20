import cyipopt

import time

from numpy import hstack
from numpy import array

try:
    from torch import tensor

    from compas_tno.algorithms.equilibrium_pytorch import f_constraints_pytorch
    from compas_tno.algorithms.equilibrium_pytorch import f_objective_pytorch
    from compas_tno.algorithms.equilibrium_pytorch import compute_autograd
    from compas_tno.algorithms.equilibrium_pytorch import compute_autograd_jacobian
except BaseException:
    pass  # Module tensor not available

from .post_process import post_process_general


__all__ = [
    'run_optimisation_ipopt'
]


class wrapper_ipopt(object):
    def __init__(self):
        self.fobj = None
        self.fconstr = None
        self.args_obj = None
        self.args_constr = None
        self.bounds = None
        self.x0 = None
        self.eps = 1e-8
        pass

    def objective(self, x):
        #
        # The callback for calculating the objective
        #
        variables = tensor(x.reshape(-1, 1))
        return array(self.fobj(variables, *self.args_obj))

    def gradient(self, x):
        #
        # The callback for calculating the gradient
        #
        variables = tensor(x.reshape(-1, 1), requires_grad=True)
        f = self.fobj(variables, *self.args_obj)
        return array(compute_autograd(variables, f))

    def constraints(self, x):
        #
        # The callback for calculating the constraints
        #
        variables = tensor(x.reshape(-1, 1))
        return array(self.fconstr(variables, *self.args_constr))

    def jacobian(self, x):
        #
        # The callback for calculating the Jacobian
        #
        variables = tensor(x.reshape(-1, 1), requires_grad=True)
        constraints = self.fconstr(variables, *self.args_constr)
        return array(compute_autograd_jacobian(variables, constraints)).flatten()


class wrapper_ipopt_analytical(object):
    def __init__(self):
        self.fobj = None
        self.fconstr = None
        self.args = None
        self.fgrad = None
        self.bounds = None
        self.x0 = None
        self.eps = 1e-8
        self.fjac = None
        pass

    def objective(self, x):
        #
        # The callback for calculating the objective
        #
        return self.fobj(x, *self.args)

    def gradient(self, x):
        #
        # The callback for calculating the gradient
        #
        return self.fgrad(x, *self.args)

    def constraints(self, x):
        #
        # The callback for calculating the constraints
        #
        return self.fconstr(x, *self.args).reshape(-1, 1)

    def jacobian(self, x):
        #
        # The callback for calculating the Jacobian
        #
        return self.fjac(x, *self.args).flatten()


def run_optimisation_ipopt(analysis):
    """ Run nonlinear optimisation problem with IPOPT

    Parameters
    ----------
    obj : analysis
        Analysis object with information about optimiser, form and shape.

    Returns
    -------
    obj : analysis
        Analysis object optimised.

    """

    optimiser = analysis.optimiser

    constraints = optimiser.settings['constraints']
    objective = optimiser.settings['objective']
    printout = optimiser.settings.get('printout', False)
    gradients = optimiser.settings.get('gradient', False)
    variables = optimiser.settings['variables']

    bounds = optimiser.bounds
    x0 = optimiser.x0
    g0 = optimiser.g0
    args = [optimiser.M]

    lower = [lw[0] for lw in bounds]
    upper = [up[1] for up in bounds]

    # Tensor modification

    if not gradients:

        (q, ind, dep, E, Edinv, Ei, C, Ct, Ci, Cit, Cf, U, V, p, px, py, pz, z, free, fixed, lh, sym, k, lb, ub, lb_ind, ub_ind, s, Wfree, x, y, b, joints, cracks_lb, cracks_ub,
         free_x, free_y, rol_x, rol_y, Citx, City, Cftx, Cfty, qmin, constraints, max_rol_rx, max_rol_ry, Asym) = args[:48]

        EdinvEi = Edinv*Ei
        Edinv_p = Edinv.dot(p)

        EdinvEi_th = tensor(EdinvEi)
        Edinv_p_th = tensor(Edinv_p)
        C_th = tensor(C.toarray())
        Ci_th = tensor(Ci.toarray())
        Cit_th = Ci_th.t()
        Cf_th = tensor(Cf.toarray())
        pzfree = tensor(pz[free])
        xyz = tensor(hstack([x, y, z]))
        xy = tensor(hstack([x, y]))
        pfixed = tensor(hstack([px, py, pz])[fixed])
        U_th = tensor(U.toarray())
        V_th = tensor(V.toarray())

        args_obj = (Edinv_p_th, EdinvEi_th, ind, dep, C_th, Ci_th, Cit_th, Cf_th, pzfree, xyz, xy, pfixed, k, objective)
        args_constr = (Edinv_p_th, EdinvEi_th, ind, dep, C_th, Ci_th, Cit_th, Cf_th, pzfree, xyz, xy, pfixed, k, free, fixed,
                       ub, lb, ub_ind, lb_ind, b, constraints, max_rol_rx, max_rol_ry, rol_x, rol_y, px, py, Asym, U_th, V_th)

        problem_obj = wrapper_ipopt()
        problem_obj.fobj = f_objective_pytorch
        problem_obj.fconstr = f_constraints_pytorch
        problem_obj.args_obj = args_obj
        problem_obj.args_constr = args_constr
        problem_obj.bounds = bounds
        problem_obj.x0 = x0
        problem_obj.args = args

        variables = tensor(x0, requires_grad=True)
        g0 = f_constraints_pytorch(variables, *args_constr)

    else:

        problem_obj = wrapper_ipopt_analytical()
        problem_obj.fobj = optimiser.fobj
        problem_obj.fconstr = optimiser.fconstr
        problem_obj.fjac = optimiser.fjac
        problem_obj.args = args
        problem_obj.fgrad = optimiser.fgrad
        problem_obj.bounds = bounds
        problem_obj.x0 = x0

        if printout:
            g0 = optimiser.fconstr(x0, *args)

    cu = [10e10]*len(g0)
    cl = [0.0]*len(g0)
    if any(el in ['symmetry', 'symmetry-horizontal', 'symmetry-vertical'] for el in constraints):
        nsym = Asym.shape[0]
        cu[-nsym:] = [0.0]*nsym
        cl[-nsym:] = [0.0]*nsym

    nlp = cyipopt.problem(
        n=len(x0),
        m=len(g0),
        problem_obj=problem_obj,
        lb=lower,
        ub=upper,
        cl=cl,
        cu=cu
    )

    # Set Options and Time
    nlp = _nlp_options(nlp, optimiser)
    start_time = time.time()

    # Solve
    xopt, info = nlp.solve(x0)
    fopt = info['obj_val']
    exitflag = info['status']
    if exitflag == 1 or exitflag == 0:  # IPOPT consider solved = 1. Solved in tolerances 0 -> TNO solved = 0
        exitflag = 0
    else:
        exitflag = 1
    if printout:
        print(info['status_msg'])

    elapsed_time = time.time() - start_time
    if printout:
        print('Solving Time: {0:.1f} sec'.format(elapsed_time))

    optimiser.exitflag = exitflag
    optimiser.time = elapsed_time
    optimiser.fopt = fopt
    optimiser.xopt = xopt
    optimiser.niter = None  # Did not find a way to display number of iterations
    optimiser.message = info['status_msg']

    post_process_general(analysis)

    return analysis


def _nlp_options(nlp, optimiser):

    # Link to instructions: https://coin-or.github.io/Ipopt/OPTIONS.html

    # nlp.addOption(b'hessian_approximation', b'limited-memory')
    # nlp.addOption('tol', 1e-4)              # Default 1e-8
    # nlp.addOption('max_iter', 500)        # Default 3000

    # nlp.addOption('dual_inf_tol', 100.0)  # Default 1.0
    # nlp.addOption('constr_viol_tol', 0.1) # Default 1e-4
    # nlp.addOption('compl_inf_tol', 0.1)   # Default 1e-4

    # nlp.addOption('acceptable_iter', 10)
    # nlp.addOption('acceptable_tol', 1e-3)
    # nlp.addOption('acceptable_constr_viol_tol', 1e-4)  # Default 1e-2
    # nlp.addOption('acceptable_dual_inf_tol', 10e10)  # Default 10e10
    # nlp.addOption('acceptable_compl_inf_tol', 1e-2)  # Default 1e-2
    # nlp.addOption('max_iter', 500)

    if not optimiser.settings['printout']:
        nlp.addOption('print_level', 0)
    if optimiser.settings.get('derivative_test', None):
        nlp.addOption('derivative_test', 'first-order')
        # nlp.addOption('derivative_test_perturbation') #, 10e-8
        # nlp.addOption('derivative_test_print_all', 'yes')
    if optimiser.settings.get('max_iter', None):
        nlp.addOption('max_iter', optimiser.settings['max_iter'])

    return nlp
