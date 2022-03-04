import pathlib
import setuptools


docs_requires = ["sphinx>=4.0.0", "sphinx-autodoc-typehints", "sphinx-rtd-theme"]
tests_requires = ["pytest>=3.0.0", "pytest-asyncio", "pytest-cov", "pytest-aiohttp"]
aiohttp_requires = ["aiohttp", "cachetools"]
httpx_requires = ["httpx>=0.11.0"]
treq_requires = ["treq<21", "twisted[tls]"]
tornado_requires = ["tornado"]

long_description = pathlib.Path("README.rst").read_text("utf-8")

setuptools.setup(
    name="gidgetlab",
    description="An async GitLab API library",
    long_description=long_description,
    url="https://gitlab.com/beenje/gidgetlab",
    author="Benjamin Bertrand",
    author_email="beenje@gmail.com",
    license="Apache",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    keywords="gitlab sans-io async",
    packages=setuptools.find_packages(exclude=("tests", "tests.*")),
    zip_safe=True,
    python_requires=">=3.6.0",
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    tests_require=tests_requires,
    extras_require={
        "docs": docs_requires,
        "tests": tests_requires,
        "aiohttp": aiohttp_requires,
        "httpx": httpx_requires,
        "treq": treq_requires,
        "tornado": tornado_requires,
        "dev": (
            docs_requires
            + tests_requires
            + aiohttp_requires
            + httpx_requires
            + treq_requires
            + tornado_requires
        ),
    },
)
