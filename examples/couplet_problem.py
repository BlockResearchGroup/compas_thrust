
from compas_tna.diagrams import FormDiagram
from compas_thrust.algorithms import optimise_general

from compas_thrust.utilities.constraints import circular_heights
from compas_thrust.diagrams.form import overview_forces
from compas_thrust.diagrams.form import create_arch

from compas_thrust.plotters.plotters import plot_form_xz
from numpy import array

# ==============================================================================
# Main
# ==============================================================================

if __name__ == "__main__":

    file_save = '/Users/mricardo/compas_dev/me/minmax/2D_Arch/couplet_problem.json'
    
    form = create_arch(total_nodes=14)
    overview_forces(form)
    print_opt = True
    decrease = 0.01
    thk = 0.18
    exitflag = 0
    while exitflag == 0:
        form = circular_heights(form, thk = thk)

        # Initial parameters

        translation = form.attributes['tmax']
        bounds_width = 5.0
        use_bounds = False
        qmax = 20000
        indset = None

        # Optimisation

        exitflag = 1
        count = 0

        while count < 100 and exitflag is not 0:
            # form = _form(form, keep_q=True)
            fopt, qopt, zbopt, exitflag = optimise_general(form,  qmax=qmax, solver='slsqp',
                                                printout=print_opt,
                                                find_inds=True,
                                                tol=0.01,
                                                translation = translation,
                                                tension=False,
                                                use_bounds = use_bounds,
                                                bounds_width = bounds_width,
                                                objective='min',
                                                indset=indset,
                                                bmax = True,
                                                summary=print_opt)

            # Check compression and Save

            q = [attr['q'] for u, v, attr in form.edges(True)]
            qmin  = min(array(q))
            count += 1
            if qmin > -0.1 and exitflag == 0:
                print('Optimisation completed - Trial:',count, 't', thk)
                plot_form_xz(form, radius=0.01, simple=True, fix_width = True, max_width=1.5, heights=True, show_q=False, thk = thk, plot_reactions=True).show()
                form.to_json(file_save)
        
        thk = thk - decrease
