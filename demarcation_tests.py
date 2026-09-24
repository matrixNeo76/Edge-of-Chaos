"""
demarcation_tests.py
====================
Compatibility module. Up to v0.2.1 this file contained three functions labelled as the
"operational demarcation tests" (edge of chaos, spectral causal degeneracy, finite-size
scaling). In the papers those are three of the five necessary conditions, not the
demarcation, and the functions computed different quantities from the ones defined in
P1_Main.tex (see CHANGELOG, v0.3.0). They have been replaced by:

- demarcation.py           -- the three operational demarcation conditions
- necessary_conditions.py  -- edge of chaos, causal degeneracy, exponent stability

Running this file runs both demonstrations of the command-line interface.
"""

import warnings

from demarcation import (  # noqa: F401
    causal_non_separability,
    non_markovian_memory,
    state_dependent_dynamics,
    is_candidate,
)
from necessary_conditions import (  # noqa: F401
    edge_of_chaos,
    causal_degeneracy,
    degeneracy_radius,
    degeneracy_prediction,
    exponent_stability,
)

warnings.warn(
    "demarcation_tests.py is a compatibility module; import from demarcation.py and "
    "necessary_conditions.py instead.",
    DeprecationWarning,
    stacklevel=2,
)

if __name__ == "__main__":
    from paper0_cli import main

    main(["demarcation"])
    print()
    main(["conditions"])
