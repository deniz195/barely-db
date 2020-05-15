Example - A bakery 
==================


Create an example database:

.. code-block:: python

    >>> import barely_db
    >>> import barely_db.examples

    >>> bdb = barely_db.examples.make_example_db('./BakeryDatabase')
    >>> bdb.load_entities()

    >>> print(bdb['CU0005'])
    BarelyDBEntity('CU0005', 'Billy Fuller')


.. code-block:: python

    print(bdb['EQ0004-D1'])


.. code-block:: python

    >>> ent = bdb['EQ0004-D1']
    >>> ent
    BarelyDBEntity('EQ0004-D1', 'scale_30kg', components=['D1', 'D2'])

    >>> ent.path
    WindowsPath('C:/Repo/barely-db/examples/BakeryDatabase/equipment/EQ0004_scale_30kg/-D1_device1')



.. code-block:: python

    import attr

    @barely_db.serialize_to_file(base_file_identifier='dough_recipe.json')
    @barely_db.cattr_json_serialize
    @attr.s(frozen=True, kw_only=True)
    class DoughRecipe():
        water = attr.ib(default='IG0004-B1')
        flour = attr.ib(default='IG0001-B1')

        w_water = attr.ib(default='1kg')
        w_flour = attr.ib(default='1kg')    



.. code-block:: python

    dr = DoughRecipe(w_water='1.34kg', w_flour='1.57kg')

    print(dr.serialize())

    >>> {
    >>>     "water": "IG0004-B1",
    >>>     "flour": "IG0001-B1",
    >>>     "w_water": "1.34kg",
    >>>     "w_flour": "1.57kg"
    >>> }


We will save the dough recipe to a entity

.. code-block:: python

    ent = bdb.create_new_entity(after='BR0001', name='sourdough')
    ent.save_object(dr)    

    print(ent)
    >>> BarelyDBEntity('BR0031', 'sourdough')


The dough recipe can easily reconstructed

.. code-block:: python

    assert ent.has_object(DoughRecipe)

    ent.load_object(DoughRecipe) == dr
    >>> True

