from typing import List, Dict, Union, Optional
import os
import pandas as pd

class FIGAROParser:
    """Parser for FIGARO format TSV files."""
    
    def __init__(self, data_dir: str):
        """Initialize the FIGARO parser with data directory path."""
        self.data_dir = data_dir
        self.imports_file = os.path.join(data_dir, 'figaro', 'estat_naio_10_fgti.tsv')
        self.exports_file = os.path.join(data_dir, 'figaro', 'estat_naio_10_fgte.tsv')
        
        # Check if required files exist
        for file_path in [self.imports_file, self.exports_file]:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Required FIGARO file not found: {file_path}")

    def _read_and_clean_df(self, file_path: str, nrows: Optional[int] = None) -> pd.DataFrame:
        """Read and clean a dataframe from a TSV file."""
        df = pd.read_csv(file_path, sep='\t', engine='python', nrows=nrows)
        
        # Clean whitespace from column names
        df.columns = df.columns.str.strip()
        
        # Clean whitespace from string columns and convert numeric columns
        for col in df.columns:
            if df[col].dtype == 'object':  # Only strip strings
                df[col] = df[col].str.strip()
            if col.isdigit():  # Convert year columns to numeric
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
        return df

    def get_value_range(self, year: int) -> Dict[str, float]:
        """Get the minimum and maximum values for a given year."""
        imports_df = self._read_and_clean_df(self.imports_file)
        exports_df = self._read_and_clean_df(self.exports_file)
        
        year_str = str(year)
        
        min_value = min(
            imports_df[year_str].min(),
            exports_df[year_str].min()
        )
        max_value = max(
            imports_df[year_str].max(),
            exports_df[year_str].max()
        )
        
        return {
            'min': float(min_value),
            'max': float(max_value)
        }

    def get_available_regions(self) -> List[str]:
        """Get list of available geographic regions."""
        imports_df = self._read_and_clean_df(self.imports_file)
        exports_df = self._read_and_clean_df(self.exports_file)
        
        # Get unique geo values from first column
        regions = set()
        for df in [imports_df, exports_df]:
            first_col = df.iloc[:, 0]
            regions.update(first_col.str.split(',').str[-1].unique())
        
        return sorted(list(regions))

    def truncate_nace_code(self, code: str, level: int) -> str:
        """Truncate NACE code to specified level."""
        if not code or level < 1:
            return code
        parts = code.split('.')
        return '.'.join(parts[:level])

    def get_available_years(self) -> List[int]:
        """Get list of available years in the dataset."""
        df = self._read_and_clean_df(self.imports_file)
        # Get all numeric columns (year columns)
        year_columns = [col for col in df.columns if col.isdigit()]
        return sorted([int(year) for year in year_columns])

    def _process_flow_file(
        self, 
        file_path: str, 
        year: int, 
        flow_type: str,
        min_value: float = 0.0,
        drop_nan: bool = True,
        nace_level: int = None,
        regions: List[str] = None
    ) -> List[Dict[str, Union[str, float]]]:
        """Process a single flow file."""
        df = self._read_and_clean_df(file_path)
        
        # Get first column (which has the format freq,nace_r2,c_exp,unit,geo)
        first_col = df.iloc[:, 0]
        first_col_parts = first_col.str.split(',')
        
        year_str = str(year)
        if year_str not in df.columns:
            raise ValueError(f"Year {year} not found in data. Available years: {', '.join(str(y) for y in self.get_available_years())}")
        
        # Create initial dataframe with variables and values
        result_df = pd.DataFrame({
            'nace_r2': first_col_parts.str[1],  # Second element is nace_r2
            'value': df[year_str],
            'geo': first_col_parts.str[4]  # Last element is geo
        })
        
        # Apply filters
        if drop_nan:
            result_df = result_df.dropna()
        
        if min_value > 0:
            result_df = result_df[result_df['value'] >= min_value]
            
        if regions:
            result_df = result_df[result_df['geo'].isin(regions)]
        
        # Apply NACE level aggregation if specified
        if nace_level is not None and nace_level > 0:
            result_df['nace_r2'] = result_df['nace_r2'].apply(
                lambda x: x[:nace_level] if x else x
            )
            # Aggregate values by truncated NACE code and sum the values
            result_df = result_df.groupby(['nace_r2', 'geo'])['value'].sum().reset_index()
        
        # Convert to the required format for Sankey diagram
        return [
            {
                'source': row['nace_r2'],
                'target': flow_type,
                'value': float(row['value'])
            }
            for _, row in result_df.iterrows()
            if not pd.isna(row['value']) and row['value'] > 0  # Exclude zero values
        ]

    def get_flow_data(
        self, 
        year: int, 
        min_value: float = 0.0,
        drop_nan: bool = True,
        nace_level: int = None,
        regions: List[str] = None,
        include_imports: bool = True,
        include_exports: bool = True
    ) -> List[Dict[str, Union[str, float]]]:
        """Get filtered trade flow data for specified year."""
        flows = []
        
        if include_imports:
            imports = self._process_flow_file(
                self.imports_file, 
                year, 
                "Total Imports",
                min_value,
                drop_nan,
                nace_level,
                regions
            )
            flows.extend(imports)
            
        if include_exports:
            exports = self._process_flow_file(
                self.exports_file, 
                year, 
                "Total Exports",
                min_value,
                drop_nan,
                nace_level,
                regions
            )
            flows.extend(exports)
        
        return flows
