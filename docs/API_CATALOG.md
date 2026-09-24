# Revvity Signals Notebook REST API — Master Endpoint Catalog
*Consolidated reference for Hackathon Developers and AI Copilots. Generated from all 21 OpenAPI 3.0 specifications.*

---

## Quick Reference & Protocol Rules
- **Base URL:** `https://<tenant>.signalsnotebook.revvitycloud.com/api/rest/v1.0`
- **Required Headers:**
  ```http
  x-api-key: <YOUR_SIGNALS_API_KEY>
  Content-Type: application/vnd.api+json
  Accept: application/vnd.api+json
  ```
- **Standard Envelope (JSON:API 1.0):** Standard requests and responses wrap entities in `{"data": {"type": "...", "attributes": {...}}}`.
- **Golden Child Upload Rule:** Always append `?force=true` when uploading file attachments or notes to child entities to prevent 409 conflicts.

---

## Domain Directory
- [Assay Data & Curves](#assay-data-curves) (27 endpoints)
- [Custom Attributes & Fields](#custom-attributes-fields) (11 endpoints)
- [Chemistry & Structure Search](#chemistry-structure-search) (2 endpoints)
- [Contract Research (CRO)](#contract-research-cro) (37 endpoints)
- [Notebook Entities & Hierarchy](#notebook-entities-hierarchy) (61 endpoints)
- [Chemical Fragments](#chemical-fragments) (12 endpoints)
- [Hierarchical Data Tables](#hierarchical-data-tables) (12 endpoints)
- [Entity Audit Trail & History](#entity-audit-trail-history) (4 endpoints)
- [Containers & Storage Locations](#containers-storage-locations) (45 endpoints)
- [Materials & Inventory Reagents](#materials-inventory-reagents) (46 endpoints)
- [Biopolymers & Monomers](#biopolymers-monomers) (9 endpoints)
- [External Actions & Webhooks](#external-actions-webhooks) (3 endpoints)
- [Parallel Experiments (DOE)](#parallel-experiments-doe) (22 endpoints)
- [Well Plates & High-Throughput Screening](#well-plates-high-throughput-screening) (14 endpoints)
- [SCIM Identity Management](#scim-identity-management) (18 endpoints)
- [Stoichiometry & Reaction Tables](#stoichiometry-reaction-tables) (19 endpoints)
- [Equipment & Instrument Synergy](#equipment-instrument-synergy) (40 endpoints)
- [System & Health](#system-health) (4 endpoints)
- [Async Background Tasks](#async-background-tasks) (12 endpoints)
- [Users & Groups](#users-groups) (27 endpoints)

---

## Assay Data & Curves
| Method | Path | Summary / Description | Key Parameters |
| :--- | :--- | :--- | :--- |
| **`GET`** | `/adt/{eid}` | Fetch content of Admin Defined Tables | None |
| **`POST`** | `/adt/{eid}` | Add a new row to Admin Defined Table | None |
| **`PATCH`** | `/adt/{eid}` | Bulk update content of Admin Defined Table | None |
| **`GET`** | `/adt/{eid}/_column` | Fetch column definitions of Admin Defined Tables | None |
| **`PATCH`** | `/adt/{eid}/_column` | Update column definitions of Admin Defined Table | None |
| **`GET`** | `/adt/{eid}/{rowid}` | Fetch specified row of Admin Defined Table | `rowid*` (path) |
| **`PATCH`** | `/adt/{eid}/{rowid}` | Update specified row of Admin Defined Table | `rowid*` (path) |
| **`DELETE`** | `/adt/{eid}/{rowid}` | Delete specified row of Admin Defined Table | `rowid*` (path) |
| **`GET`** | `/worksheet/{eid}` | Fetch content of specified worksheet | None |
| **`PATCH`** | `/worksheet/{eid}` | Update specified worksheet | None |
| **`GET`** | `/worksheet/{eid}/_fields` | Fetch worksheet field definitions | None |
| **`GET`** | `/worksheet/settings/unlock/reasons` | Fetch predefined worksheet unlock reasons | None |
| **`GET`** | `/variationsTables/{eid}` | Fetch content of variations table | None |
| **`PATCH`** | `/variationsTables/{eid}` | Update content of variations table | None |
| **`PUT`** | `/variationsTables/{eid}` | Replace content of variations table | None |
| **`GET`** | `/variationsTables/{eid}/_column` | Fetch column definition of variations table | None |
| **`PATCH`** | `/variationsTables/{eid}/_column` | Update column definitions of variations table | None |
| **`GET`** | `/variationsTables/{eid}/components` | Fetch content of component table | None |
| **`PATCH`** | `/variationsTables/{eid}/components` | Update content of component table | None |
| **`GET`** | `/variationsTables/{eid}/components/{rowId}` | Fetch specified row of component table | None |
| **`PATCH`** | `/variationsTables/{eid}/components/{rowId}` | Update specified row of component table | None |
| **`DELETE`** | `/variationsTables/{eid}/components/{rowId}` | Delete specified row from component table | None |
| **`GET`** | `/variationsTables/{eid}/variants/{variantId}` | Fetch content of variant table | None |
| **`PATCH`** | `/variationsTables/{eid}/variants/{variantId}` | Update content of variant table | None |
| **`DELETE`** | `/variationsTables/{eid}/variants/{variantId}` | Delete specified variant table from variations table | None |
| **`GET`** | `/variationsTables/{eid}/variants/{variantId}/{rowId}` | Fetch specified row of variant table | None |
| **`PATCH`** | `/variationsTables/{eid}/variants/{variantId}/{rowId}` | Update specified row of variant table | None |


## Custom Attributes & Fields
| Method | Path | Summary / Description | Key Parameters |
| :--- | :--- | :--- | :--- |
| **`GET`** | `/attributes` | Fetch all Attributes | None |
| **`POST`** | `/attributes` | Create a new Attribute | None |
| **`GET`** | `/attributes/{eid}` | Fetch content of Attribute | None |
| **`PATCH`** | `/attributes/{eid}` | Update content of Attribute | None |
| **`DELETE`** | `/attributes/{eid}` | Delete an Attribute | None |
| **`GET`** | `/attributes/{eid}/options` | Fetch options of Attribute | None |
| **`PATCH`** | `/attributes/{eid}/options` | Update options of Attribute | None |
| **`POST`** | `/attributes/{eid}/refresh` | Refresh content of an external list Attribute | None |
| **`GET`** | `/attributes/ontology/options/{optionId}/details` | Fetch ontology option details by option ID | None |
| **`GET`** | `/attributes/{eid}/ontology/options` | Fetch ontology options for an attribute | `search` (query), `page[limit]` (query) |
| **`GET`** | `/autotext/lists/{autotextListId}` | Fetch content of autotext list | None |


## Chemistry & Structure Search
| Method | Path | Summary / Description | Key Parameters |
| :--- | :--- | :--- | :--- |
| **`POST`** | `/chemistry/pairedSequence` | Add a child paired sequence chemicalDrawing from two single oligonucleotide sequences | `eid*` (query), `pageId` (query), `pageOffset` (query) |
| **`PUT`** | `/chemistry/{eid}/pairedSequence` | Update the chemical drawing with a paired sequence | `position` (query) |


## Contract Research (CRO)
| Method | Path | Summary / Description | Key Parameters |
| :--- | :--- | :--- | :--- |
| **`GET`** | `/cro/entities/{eid}` | Fetch entity by entity ID for CRO user | `include` (query) |
| **`GET`** | `/cro/entities/{eid}/properties` | Fetch entity properties for CRO user | None |
| **`PATCH`** | `/cro/entities/{eid}/properties` | Update entity properties for CRO user | None |
| **`GET`** | `/cro/entities/{eid}/children` | Fetch children of a specified entity for CRO user | `order` (query), `include` (query) |
| **`GET`** | `/cro/entities/{eid}/ancestors` | Fetch ancestors of a specified entity for CRO user | None |
| **`GET`** | `/cro/entities/{eid}/relationships` | Fetch related entities of a specified entity for CRO user | `include` (query) |
| **`GET`** | `/cro/entities/{eid}/export` | Fetch entity content for CRO user | `format` (query) |
| **`GET`** | `/cro/entities/{eid}/compliance` | Get compliance of specified entity for CRO user | `include` (query) |
| **`PATCH`** | `/cro/entities/{eid}/compliance` | Update compliance of specified entity for CRO user | `force` (query) |
| **`GET`** | `/cro/samples/{sampleId}/properties` | Fetch sample properties for CRO user | `name` (query) |
| **`PATCH`** | `/cro/samples/{sampleId}/properties` | Update sample properties for CRO user | `name` (query) |
| **`GET`** | `/cro/samples/{sampleId}/properties/{propertyId}` | Fetch sample properties by ID for CRO user | `propertyId*` (path) |
| **`PATCH`** | `/cro/samples/{sampleId}/properties/{propertyId}` | Update sample properties by ID for CRO user | `propertyId*` (path) |
| **`PUT`** | `/cro/samples/{sampleId}/status` | Update sample status for CRO User | None |
| **`GET`** | `/cro/samplesTables/{samplesTableId}/rows` | Fetch rows from samples table/summary for CRO user | None |
| **`PATCH`** | `/cro/samplesTables/{samplesTableId}/rows` | Bulk update samples in samples table/summary for CRO user | None |
| **`GET`** | `/cro/adt/{eid}` | Fetch content of Admin Defined Tables for CRO user | None |
| **`POST`** | `/cro/adt/{eid}` | Add a new row to Admin Defined Table for CRO user | None |
| **`PATCH`** | `/cro/adt/{eid}` | Bulk update content of Admin Defined Table for CRO user | None |
| **`GET`** | `/cro/adt/{eid}/_column` | Fetch column definitions of Admin Defined Tables for CRO user | None |
| **`GET`** | `/cro/adt/{eid}/{rowid}` | Fetch specified row of Admin Defined Table for CRO user | `rowid*` (path) |
| **`PATCH`** | `/cro/adt/{eid}/{rowid}` | Update specified row of Admin Defined Table for CRO user | `rowid*` (path) |
| **`GET`** | `/cro/worksheet/{eid}` | Fetch content of specified worksheet for CRO user | None |
| **`PATCH`** | `/cro/worksheet/{eid}` | Update specified worksheet for CRO user | None |
| **`GET`** | `/cro/worksheet/{eid}/_fields` | Fetch worksheet field definitions for CRO user | None |
| **`GET`** | `/cro/worksheet/settings/unlock/reasons` | Fetch predefined worksheet unlock reasons for CRO user | None |
| **`GET`** | `/cro/stoichiometry/{eid}` | Fetch stoichiometry data of experiment or chemicalDrawing for CRO user | `fields[stoichiometry]` (query) |
| **`GET`** | `/cro/stoichiometry/{eid}/{rowid}` | Fetch one specified row of stoichiometry data grid by id for CRO user | `rowid*` (path) |
| **`PATCH`** | `/cro/stoichiometry/{eid}/{rowid}` | Update row value of stoichiometry grid for CRO user | `rowid*` (path), `syncUpdateToSample` (query) |
| **`GET`** | `/cro/stoichiometry/{eid}/{rowid}/structure` | Fetch structure of reactants/products for CRO user | `rowid*` (path), `format` (query) |
| **`GET`** | `/cro/stoichiometry/{eid}/reactants` | Fetch all reactants for CRO user | None |
| **`GET`** | `/cro/stoichiometry/{eid}/products` | Fetch all products for CRO user | None |
| **`GET`** | `/cro/stoichiometry/{eid}/solvents` | Fetch all solvents for CRO user | None |
| **`GET`** | `/cro/chemicaldrawings/{eid}/reaction/{position}` | Fetch structure parts of current reaction for CRO user | `position*` (path) |
| **`POST`** | `/cro/chemicaldrawings/{eid}/reaction/{position}` | Append structure to current reaction for CRO user | `position*` (path) |
| **`POST`** | `/cro/entities/{eid}/children/{filename}` | Post an attachment to entity as a child for CRO user | `filename*` (path), `pageId` (query), `pageOffset` (query), `force` (query) |
| **`PUT`** | `/cro/entities/{eid}/attachment` | Replace attachment with a new file for CRO user | `force` (query) |


## Notebook Entities & Hierarchy
| Method | Path | Summary / Description | Key Parameters |
| :--- | :--- | :--- | :--- |
| **`GET`** | `/entities` | Fetch all entities | `includeTypes` (query), `excludeTypes` (query), `includeOptions` (query), `start` (query), `end` (query) |
| **`POST`** | `/entities` | Create a new entity | `force` (query) |
| **`GET`** | `/entities/{eid}` | Fetch entity by entity ID | `include` (query) |
| **`DELETE`** | `/entities/{eid}` | Delete entity by entity ID | `force` (query) |
| **`GET`** | `/entities/webdav/info` | Fetch entity information using webdav URL | `url` (query) |
| **`GET`** | `/entities/{eid}/children` | Fetch children of a specified entity | `order` (query), `include` (query) |
| **`GET`** | `/entities/{eid}/ancestors` | Fetch ancestors of a specified entity | None |
| **`GET`** | `/entities/{eid}/relationships` | Fetch related entities of a specified entity | `include` (query) |
| **`POST`** | `/entities/{eid}/relationships` | Create a new relationship | None |
| **`GET`** | `/entities/{eid}/properties` | Fetch entity properties | None |
| **`PATCH`** | `/entities/{eid}/properties` | Update entity properties | None |
| **`PATCH`** | `/entities/{eid}/move` | Move an experiment to another notebook | None |
| **`GET`** | `/entities/{eid}/shares` | Fetch all shares of an entity | None |
| **`POST`** | `/entities/{eid}/shares` | Add a new share to an entity | None |
| **`GET`** | `/entities/{eid}/shares/{shareId}` | Fetch share by share ID | None |
| **`PATCH`** | `/entities/{eid}/shares/{shareId}` | Update share by share ID | None |
| **`DELETE`** | `/entities/{eid}/shares/{shareId}` | Delete a share from an entity | None |
| **`GET`** | `/entities/{eid}/pdf` | Export entity to a PDF file | `header` (query), `footer` (query), `attachments` (query), `links` (query), `comments` (query) (+3 more) |
| **`PUT`** | `/entities/export/pdf` | Export entity to a PDF file asynchronously | `header` (query), `footer` (query), `attachments` (query), `links` (query), `comments` (query) (+3 more) |
| **`GET`** | `/entities/export/pdf/{fileid}` | Download file while exporting PDF asynchronously | `fileid*` (path), `filename` (query) |
| **`POST`** | `/entities/export/bulk` | Bulk export contents of an entity asynchronously | `depth` (query), `types` (query), `structureFormat` (query), `stoichiometry` (query), `stoichiometryStructureFormat` (query) |
| **`GET`** | `/entities/export/bulk/{jobId}` | Get the status of bulk export | `jobId*` (path) |
| **`GET`** | `/entities/export/bulk/{jobId}/contents` | Download the contents of bulk export | `jobId*` (path) |
| **`GET`** | `/entities/{eid}/export` | Fetch entity content | `format` (query) |
| **`POST`** | `/entities/{eid}/children/{filename}` | Post an attachment to entity as a child | `filename*` (path), `pageId` (query), `pageOffset` (query), `force` (query) |
| **`PUT`** | `/entities/{eid}/attachment` | Replace attachment with a new file | `force` (query) |
| **`GET`** | `/entities/{eid}/reviews` | Fetch signing reviews by entity ID | None |
| **`POST`** | `/entities/{eid}/reviews/close` | Close entity without signing | None |
| **`POST`** | `/entities/{eid}/reviews/reopen` | Reopen an entity | None |
| **`POST`** | `/entities/{eid}/reviews/archive` | Archive closed entity by entity ID | None |
| **`POST`** | `/entities/{eid}/reviews/unarchive` | Unarchive archived entity by entity ID | None |
| **`GET`** | `/entities/{eid}/history` | Fetch histories of specified entity | `depth` (query), `action` (query) |
| **`GET`** | `/entities/{eid}/compliance` | Get compliance of specified entity | `include` (query) |
| **`PATCH`** | `/entities/{eid}/compliance` | Update compliance of specified entity | `force` (query) |
| **`GET`** | `/entities/{eid}/comments` | Fetch comments of specified entity | `depth` (query) |
| **`GET`** | `/entities/{eid}/comments/{commentId}` | Fetch comment by comment ID | None |
| **`DELETE`** | `/entities/{eid}/comments/{commentId}` | Delete comment by ID | None |
| **`GET`** | `/entities/{eid}/layout/pages` | Fetch pages of UI layout | None |
| **`POST`** | `/entities/{eid}/layout/pages` | Add a new page to UI page layout | `force` (query) |
| **`GET`** | `/entities/{eid}/layout/pages/{pageId}` | Fetch layout page by id | None |
| **`PATCH`** | `/entities/{eid}/layout/pages/{pageId}` | Update a layout page | `force` (query) |
| **`DELETE`** | `/entities/{eid}/layout/pages/{pageId}` | Delete an empty layout page | `force` (query) |
| **`GET`** | `/entities/{eid}/layout/location` | Fetch the location of the entity in the parent page layout | None |
| **`PUT`** | `/entities/{eid}/layout/location` | Move the entity to a new location in the parent page layout | `force` (query) |
| **`GET`** | `/samples/{sampleId}/properties` | Fetch sample properties | `name` (query) |
| **`PATCH`** | `/samples/{sampleId}/properties` | Update sample properties | `name` (query) |
| **`GET`** | `/samples/{sampleId}/properties/{propertyId}` | Fetch sample properties by ID | `propertyId*` (path) |
| **`PATCH`** | `/samples/{sampleId}/properties/{propertyId}` | Update sample properties by ID | `propertyId*` (path) |
| **`PUT`** | `/samples/{sampleId}/status` | Update sample status | None |
| **`GET`** | `/sampleSummary/{sampleSummaryId}/samples` | Fetch samples from samples table/summary | None |
| **`GET`** | `/samplesTables/{samplesTableId}/rows` | Fetch rows from samples table/summary | None |
| **`PATCH`** | `/samplesTables/{samplesTableId}/rows` | Bulk update samples in samples table/summary | None |
| **`POST`** | `/samplesTables/{samplesTableId}/bulkUpdate` | Bulk update samples in samples table asynchronously | None |
| **`GET`** | `/samplesTables/{samplesTableId}/bulkUpdate/{jobId}` | Get the job status of bulk update samples in samples table | `jobId*` (path) |
| **`GET`** | `/samplesTables/{samplesTableId}/_column` | Fetch column definitions of samples table | None |
| **`PATCH`** | `/samplesTables/{samplesTableId}/_column` | Update column definition of samples table | None |
| **`POST`** | `/entities/search` | Search entities | None |
| **`POST`** | `/entities/search/tags` | Search entity tags | None |
| **`POST`** | `/entities/search/terms` | Search entity terms | None |
| **`GET`** | `/entities/templates/{eid}/fields` | Fetch template fields definition | None |
| **`POST`** | `/entities/{eid}/syncWithTemplate` | Synchronize the definition with template | `force` (query) |


## Chemical Fragments
| Method | Path | Summary / Description | Key Parameters |
| :--- | :--- | :--- | :--- |
| **`GET`** | `/fragments/salts` | Fetch Salts | None |
| **`POST`** | `/fragments/salts` | Create Salt | None |
| **`PUT`** | `/fragments/salts` | Replace all Salts | None |
| **`GET`** | `/fragments/solvates` | Fetch Solvates | None |
| **`POST`** | `/fragments/solvates` | Create Solvate | None |
| **`PUT`** | `/fragments/solvates` | Replace all Solvates | None |
| **`GET`** | `/fragments/salts/{id}` | Fetch Salt by id | None |
| **`PATCH`** | `/fragments/salts/{id}` | Update Salt by id | None |
| **`DELETE`** | `/fragments/salts/{id}` | Delete Salt by id | None |
| **`GET`** | `/fragments/solvates/{id}` | Fetch Solvate by id | None |
| **`PATCH`** | `/fragments/solvates/{id}` | Update Solvate by id | None |
| **`DELETE`** | `/fragments/solvates/{id}` | Delete Solvate by id | None |


## Hierarchical Data Tables
| Method | Path | Summary / Description | Key Parameters |
| :--- | :--- | :--- | :--- |
| **`GET`** | `/hierarchicalTables/{eid}` | Fetch all content of a Hierarchical Table | None |
| **`GET`** | `/hierarchicalTables/{eid}/tables/{tableId}` | Fetch all content of a Hierarchical Table Layer | None |
| **`POST`** | `/hierarchicalTables/{eid}/tables/{tableId}` | Add a new row to a Hierarchical Table Layer | None |
| **`PATCH`** | `/hierarchicalTables/{eid}/tables/{tableId}` | Bulk update content of a Hierarchical Table Layer | None |
| **`POST`** | `/hierarchicalTables/{eid}/tables/{tableId}/rows/search` | Fetch all rows of a Hierarchical Table Layer from specified parent rows | None |
| **`GET`** | `/hierarchicalTables/{eid}/tables/{tableId}/rows/{rowId}` | Fetch content of a specific row in a Hierarchical Table Layer | None |
| **`PATCH`** | `/hierarchicalTables/{eid}/tables/{tableId}/rows/{rowId}` | Update content of a specific row in a Hierarchical Table Layer | None |
| **`DELETE`** | `/hierarchicalTables/{eid}/tables/{tableId}/rows/{rowId}` | Delete specified row from hierarchical table | None |
| **`GET`** | `/hierarchicalTables/{eid}/header` | Fetch content of a Hierarchical Table header | None |
| **`PATCH`** | `/hierarchicalTables/{eid}/header` | Patch content of a Hierarchical Table header | None |
| **`GET`** | `/hierarchicalTables/{eid}/_columns` | Fetch column definitions of a Hierarchical Table | None |
| **`PATCH`** | `/hierarchicalTables/{eid}/_columns` | Update column definitions of a Hierarchical Table | None |


## Entity Audit Trail & History
| Method | Path | Summary / Description | Key Parameters |
| :--- | :--- | :--- | :--- |
| **`GET`** | `/history/proxy/*` | History Proxy | None |
| **`POST`** | `/history/search` | Search history | None |
| **`GET`** | `/history/revisions/{revisionId}/entities/{eid}` | Fetch entity by entity ID and revision ID in history | `revisionId*` (path) |
| **`POST`** | `/audit/search` | Search audit events | None |


## Containers & Storage Locations
| Method | Path | Summary / Description | Key Parameters |
| :--- | :--- | :--- | :--- |
| **`POST`** | `/inventory/locations` | Create a new location | None |
| **`GET`** | `/inventory/locations/{locationId}` | Get location by ID | None |
| **`PATCH`** | `/inventory/locations/{locationId}` | Update location | None |
| **`GET`** | `/inventory/locations/{locationId}/fields/{fieldId}/attachment` | Get attachment by field ID | None |
| **`PUT`** | `/inventory/locations/{locationId}/fields/{fieldId}/attachment` | Update attachment | None |
| **`DELETE`** | `/inventory/locations/{locationId}/fields/{fieldId}/attachment` | Delete attachment | None |
| **`GET`** | `/inventory/locations/{locationId}/sublocations` | Get child locations of the specified location | None |
| **`GET`** | `/inventory/types` | Get types of inventory | `entityType*` (query) |
| **`POST`** | `/inventory/containers` | Create a new container | None |
| **`POST`** | `/inventory/containers/bulk` | Create a group of containers | None |
| **`GET`** | `/inventory/containers/{containerId}` | Get container by ID | None |
| **`PATCH`** | `/inventory/containers/{containerId}` | Update container | None |
| **`POST`** | `/inventory/containers/{containerId}/status/{action}` | Update container status | None |
| **`POST`** | `/inventory/containers/bulkUpdateStatus/jobs` | Update the status of a group of containers | None |
| **`GET`** | `/inventory/containers/bulkUpdateStatus/jobs/{jobId}/status` | Get status of the bulk update containers job | None |
| **`GET`** | `/inventory/containers/bulkUpdateStatus/jobs/{jobId}/report` | Download the report of the bulk update containers job | None |
| **`POST`** | `/inventory/containers/bulkUpdate/jobs` | Update the field of a group of containers | None |
| **`GET`** | `/inventory/containers/bulkUpdate/jobs/{jobId}/status` | Get status of the bulk update field containers job | None |
| **`GET`** | `/inventory/containers/bulkUpdate/jobs/{jobId}/report` | Download the report of the bulk update field containers job | None |
| **`POST`** | `/inventory/containers/bulkReturnHome/jobs` | Return containers to Home Location | None |
| **`GET`** | `/inventory/containers/bulkReturnHome/jobs/{jobId}/status` | Get status of the bulk return containers to home location job | None |
| **`GET`** | `/inventory/containers/bulkReturnHome/jobs/{jobId}/report` | Download the report of the bulk return containers to home location job | None |
| **`POST`** | `/inventory/containers/status/{action}/bulk` | Bulk update containers status | None |
| **`POST`** | `/inventory/containers/search` | Search containers by barcodes | None |
| **`GET`** | `/inventory/containers/{containerId}/fields/{fieldId}/attachment` | Get attachment by field ID | None |
| **`PUT`** | `/inventory/containers/{containerId}/fields/{fieldId}/attachment` | Update attachment | None |
| **`DELETE`** | `/inventory/containers/{containerId}/fields/{fieldId}/attachment` | Delete attachment | None |
| **`PATCH`** | `/inventory/containers/{containerId}/amount` | Update amount of a container | None |
| **`POST`** | `/inventory/locations/jobs/movement` | Move location | None |
| **`GET`** | `/inventory/locations/jobs/movement/{jobId}` | Get job status | None |
| **`GET`** | `/inventory/locations/jobs/movement/{jobId}/report` | Get job status report | None |
| **`POST`** | `/inventory/locations/jobs/moveContents` | Transfer contents from one location to another | None |
| **`GET`** | `/inventory/locations/jobs/moveContents/{jobId}` | Get job status of moving contents | None |
| **`GET`** | `/inventory/locations/jobs/moveContents/{jobId}/report` | Get job status report of moving contents | None |
| **`GET`** | `/inventory/materialOrders/{orderId}` | Retrieve detailed order information | None |
| **`PATCH`** | `/inventory/materialOrders/{orderId}` | Update material order information | None |
| **`GET`** | `/inventory/suppliers` | Fetch suppliers | `sort*` (query), `search` (query), `name` (query), `country` (query) |
| **`POST`** | `/inventory/containers/bulkExport` | Export containers | None |
| **`GET`** | `/inventory/containers/bulkExport/jobs/{jobId}/status` | Get status of the containers bulk export job | None |
| **`GET`** | `/inventory/containers/bulkExport/jobs/{jobId}/report` | Download the report of the containers bulk export job | None |
| **`POST`** | `/inventory/materialOrders/exports` | Export material orders | None |
| **`GET`** | `/inventory/materialOrders/exports/{jobId}/status` | Get status of the material orders exports job | None |
| **`GET`** | `/inventory/materialOrders/exports/{jobId}/report` | Download the report of the material orders exports job | None |
| **`GET`** | `/inventory/suppliers/upload/example` | Get bulk upload suppliers csv file example | None |
| **`POST`** | `/inventory/suppliers/upload` | Bulk upload suppliers via CSV file | None |


## Materials & Inventory Reagents
| Method | Path | Summary / Description | Key Parameters |
| :--- | :--- | :--- | :--- |
| **`GET`** | `/materials/libraries` | Fetch all active material libraries | `name` (query) |
| **`GET`** | `/materials/{eid}` | Fetch material by entity ID | None |
| **`PATCH`** | `/materials/{eid}` | Update Fragments or Synonyms of a specified material | `digest` (query), `force` (query) |
| **`GET`** | `/materials/{eid}/properties` | Fetch properties of a specified material | None |
| **`PATCH`** | `/materials/{eid}/properties` | Update properties of a specified material | `digest` (query), `force` (query) |
| **`GET`** | `/materials/{eid}/drawing` | Export chemical drawing of a chemical material | `format` (query) |
| **`PATCH`** | `/materials/{eid}/drawing` | Patch chemical structure to a chemical material | `filename` (header), `chemicalName` (query) |
| **`GET`** | `/materials/{eid}/image` | Export display image of a non-chemical/non-bio material | None |
| **`PATCH`** | `/materials/{eid}/image` | Patch image to a non-chemical/non-bio material | None |
| **`DELETE`** | `/materials/{eid}/image` | Delete image from a non-chemical/non-bio material | None |
| **`GET`** | `/materials/{eid}/bioSequence` | Export biological sequence file of a bio-material | `format` (query) |
| **`GET`** | `/materials/{eid}/attachments/{fieldId}` | Export an attachment for a specified field of the specific material | None |
| **`PUT`** | `/materials/{eid}/attachments/{fieldId}` | Upload an attachment for a specified field of the specific material | `digest` (query), `force` (query) |
| **`DELETE`** | `/materials/{eid}/attachments/{fieldId}` | Delete an attachment for a specified field of the specific material | `digest` (query), `force` (query) |
| **`GET`** | `/materials/{eid}/report` | Get report of a specified material | None |
| **`POST`** | `/materials/{eid}/transfer` | Transfer batch to another asset | None |
| **`POST`** | `/materials/{eid}/updateFromPubChem` | Update data from PubChem | `force` (query) |
| **`POST`** | `/materials/{libraryName}/assets` | Create a new asset with batch | None |
| **`GET`** | `/materials/{libraryName}/bulkImport/example` | Get bulk Import materials zip file example | None |
| **`POST`** | `/materials/{libraryName}/bulkImport` | Bulk import materials | `rule` (query), `importType` (query), `processInAnyOrder` (query), `reportFormat` (query) |
| **`GET`** | `/materials/bulkImport/jobs/{jobId}` | Get status of bulk import job | `jobId*` (path) |
| **`DELETE`** | `/materials/bulkImport/jobs/{jobId}` | Delete the report of the specified job | `jobId*` (path) |
| **`GET`** | `/materials/bulkImport/jobs/{jobId}/failures` | Download failed report by job ID | `jobId*` (path), `filename` (query) |
| **`GET`** | `/materials/bulkImport/jobs/{jobId}/report` | Download the report file of the bulk import | `jobId*` (path), `filename` (query) |
| **`POST`** | `/materials/{libraryName}/assets/uniquenessCheck` | Check whether the asset exists in the material library according to the uniqueness rule | None |
| **`GET`** | `/materials/{libraryName}/assets/{id}/batches` | Fetch batches of a specified asset | None |
| **`POST`** | `/materials/{libraryName}/assets/{id}/batches` | Create a new batch for specified asset | None |
| **`GET`** | `/materials/{libraryName}/assets/id/{id}` | Fetch asset from a material library by material ID | None |
| **`GET`** | `/materials/{libraryName}/batches/id/{id}` | Fetch batch from a material library by material ID | None |
| **`POST`** | `/materials/{libraryName}/bulkExport` | Export materials of specified material library | `fileType` (query), `chemFormat` (query), `limit` (query), `startAfter` (query) |
| **`GET`** | `/materials/bulkExport/download/{fileId}` | Download bulk exported file | `fileId*` (path) |
| **`GET`** | `/materials/bulkExport/reports/{reportId}` | Check export status with export report | `reportId*` (path) |
| **`GET`** | `/materialsTable/{materialsTableId}` | Fetch all materials from materials table | `materialsTableId*` (path) |
| **`POST`** | `/materialsTable/{materialsTableId}` | Add material to materials table | `materialsTableId*` (path), `digest` (query), `force` (query) |
| **`PATCH`** | `/materialsTable/{materialsTableId}` | Bulk update content of materials table | `materialsTableId*` (path), `digest` (query), `force` (query) |
| **`GET`** | `/materialsTable/{materialsTableId}/{rowId}` | Get specified materials table row | `materialsTableId*` (path), `rowId*` (path) |
| **`PATCH`** | `/materialsTable/{materialsTableId}/{rowId}` | Update specified materials table row | `materialsTableId*` (path), `rowId*` (path), `digest` (query), `force` (query) |
| **`DELETE`** | `/materialsTable/{materialsTableId}/{rowId}` | Delete specified materials table row | `materialsTableId*` (path), `rowId*` (path), `digest` (query), `force` (query) |
| **`POST`** | `/materialsTable/{materialsTableId}/{rowId}/register` | Register a material using data from the specified row in the materials table | None |
| **`GET`** | `/materialsTable/{materialsTableId}/_column` | Fetch column definitions of materials table | None |
| **`PATCH`** | `/materialsTable/{materialsTableId}/_column` | Update column definition of materials table | `force` (query) |
| **`GET`** | `/materials/{libraryName}/bulkUpdate/example` | Get example ZIP file for bulk update materials | None |
| **`POST`** | `/materials/{libraryName}/bulkUpdate` | Bulk update materials | `applyNullValue` (query) |
| **`GET`** | `/materials/bulkUpdate/jobs/{jobId}` | Get report of bulk update job | `jobId*` (path) |
| **`DELETE`** | `/materials/bulkUpdate/jobs/{jobId}` | Delete the report of the specified job | `jobId*` (path) |
| **`GET`** | `/materials/bulkUpdate/jobs/{jobId}/failures` | Download failed report by job ID | `jobId*` (path) |


## Biopolymers & Monomers
| Method | Path | Summary / Description | Key Parameters |
| :--- | :--- | :--- | :--- |
| **`GET`** | `/monomers/libraries` | Fetch all active monomer libraries | None |
| **`GET`** | `/monomers/libraries/{libraryEid}/export` | Export monomers in specific library | None |
| **`POST`** | `/monomers/libraries/{libraryEid}/bulkImport` | Bulk import monomers | `treatAsNewVersion` (query), `treatAsNewMonomer` (query), `filename` (query) |
| **`GET`** | `/monomers/libraries/{libraryEid}/bulkImport/example` | Obtain an example for importing monomers in batches | None |
| **`GET`** | `/monomers/libraries/{libraryEid}/bulkImport/jobs/{jobId}` | Get report of monomer bulk import job | None |
| **`GET`** | `/monomers/libraries/{libraryEid}/bulkImport/jobs/{jobId}/failures` | Download the failures report of bulk import job | None |
| **`GET`** | `/monomers/{monomerId}` | Fetch monomer by ID | None |
| **`POST`** | `/monomers/{monomerId}/deprecate` | Deprecate specified monomer | None |
| **`POST`** | `/monomers/{monomerId}/restore` | Restore specified monomer | None |


## External Actions & Webhooks
| Method | Path | Summary / Description | Key Parameters |
| :--- | :--- | :--- | :--- |
| **`GET`** | `/notifications` | Fetch all notifications | None |
| **`GET`** | `/notifications/{id}` | Get notification by notification-id | None |
| **`PATCH`** | `/notifications/{id}` | Mark notifications as read or dismiss by notification-id' | None |


## Parallel Experiments (DOE)
| Method | Path | Summary / Description | Key Parameters |
| :--- | :--- | :--- | :--- |
| **`POST`** | `/paraexp/{eid}/reset` | Reset and delete all subexperiments of a paraexperiment | None |
| **`GET`** | `/paraexp/{eid}/reset/{jobId}` | Get the status of paraexperiment resetting job | `jobId*` (path) |
| **`GET`** | `/enumerator/{eid}` | Get content of an enumerator | None |
| **`POST`** | `/enumerator/{eid}/addCompound` | Add compound to an enumerator | None |
| **`POST`** | `/enumerator/{eid}/refreshGroups` | Refresh groups of an enumerator | None |
| **`POST`** | `/enumerator/{eid}/enumerate` | Enumerate to generate subexperiments | None |
| **`GET`** | `/enumerator/{eid}/enumerate/{jobId}` | Get the status of enumerating job | `jobId*` (path) |
| **`POST`** | `/extenumerator/{eid}/upload` | Upload csv, sdf, or rdf to an external enumerator | `X-Filename` (header) |
| **`GET`** | `/extenumerator/mapping/template` | Get mapping template for patching to external enumerator | None |
| **`PATCH`** | `/extenumerator/{eid}/mapping` | Patch mapping to an external enumerator | None |
| **`GET`** | `/extenumerator/{eid}` | Get content of an external enumerator | None |
| **`POST`** | `/extenumerator/{eid}/enumerate` | External Enumerate to generate subexperiments | None |
| **`GET`** | `/extenumerator/{eid}/enumerate/{jobId}` | Get the status of external enumerating job | `jobId*` (path) |
| **`GET`** | `/subexpSummary/{subexpSummaryId}/rows` | Fetch content of subexperiment summary table | None |
| **`PATCH`** | `/subexpSummary/{subexpSummaryId}/bulkUpdate` | Bulk update subexperiment summary table | None |
| **`GET`** | `/subexpSummary/{subexpSummaryId}/bulkUpdate/{bulkUpdateId}` | Get the status of bulk update | `bulkUpdateId*` (path) |
| **`POST`** | `/subexpSummary/{subexpSummaryId}/samples/bulkCreate` | Bulk create samples for product(s) in a parallel experiment summary table | `sampleCount*` (query) |
| **`GET`** | `/subexpSummary/{subexpSummaryId}/samples/bulkCreate/{jobId}` | Get the status of bulk create | `jobId*` (path) |
| **`GET`** | `/subexpLayout/{layoutId}` | Fetch subexperiment layout | None |
| **`PATCH`** | `/subexpLayout/{layoutId}` | Update subexperiment layout | None |
| **`PATCH`** | `/subexpLayout/{layoutId}/reset` | Reset/autoFill subexperiment layout asynchronously | None |
| **`GET`** | `/subexpLayout/{layoutId}/reset/{jobId}` | Get the job status of subexperiment layout resetting | `jobId*` (path) |


## Well Plates & High-Throughput Screening
| Method | Path | Summary / Description | Key Parameters |
| :--- | :--- | :--- | :--- |
| **`POST`** | `/plates` | Create a new plate container | `digest` (query), `force` (query) |
| **`GET`** | `/plates/{plateContainerId}` | Fetch plate container by ID | None |
| **`GET`** | `/plates/{plateContainerId}/plates` | Retrieve all plates from a specified container | None |
| **`POST`** | `/plates/{plateContainerId}/plates` | Create a new plate in a specified container | `force` (query) |
| **`GET`** | `/plates/{plateContainerId}/plates/{id}` | Retrieve data of an existing plate | None |
| **`PATCH`** | `/plates/{plateContainerId}/plates/{id}` | Update an existing plate | None |
| **`PUT`** | `/plates/{plateContainerId}/plates/{id}` | Replace an existing plate | None |
| **`DELETE`** | `/plates/{plateContainerId}/plates/{id}` | Remove an existing plate | `force` (query) |
| **`GET`** | `/plates/{plateContainerId}/settings/annotationLayers` | Get annotation layers of a specified container | None |
| **`POST`** | `/plates/{plateContainerId}/settings/annotationLayers` | Add a new annotation layer to a specified container | `force` (query) |
| **`GET`** | `/plates/{plateContainerId}/settings/annotationLayers/{annotationLayerId}` | Get annotation layer by ID | None |
| **`PATCH`** | `/plates/{plateContainerId}/settings/annotationLayers/{annotationLayerId}` | Update an existing annotation layer | None |
| **`DELETE`** | `/plates/{plateContainerId}/settings/annotationLayers/{annotationLayerId}` | Delete an existing annotation layer | `force` (query) |
| **`GET`** | `/plates/{plateContainerId}/summary` | Retrieve the summary table of an existing plate container | None |


## SCIM Identity Management
| Method | Path | Summary / Description | Key Parameters |
| :--- | :--- | :--- | :--- |
| **`GET`** | `/scim/v2/ServiceProviderConfig` | Fetch SCIM ServiceProviderConfig | None |
| **`GET`** | `/scim/v2/ResourceTypes` | Fetch SCIM ResourceTypes | None |
| **`GET`** | `/scim/v2/ResourceTypes/{resourceTypeId}` | Fetch SCIM ResourceType by id | None |
| **`GET`** | `/scim/v2/Schemas` | Fetch SCIM Schemas | None |
| **`GET`** | `/scim/v2/Schemas/{id}` | Fetch SCIM Schemas by id | None |
| **`GET`** | `/scim/v2/Users` | Search SCIM user | None |
| **`POST`** | `/scim/v2/Users` | Create SCIM user | None |
| **`GET`** | `/scim/v2/Users/{id}` | Fetch SCIM user by id | None |
| **`PATCH`** | `/scim/v2/Users/{id}` | Update SCIM user by id | None |
| **`PUT`** | `/scim/v2/Users/{id}` | Update SCIM user by id | None |
| **`DELETE`** | `/scim/v2/Users/{id}` | Delete SCIM user by id | None |
| **`GET`** | `/scim/v2/Groups` | Search SCIM group | None |
| **`POST`** | `/scim/v2/Groups` | Create SCIM group | None |
| **`GET`** | `/scim/v2/Groups/{id}` | Fetch SCIM group by id | None |
| **`PATCH`** | `/scim/v2/Groups/{id}` | Update SCIM group by id | None |
| **`PUT`** | `/scim/v2/Groups/{id}` | Update SCIM group by id | None |
| **`DELETE`** | `/scim/v2/Groups/{id}` | Delete SCIM group by id | None |
| **`POST`** | `/scim/v2/Bulk` | SCIM Bulk Operation | None |


## Stoichiometry & Reaction Tables
| Method | Path | Summary / Description | Key Parameters |
| :--- | :--- | :--- | :--- |
| **`GET`** | `/stoichiometry/{eid}` | Fetch stoichiometry data of experiment or chemicalDrawing | `fields[stoichiometry]` (query), `includeStrippedData` (query) |
| **`GET`** | `/stoichiometry/{eid}/{rowid}` | Fetch one specified row of stoichiometry data grid by id | `rowid*` (path), `includeStrippedData` (query) |
| **`PATCH`** | `/stoichiometry/{eid}/{rowid}` | Update row value of stoichiometry grid | `rowid*` (path), `syncUpdateToSample` (query) |
| **`DELETE`** | `/stoichiometry/{eid}/{rowid}` | Delete a custom row from stoichiometry grid | `rowid*` (path) |
| **`GET`** | `/stoichiometry/{eid}/{rowid}/structure` | Fetch structure of reactants/products | `rowid*` (path), `format` (query) |
| **`GET`** | `/stoichiometry/{eid}/reactants` | Fetch all reactants | None |
| **`POST`** | `/stoichiometry/{eid}/reactants` | Add a new custom reactant | None |
| **`GET`** | `/stoichiometry/{eid}/products` | Fetch all products | None |
| **`POST`** | `/stoichiometry/{eid}/products` | Add a new custom product | None |
| **`GET`** | `/stoichiometry/{eid}/solvents` | Fetch all solvents | None |
| **`POST`** | `/stoichiometry/{eid}/solvents` | Add a new solvent | None |
| **`GET`** | `/stoichiometry/{eid}/conditions` | Fetch all conditions | None |
| **`POST`** | `/stoichiometry/{eid}/conditions` | Add a new condition | None |
| **`GET`** | `/stoichiometry/{eid}/columns/{grid}` | Fetch column definitions of stoichiometry grid | `grid*` (path) |
| **`PATCH`** | `/stoichiometry/{eid}/columns/{grid}` | Update column definitions of stoichiometry grid | `grid*` (path) |
| **`GET`** | `/chemicaldrawings/{eid}/reaction/{position}` | Fetch structure parts of current reaction | `position*` (path) |
| **`POST`** | `/chemicaldrawings/{eid}/reaction/{position}` | Append structure to current reaction | `position*` (path) |
| **`GET`** | `/chemicaldrawings/{eid}/reaction` | Fetch reaction | None |
| **`PUT`** | `/chemicaldrawings/{eid}/reaction` | Update reaction | `syncUpdateToSample` (query) |


## Equipment & Instrument Synergy
| Method | Path | Summary / Description | Key Parameters |
| :--- | :--- | :--- | :--- |
| **`GET`** | `/synergy/dataExchange/{dataExchangeEid}/files` | List downloadable Data Exchange files | `dataExchangeEid*` (path) |
| **`GET`** | `/synergy/dataExchange/{dataExchangeEid}/report` | Download the Data Exchange report file | `dataExchangeEid*` (path) |
| **`GET`** | `/synergy/dataExchange/{dataExchangeEid}/resultTable/{tableName}` | Download a Data Exchange result table file by table name | `dataExchangeEid*` (path), `tableName*` (path) |
| **`GET`** | `/synergy/cros` | Fetch all Contract Research Organizations | None |
| **`GET`** | `/synergy/cros/{croId}` | Fetch Contract Research Organizations by ID | None |
| **`GET`** | `/synergy/cros/{croId}/departments` | Fetch all departments of a CRO | None |
| **`GET`** | `/synergy/departments/{departmentId}` | Fetch department by ID | None |
| **`GET`** | `/synergy/collaborations/{collaborationId}/departments` | Fetch all departments assigned to a Collaboration | None |
| **`GET`** | `/synergy/cros/{croId}/users/{userId}` | Fetch CRO user by id | None |
| **`GET`** | `/synergy/cros/{croId}/users` | Fetch all users of a CRO | `enabled` (query) |
| **`POST`** | `/synergy/cros/{croId}/users` | Create CRO user | None |
| **`GET`** | `/synergy/cros/{croId}/admins` | Fetch all admins of a CRO | `enabled` (query) |
| **`GET`** | `/synergy/departments/{departmentId}/members` | Fetch all members of a department | None |
| **`GET`** | `/synergy/departments/{departmentId}/managers` | Fetch all managers of a department | None |
| **`GET`** | `/synergy/users/{userId}/cro` | Fetch CRO associated with user by ID | None |
| **`GET`** | `/synergy/workTypes` | Fetch all work types | None |
| **`GET`** | `/synergy/collaborations` | List Collaborations | None |
| **`GET`** | `/synergy/collaborations/{collaborationEid}` | Fetch collaboration by collaboration eid | None |
| **`POST`** | `/synergy/workOrders` | Create a new work order | None |
| **`GET`** | `/synergy/workOrders/{workOrderId}` | Fetch work order by ID | None |
| **`PUT`** | `/synergy/workOrders/{workOrderId}/status` | Update work order status | None |
| **`GET`** | `/synergy/designTables/{designTableId}/rows` | Fetch design table rows | None |
| **`PATCH`** | `/synergy/designTables/{designTableId}/rows` | Update content of design table rows | None |
| **`GET`** | `/synergy/designTables/{designTableId}/columnDefinition` | Fetch design table column definition | None |
| **`GET`** | `/synergy/designs/{designId}` | Fetch design by ID | None |
| **`PATCH`** | `/synergy/designs/{designId}` | Update design by ID | None |
| **`PUT`** | `/synergy/designs/{designId}/drawing` | Update chemical structure of design | None |
| **`GET`** | `/synergy/designTables/{designTableId}/design/bulkImport` | Get status of design bulk import | None |
| **`POST`** | `/synergy/designTables/{designTableId}/design/bulkImport` | Bulk import designs | `filename*` (query), `rule*` (query), `reportFormat*` (query) |
| **`GET`** | `/synergy/designTables/design/bulkImport/reportFile/{fileId}` | Download report file by file id | `fileId*` (path) |
| **`GET`** | `/synergy/referenceTables/{referenceTableId}/rows` | Fetch rows of reference table | None |
| **`PATCH`** | `/synergy/referenceTables/{referenceTableId}/rows` | Add or delete reference to a Reference Table | None |
| **`GET`** | `/synergy/referenceTables/{referenceTableId}/columnDefinition` | Fetch column definition of reference table | None |
| **`PUT`** | `/synergy/referenceTables/{referenceTableId}/columnDefinition` | Update column definition of reference table | None |
| **`GET`** | `/synergy/config/referenceTable` | Fetch system configuration of reference table | None |
| **`POST`** | `/synergy/cros/{croId}/bulkUpdateUsers` | Bulk update CRO users | None |
| **`GET`** | `/synergy/cros/{croId}/bulkUpdateUsersStatus` | Bulk update CRO users status | None |
| **`POST`** | `/synergy/cros/{croId}/users/{userId}/deactivate` | Deactivate a CRO user | None |
| **`POST`** | `/synergy/cros/{croId}/users/{userId}/reactivate` | Reactivate a CRO user | None |
| **`PUT`** | `/synergy/synergyExperiment/{synergyExperimentId}/status` | Update synergyExperiment status | None |


## System & Health
| Method | Path | Summary / Description | Key Parameters |
| :--- | :--- | :--- | :--- |
| **`GET`** | `/version` | Retrieve the current Signals release version | None |
| **`GET`** | `/securityPolicy/export` | Retrieve tenant security policies | None |
| **`DELETE`** | `/bearerTokens/{domain}` | Revoke all bearer tokens | `domain*` (path) |
| **`DELETE`** | `/bearerTokens/{domain}/user/{email}` | Revoke bearer tokens for a user | `domain*` (path), `email*` (path), `authId` (query) |


## Async Background Tasks
| Method | Path | Summary / Description | Key Parameters |
| :--- | :--- | :--- | :--- |
| **`GET`** | `/tasks/{taskId}/properties` | Fetch task properties | `name` (query) |
| **`PATCH`** | `/tasks/{taskId}/properties` | Update task properties | `name` (query) |
| **`GET`** | `/tasks/{taskId}/properties/{propertyId}` | Fetch task properties by ID | `propertyId*` (path) |
| **`PATCH`** | `/tasks/{taskId}/properties/{propertyId}` | Update task properties by ID | `propertyId*` (path) |
| **`GET`** | `/tasks/todo/{todoListId}/rows` | Fetch tasks from tasks todo list | None |
| **`PATCH`** | `/tasks/todo/{todoListId}/rows` | Update tasks in tasks todo list | None |
| **`GET`** | `/tasks/todo/{todoListId}/_column` | Fetch column definitions of tasks todo list | None |
| **`PATCH`** | `/tasks/todo/{todoListId}/_column` | Update column definition of tasks todo list | None |
| **`GET`** | `/tasks/tasksTable/{tasksTableId}/rows` | Fetch tasks from tasks table | None |
| **`PATCH`** | `/tasks/tasksTable/{tasksTableId}/rows` | Update tasks in tasks table | None |
| **`GET`** | `/tasks/tasksTable/{tasksTableId}/_column` | Fetch column definitions of tasks table | None |
| **`PATCH`** | `/tasks/tasksTable/{tasksTableId}/_column` | Update column definition of tasks table | None |


## Users & Groups
| Method | Path | Summary / Description | Key Parameters |
| :--- | :--- | :--- | :--- |
| **`GET`** | `/users` | List users | `q` (query), `enabled` (query), `userType` (query), `cro` (query) |
| **`POST`** | `/users` | Create user | None |
| **`GET`** | `/users/{userId}` | Fetch user by id | None |
| **`PATCH`** | `/users/{userId}` | Update user | None |
| **`DELETE`** | `/users/{userId}` | Disable user by id | `assignResourceTo` (query) |
| **`GET`** | `/users/{userId}/picture` | Fetch user picture | None |
| **`GET`** | `/users/{userId}/systemGroups` | Fetch user system groups | None |
| **`PATCH`** | `/users/{userId}/reactivate` | reactivate user by id | None |
| **`GET`** | `/users/licenses` | Fetch available users licenses | None |
| **`GET`** | `/groups` | List user groups | None |
| **`POST`** | `/groups` | Create user group | None |
| **`GET`** | `/groups/{groupId}` | Fetch user group by id | None |
| **`PATCH`** | `/groups/{groupId}` | Update user group | `digest` (query), `force` (query) |
| **`DELETE`** | `/groups/{groupId}` | Delete user group by id | None |
| **`GET`** | `/groups/{groupId}/members` | Fetch user group members | None |
| **`POST`** | `/groups/{groupId}/members` | Add user to user group | `digest` (query), `force` (query) |
| **`DELETE`** | `/groups/{groupId}/members/{userId}` | Delete user from user group | None |
| **`GET`** | `/groups/{groupId}/shares` | Fetch user group shares | None |
| **`POST`** | `/groups/{groupId}/shares` | Create a share to user group | None |
| **`PATCH`** | `/groups/{groupId}/shares/{sid}` | Update user group share | None |
| **`DELETE`** | `/groups/{groupId}/shares/{sid}` | Delete a share from group | None |
| **`GET`** | `/groups/{groupId}/associations` | Fetch group associations | None |
| **`POST`** | `/groups/{groupId}/associations` | Create association to user group | None |
| **`PATCH`** | `/groups/{groupId}/associations` | Update user group associations | None |
| **`GET`** | `/roles` | List Roles | None |
| **`GET`** | `/roles/{roleId}` | Fetch role by id | None |
| **`GET`** | `/profiles/me` | Get profile of current user | None |

