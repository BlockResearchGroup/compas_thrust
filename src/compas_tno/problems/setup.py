from compas_tno.problems import initialise_problem_general

from compas_tno.problems import adapt_problem_to_fixed_diagram
from compas_tno.problems import adapt_problem_to_sym_diagram
from compas_tno.problems import adapt_problem_to_sym_and_fixed_diagram

from compas_tno.problems import objective_selector

from compas_tno.problems import callback_save_json
from compas_tno.problems import callback_create_json

from compas_tno.problems import initialize_loadpath
from compas_tno.problems import initialize_tna

from compas_tno.algorithms import apply_sag
from compas_tno.algorithms import equilibrium_fdm

from compas_tno.problems import sensitivities_wrapper

from compas_tno.problems import constr_wrapper

from compas_tno.plotters import TNOPlotter

from compas_tno.utilities import apply_bounds_on_q
from compas_tno.utilities import compute_form_initial_lengths
from compas_tno.utilities import compute_edge_stiffness
from compas_tno.utilities import compute_average_edge_stiffness
from compas_tno.utilities import set_b_constraint

from compas_tno.viewers import Viewer

from numpy import append
from numpy import array
from numpy import zeros
from numpy import vstack


def set_up_general_optimisation(analysis):
    """ Set up a nonlinear optimisation problem.

    Parameters
    ----------
    obj : analysis
        Analysis object with information about optimiser, form and shape.

    Returns
    -------
    obj : analysis
        Analysis object set up for optimise.

    """

    form = analysis.form
    optimiser = analysis.optimiser
    shape = analysis.shape

    printout = optimiser.settings.get('printout', True)
    plot = optimiser.settings.get('plot', False)
    axis_symmetry = optimiser.settings.get('axis_symmetry', None)
    sym_loads = optimiser.settings.get('sym_loads', False)
    fjac = optimiser.settings.get('jacobian', False)
    starting_point = optimiser.settings.get('starting_point', 'current')
    find_inds = optimiser.settings.get('find_inds', False)
    qmin = optimiser.settings.get('qmin', -1e+4)
    qmax = optimiser.settings.get('qmax', +1e+8)
    features = optimiser.settings.get('features', [])
    save_iterations = optimiser.settings.get('save_iterations', False)
    solver_convex = optimiser.settings.get('solver-convex', 'matlab')
    # thickness_type = optimiser.settings.get('thickness_type', 'constant')
    autodiff = optimiser.settings.get('autodiff', False)

    pattern_center = form.parameters.get('center', None)

    if shape:
        thk = shape.datashape['thk']
    else:
        thk = 0.20

    objective = optimiser.settings['objective']
    variables = optimiser.settings['variables']
    constraints = optimiser.settings['constraints']

    i_k = form.index_key()

    qmin_applied = form.edges_attribute('qmin')
    for qmin_applied_i in qmin_applied:
        if qmin_applied_i is None:
            print('Appied qmin / qmax:', qmin, qmax)
            apply_bounds_on_q(form, qmin=qmin, qmax=qmax)
            break

    M = initialise_problem_general(form)
    M.variables = variables
    M.constraints = constraints
    M.features = features
    M.shape = shape
    M.thk = thk

    if 'update-loads' in features:
        F, V0, V1, V2 = form.tributary_matrices(sparse=False)
    else:
        F, V0, V1, V2 = 4*[None]

    M.F = F
    M.V0 = V0
    M.V1 = V1
    M.V2 = V2
    M.ro = shape.ro

    if starting_point == 'current':
        pass
    elif starting_point == 'sag':
        apply_sag(form)
    elif starting_point == 'loadpath':
        initialize_loadpath(form, problem=M, find_inds=find_inds, solver_convex=solver_convex)
    elif starting_point == 'relax':
        equilibrium_fdm(form)
    elif starting_point == 'tna' or starting_point == 'TNA':
        initialize_tna(form)
    else:
        print('Warning: define starting point')

    M.q = array([form.edge_attribute((u, v), 'q') for u, v in form.edges_where({'_is_edge': True})]).reshape(-1, 1)

    if 'fixed' in features and 'sym' in features:
        # print('\n-------- Initialisation with fixed and sym form --------')
        adapt_problem_to_sym_and_fixed_diagram(M, form, list_axis_symmetry=axis_symmetry, center=pattern_center, correct_loads=sym_loads, printout=printout)
    elif 'sym' in features:
        # print('\n-------- Initialisation with sym form --------')
        adapt_problem_to_sym_diagram(M, form, list_axis_symmetry=axis_symmetry, center=pattern_center, correct_loads=sym_loads, printout=printout)
    elif 'fixed' in features:
        # print('\n-------- Initialisation with fixed form --------')
        adapt_problem_to_fixed_diagram(M, form, printout=printout)
    else:
        # print('\n-------- Initialisation with no-fixed and no-sym form --------')
        pass

    # Specific parameters that depend on the objectives

    # If objective is the complementary energy

    if 'Ecomp' in objective.split('-'):
        M.dXb = optimiser.settings['support_displacement']

    if objective == 'Ecomp-nonlinear':
        Ecomp_method = optimiser.settings.get('Ecomp_method', 'simplified')
        M.Ecomp_method = Ecomp_method

        if Ecomp_method == 'simplified':
            stiff = zeros((M.m, 1))
            lengths = compute_form_initial_lengths(form)
            k = compute_edge_stiffness(form, lengths=lengths)
            for index, edge in enumerate(form.edges()):
                stiff[index] = 1 / 2 * 1 / k[index] * lengths[index] ** 2
            M.stiff = stiff
        elif Ecomp_method == 'complete':
            #form. add here a control over the stiffness
            k = compute_average_edge_stiffness(form, E=E, Ah=Ah)
            print('Average Stiffness (1/k) applied to sections:', 1/k)
            M.stiff = 1/2 * 1/k

    # If objective is the max_load (new)

    # if objective == 'max_load':
    #     max_load_vector = optimiser.settings.get('max_load_direction', None)
    #     M.pzv = max_load_vector

    # Set specific constraints

    if 'reac_bounds' in constraints:
        M.b = set_b_constraint(form, printout)
    else:
        M.b = None

    # Select Objetive, Gradient, Costraints and Jacobian.

    fobj, fgrad = objective_selector(objective)

    fconstr = constr_wrapper
    if fjac:
        fjac = sensitivities_wrapper

    # Alternative for autodiff

    if autodiff:
        from compas_tno.autodiff.jax_objectives import objective_selector_jax
        from compas_tno.autodiff.jax_constraints import f_jacobian_jax

        fobj, fgrad = objective_selector_jax(objective)
        fconstr, fjac = f_jacobian_jax()

    # Select starting point (x0) and max/min for variables

    x0 = M.q[M.ind]
    bounds = [[qmin.item(), qmax.item()] for i, (qmin, qmax) in enumerate(zip(M.qmin, M.qmax)) if i in M.ind]

    # bounds = [[qmin, qmax]] * M.k

    if 'xyb' in variables:
        xyb0 = M.X[M.fixed, :2].flatten('F').reshape((-1, 1))
        x0 = append(x0, xyb0).reshape(-1, 1)
        bounds_x = []
        bounds_y = []
        for i in M.fixed:
            bounds_x.append([form.vertex_attribute(i_k[i], 'xmin'), form.vertex_attribute(i_k[i], 'xmax')])
            bounds_y.append([form.vertex_attribute(i_k[i], 'ymin'), form.vertex_attribute(i_k[i], 'ymax')])
        bounds = bounds + bounds_x + bounds_y

    if 'zb' in variables:
        zb0 = M.X[M.fixed, 2].flatten('F').reshape((-1, 1))
        x0 = append(x0, zb0).reshape(-1, 1)
        bounds_z = []
        for i in M.fixed:
            bounds_z.append([form.vertex_attribute(i_k[i], 'lb'), form.vertex_attribute(i_k[i], 'ub')])
        bounds = bounds + bounds_z

    if 't' in variables:
        min_thk = optimiser.settings.get('min_thk', 0.001)
        max_thk = optimiser.settings.get('max_thk', thk)
        print('max thickness', max_thk)
        x0 = append(x0, thk).reshape(-1, 1)
        bounds = bounds + [[min_thk, max_thk]]

    if 'lambd' in variables:
        lambd0 = optimiser.settings.get('lambd', 1.0)
        direction = optimiser.settings.get('lambd-direction', 'x')
        M.px0 = array(form.vertices_attribute('px')).reshape(-1, 1)
        M.py0 = array(form.vertices_attribute('py')).reshape(-1, 1)
        form.apply_horizontal_multiplier(lambd=1.0, direction=direction)
        max_lambd = optimiser.settings.get('max_lambd', lambd0 * 10)
        min_lambd = 0.0
        x0 = append(x0, lambd0).reshape(-1, 1)
        bounds = bounds + [[min_lambd, max_lambd]]

    # if 's' in variables:
    #     x0 = append(x0, 0.0).reshape(-1, 1)
    #     bounds = bounds + [[-1.0, 0.5]]

    if 'n' in variables:
        thk0_approx = thk  # shape.datashape['thk']
        print('Thickness approximate:', thk0_approx)
        x0 = append(x0, 0.0).reshape(-1, 1)
        min_limit = 0.0  # /2  # 0.0
        bounds = bounds + [[min_limit, thk0_approx/2]]
        # bounds = bounds + [[min_limit, thk0_approx/2]]

    if 'tub' in variables:
        M.tub = zeros((M.n, 1))
        tubmax = form.vertices_attribute('tubmax')
        M.tubmax = array(tubmax).reshape(M.n, 1)
        M.tubmin = zeros((M.n, 1))
        x0 = append(x0, M.tub)
        bounds = bounds + list(zip(M.tubmin, M.tubmax))

    if 'tlb' in variables:
        M.tlb = zeros((M.n, 1))
        tlbmax = form.vertices_attribute('tlbmax')
        M.tlbmax = array(tlbmax).reshape(M.n, 1)
        M.tlbmin = zeros((M.n, 1))
        x0 = append(x0, M.tlb)
        bounds = bounds + list(zip(M.tlbmin, M.tlbmax))

    if 'tub_reac' in variables:
        tub_reac = []
        for key in form.vertices_where({'is_fixed': True}):
            tub_reac.append(form.vertex_attribute(key, 'tub_reacmax'))
        tub_reac = array(tub_reac)
        tub_reac = vstack([tub_reac[:, 0].reshape(-1, 1), tub_reac[:, 1].reshape(-1, 1)])
        M.tub_reac = abs(tub_reac)
        M.tub_reac_min = zeros((2*M.nb, 1))
        x0 = append(x0, M.tub_reac_min)
        bounds = bounds + list(zip(M.tub_reac_min, M.tub_reac))

    if 'lambdv' in variables:
        max_load_vector = optimiser.settings.get('max_load_direction', None)
        max_load_mult = optimiser.settings.get('max_load_mult', 100.0)
        min_load_mult = 0.0
        lambd0 = 1.0
        print('Maximum load multiplier:', max_load_mult)
        M.pzv = max_load_vector
        M.pz0 = array(form.vertices_attribute('pz')).reshape(-1, 1)
        x0 = append(x0, lambd0).reshape(-1, 1)
        bounds = bounds + [[min_load_mult, max_load_mult]]

    if save_iterations:
        callback_create_json()
        optimiser.settings['callback'] = callback_save_json
        callback_save_json(x0)  # save staring point to file

    if plot:
        plotter = TNOPlotter(form)
        plotter.draw_form_independents()
        plotter.show()
        if 'sym' in features:
            plotter = TNOPlotter(form)
            plotter.draw_form_sym()
            plotter.show()

    f0 = fobj(x0, M)
    g0 = fconstr(x0, M)

    if fgrad:
        grad = fgrad(x0, M)
    if fjac:
        jac = fjac(x0, M)

    if plot:
        view = Viewer(form)
        view.draw_thrust()
        view.draw_force()
        view.show()

    if printout:
        print('-'*20)
        print('NPL (Non Linear Problem) Data:')
        print('Number of force variables:', len(M.ind))
        print('Number of variables:', len(x0))
        print('Number of constraints:', len(g0))
        if 'funicular' in M.constraints:
            print('# constraints funicular:', 2*len(M.q))
        if 'envelopexy' in M.constraints:
            print('# constraints envelope xy:', 4*len(M.X))
        if 'envelope' in M.constraints:
            print('# constraints envelope z:', 2*len(M.X))
        if 'reac_bounds' in M.constraints:
            print('# constraints reac_bounds:', 2*len(M.fixed))
        if fgrad:
            print('Shape of gradient:', grad.shape)
        if fjac:
            print('Shape of jacobian:', jac.shape)
        print('Init. Objective Value: {0}'.format(f0))
        # if objective == 'Ecomp-nonlinear':
        #     print('Init. Linear Obj Func: {0}'.format(f_complementary_energy(x0, M)))
        print('Init. Constraints Extremes: {0:.3f} to {1:.3f}'.format(max(g0), min(g0)))
        violated = []
        for i in range(len(g0)):
            if g0[i] < 0:
                violated.append(i)
        if violated:
            print('Constraints Violated #:', violated)

    optimiser.fobj = fobj
    optimiser.fconstr = fconstr
    optimiser.fgrad = fgrad
    optimiser.fjac = fjac
    optimiser.M = M
    optimiser.x0 = x0
    optimiser.bounds = bounds
    optimiser.f0 = f0
    optimiser.g0 = g0

    analysis.form = form
    analysis.optimiser = optimiser

    return analysis


def set_up_convex_optimisation(analysis):
    """ Set up a convex optimisation problem.

    Parameters
    ----------
    obj : analysis
        Analysis object with information about optimiser, form and shape.

    Returns
    -------
    obj : analysis
        Analysis object set up for optimise.

    """

    form = analysis.form
    optimiser = analysis.optimiser
    qmax = optimiser.settings['qmax']
    qmin = optimiser.settings['qmin']

    objective = optimiser.settings['objective']
    variables = optimiser.settings['variables']
    constraints = optimiser.settings['constraints']

    # Select Objective

    if objective not in ['loadpath', 'feasibility']:
        print('Warning: Non-convex problem for the objective: ', objective, '. Try changing the objective to \'loadpath\' or \'fesibility\'.')

    if variables == ['q']:
        pass
    else:
        print('Warning:  Non-convex problem for the variables: ', variables, '. Considering only \'q\' instead.')

    if constraints == ['funicular']:
        pass
    else:
        print('Warning:  Non-convex problem for the constraints: ', constraints, '. Considering only \'funicular\' instead.')

    apply_bounds_on_q(form, qmin=qmin, qmax=qmax)

    M = initialise_problem_general(form)
    M.variables = variables
    M.constraints = constraints

    optimiser.M = M

    analysis.form = form
    analysis.optimiser = optimiser

    return analysis
