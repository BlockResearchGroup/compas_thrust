from compas_tno.diagrams import FormDiagram
from compas_tno.plotters import TNOPlotter
from compas.colors import Color

# ------------------------------------------------
# --------- CREATING ARCH FORM DIAGRAM -----------
# ------------------------------------------------

# data = {
#     'type': 'arch',
#     'H': 1.0,
#     'L': 2.0,
#     'discretisation': 11,
#     'x0': 0.0,
# }

# form = FormDiagram.from_library(data)
# plotter = TNOPlotter(form)
# plotter.draw_form(scale_width=False, color=Color.black())
# plotter.draw_supports()
# plotter.show()

# # or

# form = FormDiagram.create_arch()
# plotter = TNOPlotter(form)
# plotter.draw_form(scale_width=False, color=Color.black())
# plotter.draw_supports()
# plotter.show()


# ------------------------------------------------
# --------- CREATING ORTHO FORM DIAGRAM ----------
# ------------------------------------------------

data = {
    'type': 'ortho',
    'xy_span': [[0, 10], [0, 10]],
    'discretisation': [14, 14],
    'fix': 'all',
}

form = FormDiagram.from_library(data)
plotter = TNOPlotter(form)
plotter.draw_form(scale_width=False, color=Color.black())
plotter.draw_supports()
plotter.show()

# # or

# form = FormDiagram.create_ortho_form()
# plotter = TNOPlotter(form)
# plotter.draw_form(scale_width=False, color=Color.black())
# plotter.draw_supports()
# plotter.show()

# ------------------------------------------------
# --------- CREATING CROSS FORM DIAGRAM ----------
# ------------------------------------------------

data = {
    'type': 'cross_fd',
    'xy_span': [[0, 10], [0, 10]],
    'discretisation': 14,
    'fix': 'corners',
}

form = FormDiagram.from_library(data)
plotter = TNOPlotter(form)
plotter.draw_form(scale_width=False, color=Color.black())
plotter.draw_supports()
plotter.show()

# # or

# form = FormDiagram.create_cross_form()
# plotter = TNOPlotter(form)
# plotter.draw_form(scale_width=False, color=Color.black())
# plotter.draw_supports()
# plotter.show()

# ------------------------------------------------
# --------- CREATING FAN FORM DIAGRAM ------------
# ------------------------------------------------

data = {
    'type': 'fan_fd',
    'xy_span': [[0, 10], [0, 10]],
    'discretisation': [14, 14],
    'fix': 'corners',
}

form = FormDiagram.from_library(data)
plotter = TNOPlotter(form)
plotter.draw_form(scale_width=False, color=Color.black())
plotter.draw_supports()
plotter.show()

# # or

# form = FormDiagram.create_fan_form()
# plotter = TNOPlotter(form)
# plotter.draw_form(scale_width=False, color=Color.black())
# plotter.draw_supports()
# plotter.show()

# -----------------------------------------------------------
# --------- CREATING CROSS DIAGONAL FORM DIAGRAM ------------
# -----------------------------------------------------------

# data = {
#     'type': 'cross_diagonal',
#     'xy_span': [[0, 10], [0, 10]],
#     'discretisation': 4,
#     'fix': 'corners',
# }

# form = FormDiagram.from_library(data)
# plotter = TNOPlotter(form)
# plotter.draw_form(scale_width=False, color=Color.black())
# plotter.draw_supports()
# plotter.show()

# # or

# form = FormDiagram.create_cross_diagonal()
# plotter = TNOPlotter(form)
# plotter.draw_form(scale_width=False, color=Color.black())
# plotter.draw_supports()
# plotter.show()

# ------------------------------------------------
# --------- CREATING RADIAL FORM DIAGRAM ---------
# ------------------------------------------------

data = {
    'type': 'radial_fd',
    'center': [5.0, 5.0],
    'radius': 5.0,
    'discretisation': [12, 16],
    'r_oculus': 0.75,
}

form = FormDiagram.from_library(data)
plotter = TNOPlotter(form)
plotter.draw_form(scale_width=False, color=Color.black())
plotter.draw_supports()
plotter.show()

# # or

# form = FormDiagram.create_circular_radial_form()
# plotter = TNOPlotter(form)
# plotter.draw_form(scale_width=False, color=Color.black())
# plotter.draw_supports()
# plotter.show()

print(xxxx)

# ------------------------------------------------
# --- CREATING RADIAL FORM DIAGRAM W DIAGONALS ---
# ------------------------------------------------

data = {
    'type': 'radial_fd',
    'center': [5.0, 5.0],
    'radius': 5.0,
    'discretisation': [8, 12],
    'r_oculus': 0.0,
    'diagonal': True,
    'partial_diagonal': 'right',
}

form = FormDiagram.from_library(data)
plotter = TNOPlotter(form)
plotter.draw_form(scale_width=False, color=Color.black())
plotter.draw_supports()
plotter.show()

# or

form = FormDiagram.create_circular_radial_form(discretisation=data['discretisation'], r_oculus=data['r_oculus'], diagonal=data['diagonal'], partial_diagonal=data['partial_diagonal'])
plotter = TNOPlotter(form)
plotter.draw_form(scale_width=False, color=Color.black())
plotter.draw_supports()
plotter.show()

# ------------------------------------------------
# --------- CREATING RADIAL SPACED DIAGRAM ---------
# ------------------------------------------------

data = {
    'type': 'radial_spaced_fd',
    'D': 3.0,
    'center': [5.0, 5.0],
    'radius': 5.0,
    'discretisation': [8, 20],
    'r_oculus': 0.0,
    'diagonal': False,
    'partial_diagonal': False,
}

form = FormDiagram.from_library(data)
plotter = TNOPlotter(form)
plotter.draw_form(scale_width=False, color=Color.black())
plotter.draw_supports()
plotter.show()

# or

form = FormDiagram.create_circular_radial_form()
plotter = TNOPlotter(form)
plotter.draw_form(scale_width=False, color=Color.black())
plotter.draw_supports()
plotter.show()

# ------------------------------------------------
# --------- CREATING SPIRAL FORM DIAGRAM ---------
# ------------------------------------------------

data = {
    'type': 'spiral_fd',
    'D': 3.0,
    'center': [5.0, 5.0],
    'radius': 5.0,
    'discretisation': [8, 20],
    'r_oculus': 0.0,
}

form = FormDiagram.from_library(data)
plotter = TNOPlotter(form)
plotter.draw_form(scale_width=False, color=Color.black())
plotter.draw_supports()
plotter.show()

# or

form = FormDiagram.create_circular_spiral_form()
plotter = TNOPlotter(form)
plotter.draw_form(scale_width=False, color=Color.black())
plotter.draw_supports()
plotter.show()

# -----------------------------------------------------------
# --------- CREATING CROSS W DIAGONAL FORM DIAGRAM ------------
# -----------------------------------------------------------

data = {
    'type': 'cross_with_diagonal',
    'xy_span': [[0, 10], [0, 10]],
    'discretisation': 10,
    'fix': 'all',
}

form = FormDiagram.from_library(data)
plotter = TNOPlotter(form)
plotter.draw_form(scale_width=False, color=Color.black())
plotter.draw_supports()
plotter.show()

# or

form = FormDiagram.create_cross_with_diagonal()
plotter = TNOPlotter(form)
plotter.draw_form(scale_width=False, color=Color.black())
plotter.draw_supports()
plotter.show()
