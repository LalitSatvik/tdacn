import pytest

from tdacn.adapters.base import AdapterBase


def test_adapter_base_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        AdapterBase()


def test_subclass_must_implement_load():
    class IncompleteAdapter(AdapterBase):
        pass

    with pytest.raises(TypeError):
        IncompleteAdapter()
