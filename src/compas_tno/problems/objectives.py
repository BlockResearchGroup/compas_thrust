from numpy import hstack
from numpy import array
from numpy import sum as npsum

from compas_tno.algorithms import xyz_from_q
from compas.numerical import normrow

from scipy.sparse import diags


def f_min_thrust(variables, M):
    """Objective function to minimise the horizontal thrust"""

    if isinstance(M, list):
        M = M[0]

    k = M.k
    nb = len(M.fixed)

    qid = variables[:k]
    M.q = M.B.dot(qid)

    if 'xyb' in M.variables:
        xyb = variables[k:k + 2*nb]
        M.X[M.fixed, :2] = xyb.reshape(-1, 2, order='F')
    if 'zb' in M.variables:
        zb = variables[-nb:]
        M.X[M.fixed, [2]] = zb.flatten()

    M.X[M.free] = xyz_from_q(M.q, M.P[M.free], M.X[M.fixed], M.Ci, M.Cit, M.Cb)
    xy = M.X[:, :2]
    P_xy_fixed = M.P[M.fixed][:, :2]

    CfQC = M.Cb.transpose().dot(diags(M.q.flatten())).dot(M.C)
    Rh = CfQC.dot(xy) - P_xy_fixed
    f = sum(normrow(Rh))

    return f


def f_max_thrust(variables, M):
    """Objective function to maximise the horizontal thrust"""

    return -1 * f_min_thrust(variables, M)


def f_bestfit(variables, M):
    """Objective function to minimise the vertical squared distance to a given target"""

    if isinstance(M, list):
        M = M[0]

    k = M.k
    nb = len(M.fixed)

    qid = variables[:k]
    M.q = M.B.dot(qid)

    if 'xyb' in M.variables:
        xyb = variables[k:k + 2*nb]
        M.X[M.fixed, :2] = xyb.reshape(-1, 2, order='F')
    if 'zb' in M.variables:
        zb = variables[-nb:]
        M.X[M.fixed, [2]] = zb.flatten()

    M.X[M.free] = xyz_from_q(M.q, M.P[M.free], M.X[M.fixed], M.Ci, M.Cit, M.Cb)

    f = sum((M.X[:, [2]] - M.s)**2)

    return f


def f_horprojection(variables, M):
    """Objective function to minimise the horizontal squared distance of the nodes on the form diagram to a given pattern"""

    if isinstance(M, list):
        M = M[0]

    k = M.k
    nb = len(M.fixed)

    qid = variables[:k]
    M.q = M.B.dot(qid)

    if 'xyb' in M.variables:
        xyb = variables[k:k + 2*nb]
        M.X[M.fixed, :2] = xyb.reshape(-1, 2, order='F')
    if 'zb' in M.variables:
        zb = variables[-nb:]
        M.X[M.fixed, [2]] = zb.flatten()

    M.X[M.free] = xyz_from_q(M.q, M.P[M.free], M.X[M.fixed], M.Ci, M.Cit, M.Cb)

    f = sum((M.X[:, [0]] - M.x0)**2) + sum((M.X[:, [1]] - M.y0)**2)

    return f


def f_loadpath_general(variables, M):
    """Objective function to minimise the loadpath"""

    if isinstance(M, list):
        M = M[0]

    k = M.k
    nb = len(M.fixed)

    qid = variables[:k]
    M.q = M.B.dot(qid)

    if 'xyb' in M.variables:
        xyb = variables[k:k + 2*nb]
        M.X[M.fixed, :2] = xyb.reshape(-1, 2, order='F')
    if 'zb' in M.variables:
        zb = variables[-nb:]
        M.X[M.fixed, [2]] = zb.flatten()

    M.X[M.free] = xyz_from_q(M.q, M.P[M.free], M.X[M.fixed], M.Ci, M.Cit, M.Cb)

    uvw = M.C.dot(M.X)

    l2 = npsum(uvw**2, axis=1).reshape(-1, 1)

    f = (abs(M.q.transpose()).dot(l2)).item()

    return f


def f_complementary_energy(variables, M):
    """Objective function to minimise the complementary energy to a given applied foundation displacement"""

    if isinstance(M, list):
        M = M[0]

    k = M.k
    nb = len(M.fixed)

    qid = variables[:k]
    M.q = M.B.dot(qid)

    if 'xyb' in M.variables:
        xyb = variables[k:k + 2*nb]
        M.X[M.fixed, :2] = xyb.reshape(-1, 2, order='F')
    if 'zb' in M.variables:
        zb = variables[-nb:]
        M.X[M.fixed, [2]] = zb.flatten()

    M.X[M.free] = xyz_from_q(M.q, M.P[M.free], M.X[M.fixed], M.Ci, M.Cit, M.Cb)

    CfQC = M.Cb.transpose().dot(diags(M.q.flatten())).dot(M.C)
    R = CfQC.dot(M.X) - M.P[M.fixed]
    f = -1 * npsum(R*M.dXb)

    return f


def f_complementary_energy_nonlinear(variables, M):
    """Objective function to minimise the nonlinear complementary energy to a given applied foundation displacement"""

    if isinstance(M, list):
        M = M[0]

    flin = f_complementary_energy(variables, M)

    if M.Ecomp_method == 'simplified':
        fquad = npsum(M.stiff * M.q.reshape(-1, 1) ** 2)  # assuming area and lengths constant - computed in beginning
    if M.Ecomp_method == 'complete':
        fquad = f_loadpath_general(variables, M) * M.stiff

    f = flin + fquad

    return f


def f_max_section(variables, M):
    """Objective function to minimise additional thickness required to find a feasible thrust network"""

    if isinstance(M, list):
        M = M[0]

    k = M.k
    nb = len(M.fixed)
    n = M.X.shape[0]

    check = k

    f = 0.0

    if 'xyb' in M.variables:
        check = check + 2*nb
    if 'zb' in M.variables:
        check = check + nb
    if 'tub' in M.variables:
        tub = variables[check: check + n]
        f += sum(tub**2)
        M.tub = tub
        check = check + n
    if 'tlb' in M.variables:
        tlb = variables[check: check + n]
        f += sum(tlb**2)
        M.tlb = tlb
        check = check + n
    if 'tlb' in M.variables:
        tlb = variables[check: check + n]
        f += sum(tlb**2)
        M.tlb = tlb
        check = check + n
    if 'tub_reac' in M.variables:
        tub_reac = variables[check: check + 2*nb]
        M.tub_reac = tub_reac
        f += sum(tub_reac[:nb]**2 + tub_reac[nb:]**2)  # this is not really 100% ok for 3D. x^2 +y^2 != (x + y)^2
        check = check + 2*nb

    return f


def f_constant(variables, M):
    """Constant or feasible objective function f=1"""

    f = 1.0

    return f


def f_reduce_thk(variables, M):
    """Objective function to reduce the thickness of the structure"""

    return variables[-1]


def f_tight_crosssection(variables, M):
    """Objective function to tight the cross section using normal vectors"""

    return -1 * variables[-1]


def f_min_thrust_pytorch(xopt, *args):
    q, ind, dep, E, Edinv, Ei, C, Ct, Ci, Cit, Cf, U, V, p, px, py, pz, z, free, fixed, lh, sym, k, lb, ub, lb_ind, ub_ind, s, Wfree, x, y, b, joints, i_uv, k_i = args[:35]
    qid = xopt[:k].reshape(-1, 1)
    q[ind] = array(qid).reshape(-1, 1)
    q[dep] = Edinv.dot(- p + Ei.dot(q[ind]))
    CfQC = Cf.transpose().dot(diags(q.flatten())).dot(C)
    xy = hstack([x, y])
    Rh = CfQC.dot(xy) - hstack([px, py])[fixed]
    f = sum(normrow(Rh))
    return f
