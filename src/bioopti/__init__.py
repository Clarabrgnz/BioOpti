"""
BioOpti: A toolkit for optimizing biochemical processes,
including enzyme reaction rates and culture media.
"""

from __future__ import annotations

from .reaction_simulator import (
    get_enzyme_kinetics,
    simulate_from_local_data,
    simulate_reaction_rate,
)

__version__ = "0.1.0"

from bioopti.media_optimizer import (
    get_bearer_token,
    search_ids,
    fetch_strain,
    extract_media,
    extract_temperature,
    display_media_table,
    run,
)