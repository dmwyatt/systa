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
  :special-members: __eq__

.. autoclass:: WindowRelativeMouseController

Events
------

The user's function will be called with one argument whose value is an instance of the
``EventData`` :func:`~dataclasses.dataclass`.

``listen_to`` decorators
^^^^^^^^^^^^^^^^^^^^^^^^

.. py:currentmodule:: systa.events.decorators.listen_to

.. automodule:: systa.events.decorators.listen_to
  :members:

``filter_by`` decorators
^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: systa.events.decorators.filter_by
  :members:

Event types
^^^^^^^^^^^

.. autoclass:: systa.events.types.EventData
  :members:

.. autoclass:: systa.events.types.CallbackReturn
  :members:

.. autoclass:: systa.events.types.EventType
  :members:

.. autoclass:: systa.events.types.EventTypeNamesType
