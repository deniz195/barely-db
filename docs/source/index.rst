.. barely-db documentation master file, created by
   sphinx-quickstart on Sun May 10 19:50:05 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

==================================================
``barely-db``: A Database when you barely need one
==================================================




Getting Started
===============



Why?
====





Semantic vs Random Identifiers
==============================

An important requirement in any operation is the ability to uniquely refer to objects. Examples are: Your name (probably not exactly unique), your licence plate (unique), 


The different options to identify things can be put on a semantic scale of how much description is in the identifier, from ``Test_Sample_200303_SupplierA_25degC_Deniz`` (very semantic) to the identifier of a git revision ``975c061e90f3ac7a2641e5e9ffe68707628457b7`` (no semantics). Some where in between is e.g. the swiss licence plate ``ZH 7492874``, which contains the city of registration and a number.

It turns out that while computers can deal really well with 





https://www.w3.org/2001/03/identification-problem/
https://www.namingthings.co/




Example: A small bakery
=======================

+------------------------+------------+----------+----------+
| Header row, column 1   | Header 2   | Header 3 | Header 4 |
| (header rows optional) |            |          |          |
+========================+============+==========+==========+
| body row 1, column 1   | column 2   | column 3 | column 4 |
+------------------------+------------+----------+----------+
| body row 2             | ...        | ...      |          |
+------------------------+------------+----------+----------+



Full Table of Contents
======================

.. toctree::
   :maxdepth: 2
   :caption: Contents:



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
