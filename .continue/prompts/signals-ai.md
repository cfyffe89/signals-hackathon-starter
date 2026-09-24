---
name: signals-ai
description: Add an AI feature grounded in Signals data and the knowledge pack
invokable: true
---
Add an AI feature that is grounded:
- Records: backend.context.experiment_context(sc, eid)["text"] (or structure_context(smiles)).
- Knowledge: backend.knowledge.knowledge_block(question) for API/integration answers.
- Call ai.ask(question, records=..., knowledge=...). It already tells the model to cite and not to invent.
- Show the answer plus what context was used, so users can check it.

Apply this to the request the user types after the slash command.
