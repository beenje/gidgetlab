import pathlib
import setuptools


docs_requires = ["sphinx", "sphinx-autodoc-typehints"]
tests_requires = ["pytest>=3.0.0", "pytest-asyncio", "pytest-cov", "pytest-aiohttp"]
aiohttp_requires = ["aiohttp", "cachetools"]
treq_requires = ["treq", "twisted[tls]"]
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
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
    ],
    keywords="gitlab sans-io async",
    packages=setuptools.find_packages(),
    zip_safe=True,
    python_requires=">=3.6.0",
    use_scm_version=True,
    setup_requires=["setuptools_scm", "pytest-runner>=2.11.0"],
    tests_require=tests_requires,
    extras_require={
        "docs": docs_requires,
        "tests": tests_requires,
        "aiohttp": aiohttp_requires,
        "treq": treq_requires,
        "tornado": tornado_requires,
        "dev": (
            docs_requires
            + tests_requires
            + aiohttp_requires
            + treq_requires
            + tornado_requires
        ),
    },
)
