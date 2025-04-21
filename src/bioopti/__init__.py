"""
BioOpti: A toolkit for optimizing biochemical processes,
including enzyme reaction rates and culture media.
"""

from __future__ import annotations

from .enzyme_kinetics import get_enzyme_kinetics
from .simulation import simulate_from_local_data, simulate_reaction_rate

__version__ = "0.1.0"
