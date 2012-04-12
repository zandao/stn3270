from distutils.core import setup

setup(
    name='stn3270',
    version='0.1.0',
    author='Alexandre "Zandao" Drummond',
    author_email='alexandre dot drummond at gmail dot com',
    packages=['stn3270', 'stn3270.test'],
    #scripts=['bin/x.py','bin/y.py'],
    url='http://pypi.python.org/pypi/stn3270/',
    license='LICENSE.txt',
    description='Super TN3270 is a very thin chocolate layer over py3270 cake.',
    long_description=open('README.txt').read(),
    install_requires=["py3270 >= 0.1.4"],
)
