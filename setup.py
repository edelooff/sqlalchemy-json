from setuptools import setup, find_packages

if __name__ == "__main__":
    setup(
        name='sqlalchemy-json',
        version="1.0.0",
        description="A full-featured JSON type with mutation tracking for SQLAlchemy",
        author="Elmer de Looff",
        author_email="elmer.delooff@gmail.com",
        url="https://github.com/edelooff/sqlalchemy-json",
        packages=find_packages(),
        install_requires=[
            'sqlalchemy>=0.7'
        ],
        zip_safe=False,
        classifiers=[
            'License :: OSI Approved :: BSD License',
            'Programming Language :: Python',
            'Programming Language :: Python :: 3',
        ],
    )
