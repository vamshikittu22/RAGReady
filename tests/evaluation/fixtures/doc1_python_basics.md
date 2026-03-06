# Python Programming Fundamentals

## History and Origins

Python was created by Guido van Rossum and first released in 1991. Van Rossum began working on Python in December 1989 at Centrum Wiskunde & Informatica (CWI) in the Netherlands. He named the language after the BBC comedy show "Monty Python's Flying Circus." The reference implementation of Python is called CPython, which is written in C and maintained by the Python Software Foundation. Python 2.0 was released in October 2000 and introduced list comprehensions and a garbage collector with reference counting. Python 3.0, released in December 2008, was a major backward-incompatible revision that fixed fundamental design flaws.

## Type System

Python uses dynamic typing, meaning variable types are determined at runtime rather than compile time. A variable can hold a string value and later be reassigned to an integer without any error. Starting with Python 3.5, type hints were introduced through PEP 484, allowing developers to annotate function signatures and variable types. Type hints are optional and do not affect runtime behavior — they are used by static analysis tools like mypy for type checking. Python 3.10 introduced the match statement for structural pattern matching, similar to switch-case statements in other languages.

## Core Data Types

Python provides several built-in data types. A list is an ordered, mutable sequence that allows duplicate elements and supports indexing with O(1) access time. A dictionary (dict) is an unordered collection of key-value pairs with O(1) average lookup time, implemented using hash tables since Python 3.7 dictionaries maintain insertion order. A tuple is an immutable ordered sequence, commonly used for returning multiple values from functions and as dictionary keys. A set is an unordered collection of unique elements that supports mathematical set operations like union, intersection, and difference with O(1) average membership testing.

## Virtual Environments

Python virtual environments provide isolated spaces for project dependencies. The venv module, included in the Python standard library since Python 3.3, creates lightweight virtual environments. The pip package manager installs packages from the Python Package Index (PyPI), which hosts over 500,000 third-party packages. Virtual environments prevent dependency conflicts between projects by maintaining separate site-packages directories. The requirements.txt file lists project dependencies with version specifiers, and pip freeze generates a snapshot of all installed packages.

## Functions and Decorators

Python functions are first-class objects, meaning they can be assigned to variables, passed as arguments, and returned from other functions. Decorators are a syntactic sugar for wrapping functions, using the @decorator_name syntax above the function definition. Common built-in decorators include @staticmethod, @classmethod, and @property. Lambda expressions create small anonymous functions limited to a single expression, using the syntax lambda arguments: expression.

## Error Handling

Python uses try-except blocks for exception handling. The raise statement creates custom exceptions, and the finally clause executes cleanup code regardless of whether an exception occurred. Python follows the EAFP principle (Easier to Ask Forgiveness than Permission), preferring try-except over pre-checking conditions. The with statement provides context managers for automatic resource cleanup, commonly used with file operations and database connections.
