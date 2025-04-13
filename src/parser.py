from typing import List, Dict, Union, Optional, Set
import os
import pandas as pd
from dataclasses import dataclass

class FIGAROError(Exception):
    """Base exception for FIGARO-related errors."""
    pass

class FileFormatError(FIGAROError):
    """Exception raised when file format is invalid."""
    pass

class YearNotFoundError(FIGAROError):
    """Exception raised when requested year is not found in data."""
    pass

@dataclass
class FIGAROMetadata:
    freq: str
    nace_r2: str
    c_exp: str
    unit: str
    geo: str

class FIGAROParser:
    """Parser for FIGARO format TSV files."""
    
    def __init__(self, data_dir: str, validate_files: bool = True):
        """Initialize the FIGARO parser with data directory path."""
        self.data_dir = data_dir
        self.imports_file = os.path.join(data_dir, 'figaro', 'estat_naio_10_fgti.tsv')
        self.exports_file = os.path.join(data_dir, 'figaro', 'estat_naio_10_fgte.tsv')
        if validate_files:
            self._validate_files()

    def get_value_range(self, year: int) -> Dict[str, float]:
        """Get the minimum and maximum values for a given year."""
        try:
            # Read both files
            imports_df = pd.read_csv(self.imports_file, sep='\t')
            exports_df = pd.read_csv(self.exports_file, sep='\t')
            
            year_str = str(year)
            if year_str not in imports_df.columns or year_str not in exports_df.columns:
                raise YearNotFoundError(f"Year {year} not found in data")
            
            # Get min/max values from both files
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
        except Exception as e:
            raise ValueError(f"Error getting value range: {str(e)}")

    def get_available_regions(self) -> List[str]:
        """Get list of available geographic regions."""
        try:
            # Read both files
            imports_df = pd.read_csv(self.imports_file, sep='\t', nrows=None)
            exports_df = pd.read_csv(self.exports_file, sep='\t', nrows=None)
            
            # Extract and parse metadata
            imports_meta = imports_df.iloc[:, 0].apply(self.parse_metadata)
            exports_meta = exports_df.iloc[:, 0].apply(self.parse_metadata)
            
            # Combine unique regions
            regions = set()
            for meta in [imports_meta, exports_meta]:
                regions.update(m.geo for m in meta if m is not None)
            
            return sorted(list(regions))
        except Exception as e:
            raise ValueError(f"Error getting available regions: {str(e)}")

    def truncate_nace_code(self, code: str, level: int) -> str:
        """Truncate NACE code to specified level."""
        if not code or level < 1:
            return code
        parts = code.split('.')
        return '.'.join(parts[:level])

    def _validate_files(self) -> None:
        """Validate that required files exist and have correct format."""
        for file_path in [self.imports_file, self.exports_file]:
            if not os.path.exists(file_path):
                raise FileNotFoundError(
                    f"Required FIGARO file not found: {file_path}\n"
                    "Make sure you have downloaded the FIGARO dataset files and placed "
                    "them in the correct directory structure: data/figaro/"
                )
            
            try:
                # Read just the first row for validation
                df = pd.read_csv(file_path, sep='\t', nrows=1)
                if df.empty:
                    raise FileFormatError(f"File is empty: {file_path}")
                    
                first_col = df.columns[0]
                sample_value = df.iloc[0][first_col]
                parts = sample_value.split(',')
                
                if len(parts) < 5:
                    raise FileFormatError(
                        f"First column in {file_path} does not have the expected "
                        "comma-separated format (freq,nace_r2,c_exp,unit,geo). "
                        f"Found: {sample_value}"
                    )
            except pd.errors.EmptyDataError:
                raise FileFormatError(f"File is empty: {file_path}")
            except Exception as e:
                raise FileFormatError(f"Invalid FIGARO file format in {file_path}: {str(e)}")
    
    @staticmethod
    def parse_metadata(value: str) -> Optional[FIGAROMetadata]:
        """Parse comma-separated metadata from first column."""
        if not value or not isinstance(value, str):
            return None
            
        parts = [part.strip() for part in value.split(',')]
        if len(parts) >= 5:
            return FIGAROMetadata(
                freq=parts[0],
                nace_r2=parts[1],
                c_exp=parts[2],
                unit=parts[3],
                geo=parts[4]
            )
        return None

    def get_available_years(self) -> List[int]:
        """Get list of available years in the dataset."""
        try:
            df = pd.read_csv(self.imports_file, sep='\t')
            if df.empty:
                return []
                
            year_columns = df.columns[1:]  # All columns except the first metadata column
            return sorted([
                int(year.strip()) 
                for year in year_columns 
                if year.strip().isdigit()
            ])
        except Exception as e:
            raise ValueError(f"Error reading years from dataset: {str(e)}")

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
        """Process a single flow file with enhanced filtering."""
        df = pd.read_csv(file_path, sep='\t')
        if df.empty:
            return []
            
        # Extract metadata from first column
        metadata_col = df.iloc[:, 0].apply(self.parse_metadata)
        
        # Get the values for the specified year
        year_str = str(year)
        if year_str not in df.columns:
            raise YearNotFoundError(
                f"Year {year} not found in data. Available years: "
                f"{', '.join(str(y) for y in self.get_available_years())}"
            )
        
        # Create initial dataframe with metadata and values
        result_df = pd.DataFrame({
            'nace_r2': metadata_col.apply(lambda x: x.nace_r2 if x else None),
            'value': df[year_str],
            'geo': metadata_col.apply(lambda x: x.geo if x else None)
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
                lambda x: self.truncate_nace_code(x, nace_level)
            )
            # Aggregate values by truncated NACE code
            result_df = result_df.groupby('nace_r2')['value'].sum().reset_index()
        
        # Convert to the required format
        return [
            {
                'source': row['nace_r2'],
                'target': flow_type,
                'value': float(row['value'])
            }
            for _, row in result_df.iterrows()
            if not pd.isna(row['value'])  # Extra safety check
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
        """
        Get filtered trade flow data for specified year.
        
        Args:
            year: The year to get data for
            min_value: Minimum value to include in results (default: 0.0)
            drop_nan: Whether to drop NaN values (default: True)
            nace_level: Level of NACE code aggregation (default: None)
            regions: List of geographic regions to include (default: None)
            include_imports: Whether to include import flows (default: True)
            include_exports: Whether to include export flows (default: True)
        
        Returns:
            List of dictionaries containing flow data with 'source', 'target', 'value' keys
        """
        try:
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
            
        except YearNotFoundError:
            raise
        except FileFormatError:
            raise
        except Exception as e:
            raise ValueError(f"Error processing flow data for year {year}: {str(e)}")
