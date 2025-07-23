from setuptools import setup, find_packages

setup(
    name='build_logger',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'build_logger=build_logger.get_build_logs:main'
            ] ,
    },
)