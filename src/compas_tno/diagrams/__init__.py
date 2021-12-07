"""
********************************************************************************
compas_tno.diagrams
********************************************************************************

.. currentmodule:: compas_tno.diagrams


Classes
=======

.. autosummary::
    :toctree: generated/

    FormDiagram
    ForceDiagram
    FormGraph


Rectangular diagrams
====================

.. autosummary::
    :toctree: generated/

    create_cross_form
    create_cross_diagonal
    create_cross_with_diagonal
    create_fan_form
    create_ortho_form


Circular diagrams
=================

.. autosummary::
    :toctree: generated/

    create_circular_radial_form
    create_circular_radial_spaced_form
    create_circular_spiral_form


Linear diagrams
===============

.. autosummary::
    :toctree: generated/

    create_arch_form_diagram
    create_linear_form_diagram

"""
from __future__ import absolute_import

from .force import ForceDiagram
from .form import FormDiagram
from .graph import FormGraph

from .diagram_arch import (
    create_arch_form_diagram,
    create_linear_form_diagram
)
from .diagram_circular import (
    create_circular_radial_form,
    create_circular_radial_spaced_form,
    create_circular_spiral_form,
)
from .diagram_rectangular import (
    create_cross_form,
    create_cross_diagonal,
    create_cross_with_diagonal,
    create_fan_form,
    create_ortho_form
)

__all__ = [
    'ForceDiagram',
    'FormDiagram',
    'FormGraph',

    'create_arch_form_diagram',
    'create_linear_form_diagram',

    'create_circular_radial_form',
    'create_circular_radial_spaced_form',
    'create_circular_spiral_form',

    'create_cross_form',
    'create_cross_diagonal',
    'create_cross_with_diagonal',
    'create_fan_form',
    'create_ortho_form'

]
