from setuptools import setup
from slurm_factory.version import version

def readme():
    with open('README.md') as f:
        return f.read()

setup(name = 'slurm_factory',
      version = version(),
      description = 'A package that allows to conveniently create and submit SLURM jobs',
      long_description = readme(),
      classifiers = [
        'Development Status :: 2 - Pre-Alpha',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Topic :: Scientific/Engineering',
        'Topic :: System :: Clustering',
        'Topic :: System :: Distributed Computing'
      ],
      url = 'https://github.com/krivenko/slurm_factory',
      author = 'Igor Krivenko',
      author_email = 'igor.s.krivenko@gmail.com',
      license = 'GPL',
      packages = ['slurm_factory'],
      include_package_data = True,
      zip_safe = True,
      tests_require = ['nose'],
      test_suite = 'nose.collector')
