from setuptools import setup, find_packages

setup(
    name="kotogram",
    version="8.0.0",
    packages=find_packages(),
    install_requires=["httpx>=0.27.0", "apscheduler>=3.10.0"],
    python_requires=">=3.9",
    author="ValeryAFK",
    description="Kotogram PRO — библиотека для Telegram ботов",
    url="https://github.com/valeryafk/kotogram",
)
