# -*- coding: utf-8 -*-

"""Conversion utilities for BEL."""

import logging
from pathlib import Path
from typing import TextIO, Tuple, Union

import pandas as pd
from tqdm import tqdm

from pybel import BELGraph
from pybel.constants import ACTIVITY, HAS_COMPONENT, MODIFIER, OBJECT, REGULATES, RELATION, SUBJECT
from pybel.dsl import BaseEntity

__all__ = [
    'to_keen_file',
    'to_keen_df',
    'get_triple',
]

logger = logging.getLogger(__name__)


def to_keen_file(graph: BELGraph, file: Union[str, Path, TextIO]) -> None:
    """Write the relationships in the BEL graph to a KEEN TSV file."""
    df = to_keen_df(graph)
    df.to_csv(file, sep='\t', index=None, header=None)


def to_keen_df(graph: BELGraph) -> pd.DataFrame:
    """Get a pandas DataFrame representing the triples."""
    triples = (
        get_triple(graph, u, v, key)
        for u, v, key in tqdm(graph.edges(keys=True), total=graph.number_of_edges(), desc='keen')
    )

    # clean Nones
    triples = [triple for triple in triples if triple is not None]

    return pd.DataFrame(triples, columns=['subject', 'predicate', 'object'])


def get_triple(graph: BELGraph, u: BaseEntity, v: BaseEntity, key: str) -> Tuple[str, str, str]:
    """Get the triples' strings that should be written to the file."""
    data = graph[u][v][key]
    relation = data[RELATION]
    subject_modifier = data.get(SUBJECT)
    object_modifier = data.get(OBJECT)

    if relation == HAS_COMPONENT:
        return (
            f'{v.namespace}:{v.identifier or v.name}',
            'part of',
            str(u),
        )

    elif relation == REGULATES and object_modifier and object_modifier.get(MODIFIER) == ACTIVITY:
        return (
            f'{u.namespace}:{v.identifier or u.name}',
            'activity directly negatively regulates activity of',
            f'{v.namespace}:{v.identifier or v.name}',
        )

    else:
        logger.info(f'unhandled: {graph.edge_to_bel(u, v, data)}')