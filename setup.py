from setuptools import setup, find_packages

setup(
    name="quant_factor_system",
    version="4.1.0",
    description="Quantitative Factor Mining and Research Platform",
    author="QuantFactorSystem",
    package_dir={"": "src"},
    packages=find_packages(where="src", exclude=["_archive", "_archive.*", "examples", "examples.*"]),
    python_requires=">=3.8",
    install_requires=[
        "pandas>=1.5.0",
        "numpy>=1.21.0",
        "scipy>=1.10.0",
        "sqlalchemy>=2.0.0",
        "psycopg2-binary>=2.9.0",
        "matplotlib>=3.5.0",
        "plotly>=5.10.0",
        "streamlit>=1.20.0",
        "python-dateutil>=2.8.0",
        "pytz>=2023.3",
        "pyyaml>=6.0",
    ],
    extras_require={
        "ricequant": ["rqdatac>=1.0.0"],
        "mining": ["qlib>=0.9.0"],
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "quant-mining=mining.cli:main",
            "quant-research=research.cli.main:main",
        ],
    },
)
