from typing import List, Dict, Union
import os
import polars as pl
from rust_core import process_flows

class FIGAROParser:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.imports_file = os.path.join(data_dir, 'figaro', 'estat_naio_10_fgti.tsv')
        self.exports_file = os.path.join(data_dir, 'figaro', 'estat_naio_10_fgte.tsv')
        
    def get_available_years(self) -> List[int]:
        # Use polars for efficient reading and processing
        df = pl.read_csv(self.imports_file, separator='\t')
        # Get year columns (all columns after the first)
        year_columns = df.columns[1:]
        return sorted([int(year.strip()) for year in year_columns])
    
    def get_flow_data(self, year: int) -> List[Dict[str, Union[str, float]]]:
        # Use the Rust implementation for high-performance data processing
        flows_data = process_flows(self.imports_file, self.exports_file, year)
        
        # Convert to the format expected by the visualization
        return [
            {
                'source': source,
                'target': target,
                'value': value
            }
            for source, target, value in flows_data
        ]
