"""Base interface every dataset adapter must implement.

An adapter is the only part of the pipeline allowed to know about a
specific dataset's raw format. Porting the pipeline to a new dataset (a
different set of quarters, a different jurisdiction's XBRL, or an
unrelated entity x concept x time panel) means writing a new subclass of
AdapterBase — no changes to graph/embed/metrics/segment code, which only
ever operates on the CanonicalBundle this produces.
"""

from abc import ABC, abstractmethod

from tdacn.schema import CanonicalBundle


class AdapterBase(ABC):
    @abstractmethod
    def load(self, source) -> CanonicalBundle:
        """Read raw data from `source` and return a validated CanonicalBundle."""
        raise NotImplementedError
