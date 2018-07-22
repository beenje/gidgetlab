import pathlib
import setuptools


docs_requires = ["sphinx"]
tests_requires = ["pytest>=3.0.0", "pytest-asyncio"]
aiohttp_requires = ["aiohttp"]
treq_requires = ["treq", "twisted[tls]"]
tornado_requires = ["tornado"]

long_description = pathlib.Path("README.rst").read_text("utf-8")

setuptools.setup(
    name="gidgetlab",
    version="0.1.0",
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
    setup_requires=["pytest-runner>=2.11.0"],
    tests_require=tests_requires,
    install_requires=["uritemplate>=3.0.0"],
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
