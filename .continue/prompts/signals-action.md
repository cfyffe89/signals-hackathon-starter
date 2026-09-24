---
name: signals-action
description: Build a Signals External Action page (FastAPI)
invokable: true
---
Build an External Action as a FastAPI GET route that returns HTML (see the /action route in backend/app.py).
- Signals opens the URL in the user's browser (dialog or new window) with ?__eid=<entity eid> (parameter name configurable; POST sends the entity object instead, always for Folders).
- Read the eid with Query(alias="__eid"), load data with SignalsClient, do the work.
- Return control with window.parent.postMessage(["closeAndContinue",[]], "<tenant origin>") (also close / closeAndAbort / setTitle / setWidth).
- To write back, use SignalsClient methods (e.g. upload_child_attachment, or PATCH /stoichiometry/{eid}/{rowid} for a stoichiometry row) with the parent digest.
- Register it in Signals Configuration › External Actions with the Codespaces port-8000 URL.

Apply this to the request the user types after the slash command.
