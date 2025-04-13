# Econ Flow Visualizer 📊 🌐

A high-performance economic data visualization tool combining Python and Rust for analyzing international trade flows. This project is currently under active development and needs several fixes to reach its full potential.

![Work in Progress](https://img.shields.io/badge/Status-In_Development-yellow)
![Python](https://img.shields.io/badge/Python-3.12+-blue)
![Rust](https://img.shields.io/badge/Rust-Latest-orange)
![Flask](https://img.shields.io/badge/Flask-Latest-green)

## 🎯 Project Overview

This tool aims to provide interactive visualizations of economic input-output relationships using Eurostat FIGARO datasets. It combines Python's rich visualization capabilities with Rust's high-performance data processing.

### Current Features
- Web interface built with Flask
- Sankey diagram visualization of trade flows
- Rust-powered data processing core
- Support for Eurostat FIGARO TSV data format

### Known Issues to Fix 🔧
1. **Rust Integration Issues:**
   - Memory management optimizations needed in Rust core
   - Better error handling required between Python and Rust layers
   - Performance bottlenecks in TSV processing

2. **Data Processing:**
   - Need to handle missing values more gracefully
   - Improve validation of input data format
   - Add support for different data normalization methods

3. **Visualization:**
   - Enhanced interactivity needed in Sankey diagrams
   - Additional visualization types required
   - Better handling of large datasets

## 🚀 Installation

### Prerequisites

- Python 3.12+
- Rust toolchain (latest stable)
- `maturin` for Python-Rust binding compilation

### Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/econ-flow-visualizer
cd econ-flow-visualizer

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Build Rust components
cd rust_core
maturin develop
cd ..
```

## 📊 Data Requirements

### Supported Data Format
Currently supports Eurostat FIGARO datasets:
- `estat_naio_10_fgte.tsv`: Export data
- `estat_naio_10_fgti.tsv`: Import data

Data files should be placed in `data/figaro/` directory.

## 🔄 Development Roadmap

### Phase 1: Core Functionality Fixes
1. Optimize Rust data processing:
   - Implement proper error handling
   - Add data validation
   - Optimize memory usage

2. Enhance Python-Rust integration:
   - Improve type safety
   - Add comprehensive error reporting
   - Implement proper memory management

3. Add data preprocessing capabilities:
   - Data cleaning
   - Normalization options
   - Missing value handling

### Phase 2: Feature Enhancements
1. Visualization improvements:
   - Interactive filters
   - Multiple visualization types
   - Custom color schemes

2. Analysis features:
   - Time series analysis
   - Comparative analysis
   - Statistical summaries

## 🤝 Contributing

Contributions are welcome! Key areas where help is needed:

1. **Rust Core Optimization:**
   - Memory management
   - Error handling
   - Performance optimization

2. **Data Processing:**
   - Additional data format support
   - Validation improvements
   - Preprocessing features

3. **Visualization:**
   - New visualization types
   - Interactive features
   - Performance optimization

### Getting Started with Development

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Run Rust tests
cd rust_core
cargo test
```

## 📫 Getting Help

For assistance with development or usage:
1. Check the [issues](https://github.com/yourusername/econ-flow-visualizer/issues) for known problems
2. Create a new issue with:
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs actual behavior

## 📝 License

This project is licensed under the terms of the license file included in the repository.

---

<div align="center">
🔧 Under Active Development - Contributors Welcome! 🚀
</div>