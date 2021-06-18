The API
=======

Here we document all of the useful parts of the API.

Finding windows
---------------

See :doc:`finding_windows` for a guide.

.. py:currentmodule:: systa.windows

.. autodata:: current_windows

.. autoclass:: CurrentWindows
  :members:
  :special-members: __contains__, __getitem__

.. autoclass:: WindowSearchPredicate
  :members:

.. autodata:: WindowLookupType
  :annotation:

.. autoclass:: regex_search

Controlling windows
-------------------

.. autoclass:: Window
  :members:

.. autoclass:: WindowRelativeMouseController

Events
------

``listen_to`` decorators
^^^^^^^^^^^^^^^^^^^^^^^^

.. py:currentmodule:: systa.events.decorators.listen_to

.. automodule:: systa.events.decorators.listen_to
  :members:

``filter_by`` decorators
^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: systa.events.decorators.filter_by
  :members:
