"""Setup configuration for ProxyHunter package."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Requirements
requirements = [
    'requests>=2.31.0',
    'flask>=3.1.1',
    'urllib3>=2.2.0',
    'certifi>=2024.0.0',
    'flask-socketio>=5.3.0',
    'python-socketio>=5.10.0',
    'eventlet>=0.33.0',
    'Jinja2>=3.1.0'
]

setup(
    name="proxy-meshx",
    version="2.3.0",
    author="sheng1111",
    author_email="ysl58200@gmail.com",
    description="Professional proxy fetching and validation tool for red team operations and web scraping",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sheng1111/Proxy-Hunter",
    project_urls={
        "Bug Reports": "https://github.com/sheng1111/Proxy-Hunter/issues",
        "Source": "https://github.com/sheng1111/Proxy-Hunter",
        "Documentation": "https://github.com/sheng1111/Proxy-Hunter/blob/main/README.md",
    },
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'proxyhunter': [
            'public/*.html',
            'public/*.css',
            'public/*.js',
            'i18n/*.json',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: Proxy Servers",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Security",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Networking",
    ],
    keywords="proxy, scraping, red-team, security, networking, validation, anonymity",
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        'dev': [
            'pytest>=8.0.0',
            'pytest-cov>=4.0.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'mypy>=1.0.0',
        ],
        'web': [
            'gunicorn>=21.0.0',
            'waitress>=3.0.0',
        ],
        'full': [
            'plotly>=5.18.0',
            'pandas>=2.1.0',
            'sqlalchemy>=2.0.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'proxymeshx=proxyhunter.__main__:main',
            'proxy-meshx=proxyhunter.__main__:main',
        ],
    },
    zip_safe=False,
    test_suite='tests',
    tests_require=[
        'pytest>=8.0.0',
        'pytest-cov>=4.0.0',
    ],
)
