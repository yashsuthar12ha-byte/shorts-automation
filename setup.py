from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="ai-game-shorts",
    version="1.0.0",
    author="AI Game Shorts",
    description="Autonomous AI YouTube Shorts Creator for Gaming Content",
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires=">=3.10",
    install_requires=requirements,
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "aigameshorts=scripts.run_pipeline:cli",
        ],
    },
)
