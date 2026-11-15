import pytest
import torch
from spiraldb import SpiralDB, create_spiraldb

class TestSpiralDB:
    def test_init(self):
        m = SpiralDB(dim=256, hidden_dim=512)
        assert m.dim == 256
    
    def test_forward(self):
        m = SpiralDB(dim=256)
        x = torch.randn(32, 256)
        assert m(x).shape == (32, 256)
    
    def test_factory(self):
        m = create_spiraldb()
        assert isinstance(m, SpiralDB)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
