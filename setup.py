from setuptools import setup, find_packages

setup(
    name="undetected-android-emulator",
    version="0.2.0",
    description="Undetectable Android Emulator with GUI",
    author="agentbryce2025",
    author_email="example@example.com",
    url="https://github.com/agentbryce2025/emulator",
    packages=find_packages(),
    install_requires=[
        "PyQt5",
        "pyside6",
        "frida",
        "pycdlib",
        "pillow",
        "numpy",
        "requests",
        "psutil",
        "aiohttp",
        "python-magic",
        "python-xlib",
        "pycryptodomex",
        "scikit-learn",
        "joblib",
        "matplotlib",
    ],
    entry_points={
        "console_scripts": [
            "undetected-emulator=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
)