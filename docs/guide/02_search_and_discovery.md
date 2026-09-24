<!-- 
Signals EMEA Hackathon 2026 Reference Guide (Distilled Markdown)
Architecture Notice: Use FastAPI (backend) & Streamlit (UI). Do NOT copy legacy Flask patterns.
-->


# Search

The `POST /entities/search` endpoint is how you find and pull the exact data you need out of Signals — from a single experiment to a full nightly extract. This page takes you from your first query to production-grade extraction and sync.

1A first search
2What decides every query
3Fields and tags
4Operators
5Filtering on metadata
6Following relationships
7Full-text Search
8Chemistry search
9Sorting & paging
10Extract & sync
11Recipes
12Practical notes

## 1 · A first search

A search is a `POST` whose body contains a `query`. That's the only required part. Send this to find the 20 most recently modified experiments:

```python
POST https://<your-tenant>/api/rest/v1.0/entities/search?page[limit]=20
x-api-key: <your key>
Content-Type: application/vnd.api+json

{
  "query": {
    "$and": [
      { "$match": { "field": "type", "value": "experiment", "mode": "keyword" } },
      { "$match": { "field": "isTemplate", "value": false } }
    ]
  },
  "options": { "sort": { "modifiedAt": "desc" } }
}
```

The response is standard JSON:API, with a `meta` block describing the search itself:

```python
{
  "meta": { "total": 123, "count": 20, "took-ms": 11, "query-reached-limit": false },
  "links": { "self": "…", "next": "…" },
  "data": [ { "type": "entity", "id": "experiment:…", "attributes": { … } } ]
}
```

`meta.total` is the full number of matches; `meta.count` is how many are on this page. Drive your paging from `total`.

About the examples on this page Field keys, values, and counts in the examples that follow come from one tenant and are there to show the shape of a request and its response. Substitute your own — §3 explains how to discover the keys your tenant actually uses.
Using curl? The `[` and `]` in `page[limit]` are wildcard characters to curl. Add `-g` (`--globoff`) or the request quietly returns nothing.

## 2 · What decides every query

Two choices determine the structure of almost every search:

* The field you test. Every condition names a `field`. Fields come in two kinds — plain system fields and namespaced tag fields — covered next.

* The `source` you search. Entities live in separate indexes. The default index holds notebook content; inventory, archive, and chemical drawings each have their own. Choosing the wrong one is the most common reason a correct-looking query returns nothing (see §12).

A query itself is a tree of operators: leaf operators such as `$match` test one field; `$and`, `$or`, and `$not` combine them; and `$child` / `$parent` run a sub-query against an entity's relatives. You nest these to any depth.

## 3 · Fields and tags

This is the concept everything else builds on. Every `field` you name is one of two kinds.

### System fields

Top-level properties, named plainly with no extra qualifiers:

| Field | Meaning |

| type | Entity type — `experiment`, `sample`, `materialsTable`, `grid`, `container`, … Use `mode:"keyword"`. |

| isTemplate | Whether the entity is a template. Most content queries set this to `false`. |

| state | Workflow state, e.g. `open` or `closed`. |

| name, description | Entity name and description. |

| createdAt, modifiedAt | Timestamps. Compare with `$gt`/`$lt`/`$range` and `as:"date"`. |

| createdBy, editedBy, owner | User ids (integers). |

| eid | The exact entity id — to pinpoint one entity. |

| _parent_eid, _parent_type | The direct parent's id / type, without a relationship traversal. |

### Tag fields

Custom columns and metadata live in a separate tags index. You address them by a namespaced key and add `"in":"tags"` plus an `"as"` type that tells the index how to read the value. You don't have to guess these keys — a search result already lists them. Every key in a result's `attributes.tags` is directly queryable:

```python
// attributes.tags from a materialsTable result — each key is a field you can search
{
  "materials.Chemical Name":   ["GAM-001 (lead)"],
  "materials.Molecular Weight": [275.32],
  "materials.ID":              ["0006"],
  "system.Keywords":           "Niloc Fyffe"
}
```

The namespace prefix tells you which family of fields a key belongs to:

| Prefix | Applies to | Example key |

| fields. | Experiment / request / work-order header fields | fields.Status |

| system. | System metadata on many entity types | system.Origin Template |

| grid. | Admin-defined table columns | grid.Sample Description |

| materials. | Materials-table columns | materials.Chemical Name |

| variationsGrid. | Variations-table columns | variationsGrid.Sample Data |

| monomer. | Monomer library columns | monomer.Symbol |

The workflow To filter on any custom field, first run a broad query for one entity of that type, read its `attributes.tags`, and copy the key you want. This always reflects your tenant's real schema.

## 4 · Operators

You'll build most queries from a handful of these; the rest are here when you need them.

| Operator | Shape | Purpose |

| $match | {field, value, mode?, in?, as?} | Match one value. `mode:"keyword"` = exact. |

| $in | {field, values[]} | Field matches any value in the list. |

| $exists | {field, in?, as?} | Field is present / non-empty. |

| $prefix | {field, value} | Starts-with match (case-sensitive against tokenized index; supply lowercase value like `"del"`, `"exp"`). |

| $gt $lt $gte $lte | {field, value, as?} | Numeric / date comparison. |

| $range | {field, from, to, as?} | Between two bounds, inclusive. |

| $intersect | {field, values[], minimum} | Match at least `minimum` of the values. |

| $and $or $not | [ …operators ] | Combine conditions. `$not` takes an array. |

| $child $parent | { …operator } | Test an entity's children / parents (§6). |

| $simple | {query, ?} | Full-text search across indexed fields (§7). |

| $chemsearch | {molecule, mime, options?} | Structure / substructure search (§8). |

## 5 · Filtering on metadata

To filter on a tag field, name its key, add `in:"tags"`, and give the `as` type. For an exact text match, add `mode:"keyword"`:

```python
{ "query": { "$and": [
    { "$match": { "field": "type", "value": "materialsTable", "mode": "keyword" } },
    { "$match": { "field": "materials.Chemical Name", "in": "tags", "as": "text",
                 "value": "GAM-001 (lead)", "mode": "keyword" } }
] } }
```

The `as` type matches the column's data type:

| as | Use for |

| text | Text columns (pair with `mode:"keyword"` for exact match). |

| date | Date columns and `createdAt`/`modifiedAt` (ISO-8601 value). |

| integer | Whole-number columns. |

| double | Decimal numeric columns — use this for numeric `$gt`/`$lt`/`$range` on tag fields. |

| boolean | True/false columns. |

For a numeric comparison on a decimal column, use `as:"double"`:

```python
{ "$gt": { "field": "materials.Molecular Weight", "in": "tags", "as": "double", "value": 200 } }
```

## 6 · Following relationships

Find entities by their relatives. The sub-query inside `$child` or `$parent` runs against the child (or parent); the results are always the outer entity.

#### Experiments that contain a materials table

```python
{ "query": { "$and": [
    { "$match": { "field": "type", "value": "experiment", "mode": "keyword" } },
    { "$child": { "$match": { "field": "type", "value": "materialsTable", "mode": "keyword" } } }
] } }
```

#### Samples whose parent is an experiment

```python
{ "query": { "$and": [
    { "$match":  { "field": "type", "value": "sample", "mode": "keyword" } },
    { "$parent": { "$match": { "field": "type", "value": "experiment", "mode": "keyword" } } }
] } }
```

When you already know the single parent, the `_parent_eid` system field is cheaper than a `$parent` sub-query.

## 7 · Full-text Search search

`$simple` does keyword full-text; append `*` for a prefix wildcard. Add `in:"tags"` to search the tag index instead of default fields.

```python
{ "$simple": { "query": "benzocaine", "operator": "and" } }   // all terms must match
{ "$simple": { "query": "benzo*",      "operator": "and" } }   // prefix wildcard
```

## 8 · Chemistry search

Match by chemical structure with `$chemsearch`, typically nested in a `$child` to find drawings inside experiments. `options:"full=true"` requires an exact match; omit it for substructure.

```python
{ "query": { "$and": [
    { "$match": { "field": "type", "value": "experiment", "mode": "keyword" } },
    { "$child": { "$chemsearch": {
        "molecule": "C1=CC=CC=C1",
        "mime": "chemical/x-daylight-smiles",
        "options": "full=true"
        } } }
] } }
```

## 9 · Sorting and paging

Paging and sorting can go in the request body's `options` object or as query parameters:

| Body option | Query parameter | Notes |

| options.offset | page[offset] | Skip N results (0–5000). |

| options.limit | page[limit] | Page size (1–100, default 20). |

| options.sort | sort=name,-modifiedAt | Object/array in the body; comma list (`-` = descending) as a param. |

| options.stop-after-items | stopAfterItems | Per-shard scan budget — see below. |

Sort a tag field with the array form, giving each key its `in`/`as`/`order`:

```python
"options": { "sort": [
    { "monomer.Symbol":  { "in": "tags", "as": "text",    "order": "desc" } },
    { "monomer.Version": { "in": "tags", "as": "integer", "order": "desc" } }
] }
```

stop-after-items is a scan budget, not a result count
    The index is sharded, and `stop-after-items` applies per shard — on a ten-shard deployment, `1000000` lets the engine examine up to ten million rows. It caps how hard the query scans, not how much comes back. Separately, paging stops at 5,000 (`page[offset]` max). A large `stop-after-items` just does more work; if `meta.query-reached-limit` is `true`, narrow the query rather than raising the cap. To pull more than 5,000 rows, use the pattern in §10.

## 10 · Extracting everything and keeping it in sync

Search is built to find and filter, not to dump millions of rows. To seed an external database and keep it current, use this pattern rather than a giant `stop-after-items`.

### Walk large sets by an immutable key

Because paging stops at 5,000, retrieve everything with keyset pagination on a field that never changes while you read — `createdAt` or `eid`. Ask for "the next page after the last value I saw," feeding that value back each time, instead of a growing offset:

```python
// Walk ALL experiments in createdAt order, 100 at a time. Feed the last
// createdAt back in as the new lower bound until a page comes back empty.
{
  "query": { "$and": [
    { "$match": { "field": "type", "value": "experiment", "mode": "keyword" } },
    { "$gt":    { "field": "createdAt", "as": "date", "value": "1970-01-01T00:00:00.000Z" } }
  ] },
  "options": { "limit": 100, "sort": { "createdAt": "asc" } }
}
```

Sort on a mutable field like `modifiedAt` or `state` and rows shift between pages as data is edited, causing skips and duplicates — so partition and cursor on immutable fields only.

### Seed once, then sync deltas

* Seed your database with the full keyset walk above; store each entity's `eid` and `digest`.

* Record a watermark — the time the seed finished.

* Sync on a schedule: fetch only what changed since the watermark and upsert by `eid`. Here `modifiedAt` is the right filter, because now you want what moved:

```python
{
  "query": { "$gt": { "field": "modifiedAt", "as": "date", "value": "2026-07-16T00:00:00.000Z" } },
  "options": { "limit": 100, "sort": { "modifiedAt": "asc" } }
}
```

A purpose-built alternative is `GET /entities?includeOptions=nontemplate&start=<timestamp>`. Its notion of "modified" cascades from children and inherited sharing — so a notebook appears in the results when one of its experiments changes, letting a single query catch nested edits.

Delta reliability Re-query from a few minutes before the last watermark; because upserting by `eid` is idempotent, the overlap carries no cost. Advance the watermark only after the batch commits, and compare `digest` values to skip no-op writes. Pair this with External Notifications for real-time triggers, using polling as the reliable backstop.

## 11 · Recipes

Copy-ready bodies for common questions. Substitute your own field names and values — read a result's `attributes.tags` (§3) to find the keys for your tenant.

#### Open experiments owned by specific people

```python
{ "query": { "$and": [
    { "$match": { "field": "type",  "value": "experiment", "mode": "keyword" } },
    { "$match": { "field": "state", "value": "open", "mode": "keyword" } },
    { "$in":    { "field": "owner", "values": [100, 121] } }
] } }
```

#### Experiments created since a date

```python
{ "query": { "$and": [
    { "$match": { "field": "type", "value": "experiment", "mode": "keyword" } },
    { "$gt": { "field": "createdAt", "as": "date", "value": "2025-01-01T00:00:00.000Z" } }
] } }
```

#### Instances created from a specific template

```python
{ "query": { "$and": [
    { "$match": { "field": "type", "value": "grid", "mode": "keyword" } },
    { "$match": { "field": "isTemplate", "value": false } },
    { "$match": { "field": "system.Origin Template", "in": "tags", "as": "text",
                 "value": "grid:935d381a-6b98-4ba9-8dfd-68b755275444", "mode": "keyword" } }
] } }
```

#### Inventory containers (remember `source=IVT`)

```python
POST /entities/search?source=IVT
{ "query": { "$and": [
    { "$match":  { "field": "type", "value": "container", "mode": "keyword" } },
    { "$match":  { "field": "isTemplate", "value": false } }
] } }
```

```python
{ "query": { "$match": { "field": "_starringUserIDs", "value": "100", "mode": "keyword" } } }
```

## 12 · Practical notes

String Tokenization & Exact Keyword Matching
By default, string matching tokenizes values on hyphens and punctuation. For example, a query for `{"$match": {"field": "type", "value": "experiment"}}` without `mode: "keyword"` matches both `experiment` and tokenized variants like `delete-experiment`. To perform exact string or entity type matching, specify `"mode": "keyword"` inside your `$match` clause.
Names are unique within a notebook, not across the tenant
      Signals rejects a second entity with the same name, of the same type, in the same parent — the API returns `409 Conflict`
      with “cannot have the same name as an existing item of same type in same location”. The constraint is scoped to the
      parent, so the same experiment name may legitimately exist in several notebooks. A name is therefore a usable key only in combination with
      its notebook; pair the name match with a `$parent` constraint, or filter on `_parent_eid`, when you need one specific
      entity. And because this is a lookup by exact value, it must carry `mode:"keyword"` — see above.

* Set isTemplate Without it, searches return real entities and their templates. Pin `isTemplate:false` for content queries.

* Use mode:"keyword" for exact matches On `type`, names, ids, and exact tag values — see the warning above, which this list does not repeat. Omitting it analyses the value into tokens and over-matches silently.

* Pick the right source The default index is notebook content; inventory (`container`, `asset`) needs `source=IVT`. A source mismatch returns zero rows with no error — check it first when a query comes back empty.

* total vs. count `meta.total` is all matches; `meta.count` is this page. Page from `total`.

* Companion endpoints Both take the same `query` shape. `POST /entities/search/terms` takes an extra `field` and returns that field's distinct values with counts — the basis of faceted filters, and the way to discover which values a field actually holds. `POST /entities/search/tags` returns the tag fields themselves, each with a count and the data types it is indexed as — which is how you find the correct `as` type for a tag field.