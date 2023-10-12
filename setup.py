from setuptools import setup, find_packages

setup(
    name="VariantAnnotator",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "asyncio",
        "numpy",
        "tqdm",
        "aiohttp",
        "xlsxwriter"
    ],
    author="Shiwani Limbu",
    author_email="slimbu@ucmerced.edu",
    description="Annotates vcf file variants",
    license="MIT",
    keywords="Variant annotation package",
    url="NA",  # project home page, if any
)
