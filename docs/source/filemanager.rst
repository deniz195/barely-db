Filemanager
===========

Create an example database:

.. code-block:: python

    >>> import barely_db
    >>> import barely_db.examples

    >>> bdb = barely_db.examples.make_example_db('./BakeryDatabase')
    >>> bdb.load_entities()

    >>> print(bdb['CU0005'])
    BarelyDBEntity('CU0005', 'Billy Fuller')



