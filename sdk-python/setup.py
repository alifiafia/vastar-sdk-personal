from setuptools import setup, find_packages
setup(
    name="vastar-connector-sdk",
    version="0.1.0",
    packages=find_packages(include=["vastar_connector_sdk", "vastar_connector_sdk.*"]),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "flatbuffers>=23.5.26",
    ],
)
