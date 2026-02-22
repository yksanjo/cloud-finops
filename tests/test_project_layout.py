from pathlib import Path


def test_cloud_finops_structure_exists():
    assert Path('cloud_finops/optimizer.py').exists()
    assert Path('cloud_finops/providers/aws_provider.py').exists()
    assert Path('setup.py').exists()
