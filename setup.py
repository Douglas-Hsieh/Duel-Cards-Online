import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-game',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    license='BSD License',
    description='Duel Cards Online is a game inspired by trading card games like Hearthstone that allows users to create and play with customized cards.',
    long_description=README,
    url='https://www.douglashsieh.com/',
    author='Douglas Hsieh',
    author_email='douglas.w.hsieh@g.ucla.edu',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 2.2',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
