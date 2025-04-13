import pytest
import os
import tempfile
from src.parser import FIGAROParser

@pytest.fixture
def sample_data_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create figaro subdirectory
        figaro_dir = os.path.join(tmpdir, 'figaro')
        os.makedirs(figaro_dir)
        
        # Create sample import file with some NaN and zero values
        import_content = (
            "TIME,nace_r2,c_exp,unit,geo\t2019\t2020\n"
            "A,B01,EXP_GO,MIO_EUR,AT\t100.5\t200.5\n"
            "A,B02,EXP_GO,MIO_EUR,BE\t150.3\t250.3\n"
            "A,B03,EXP_GO,MIO_EUR,DE\t0.0\t0.0\n"
            "A,B04,EXP_GO,MIO_EUR,FR\t\t\n"  # NaN values
        )
        with open(os.path.join(figaro_dir, 'estat_naio_10_fgti.tsv'), 'w') as f:
            f.write(import_content)
        
        # Create sample export file with some NaN and zero values
        export_content = (
            "TIME,nace_r2,c_exp,unit,geo\t2019\t2020\n"
            "A,B01,IMP_GO,MIO_EUR,AT\t300.5\t400.5\n"
            "A,B02,IMP_GO,MIO_EUR,BE\t350.3\t450.3\n"
            "A,B03,IMP_GO,MIO_EUR,DE\t0.0\t0.0\n"
            "A,B04,IMP_GO,MIO_EUR,FR\t\t\n"  # NaN values
        )
        with open(os.path.join(figaro_dir, 'estat_naio_10_fgte.tsv'), 'w') as f:
            f.write(export_content)
            
        yield tmpdir

def test_parser_initialization(sample_data_dir):
    parser = FIGAROParser(sample_data_dir)
    assert parser.data_dir == sample_data_dir
    assert os.path.exists(parser.imports_file)
    assert os.path.exists(parser.exports_file)

def test_get_available_years(sample_data_dir):
    parser = FIGAROParser(sample_data_dir)
    years = parser.get_available_years()
    assert years == [2019, 2020]

def test_missing_files():
    with pytest.raises(FileNotFoundError) as exc_info:
        FIGAROParser('nonexistent_dir')
    assert "Required FIGARO file not found" in str(exc_info.value)

@pytest.mark.integration
def test_get_flow_data_with_filters(sample_data_dir):
    parser = FIGAROParser(sample_data_dir)
    
    # Test with default parameters (drop_nan=True, min_value=0.0)
    flows = parser.get_flow_data(2019)
    assert len(flows) > 0
    # Zero values should be included by default, so we should find some
    assert any(f['value'] == 0.0 for f in flows)
    
    # Test with min_value filter
    flows_min_200 = parser.get_flow_data(2019, min_value=200.0)
    assert all(f['value'] >= 200.0 for f in flows_min_200)
    assert len(flows_min_200) < len(flows)  # Should have fewer entries
    
    # Make sure we can exclude zeros
    flows_no_zeros = parser.get_flow_data(2019, min_value=0.1)
    assert all(f['value'] > 0.0 for f in flows_no_zeros)
    assert len(flows_no_zeros) < len(flows)  # Should have fewer entries
    
    # Test with drop_nan=False (should include NaN entries)
    flows_with_nan = parser.get_flow_data(2019, drop_nan=False)
    assert len(flows_with_nan) >= len(flows)  # Should have at least as many entries