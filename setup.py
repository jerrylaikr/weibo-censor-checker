import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="weibo-censor-checker",
    version="0.1.0",
    author="Dokudenpa",
    author_email="",
    description="Check modified/censored weibo posts.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jerrylaikr/weibo-censor-checker",
    packages=setuptools.find_packages(),
    package_data={"wb_feed_spider": ["config_sample.json", "logging.conf"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    install_requires=["lxml", "requests", "tqdm", "pymongo"],
    python_requires=">=3.6",
)
