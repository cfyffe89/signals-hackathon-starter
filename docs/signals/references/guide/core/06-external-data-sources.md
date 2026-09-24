# External Data Sources, Lists & Chemical Sources

Signals can pull data from systems you host directly into the notebook — as dropdown values, as live table rows, and as chemical structures in a reaction. All three are configured under one _Data Sources_ area and share the same basic model.

**1** Overview **2** How they work **3** External Lists **4** External Data Sources **5** External Chemical Sources **6** Limits **7** Next steps

## 1 · Overview

There are three external source types. They differ in what they return and where the data lands in Signals:

Type| Returns| Lands in| Direction  
---|---|---|---  
**External List**|  A list of values| An attribute's dropdown / picklist| read  
**External Data Source**|  A record, by key| Rows of an Admin-Defined Table| read write  
**External Chemical Source**|  A structure + properties, by key| Reactants / Products in Stoichiometry| read  
  
System Configuration → Data Sources. All three source types are created from here.

Choose a **List** to keep a field's options in sync with a system of record; a **Data Source** to fill (or push back) a whole table row from a key such as a barcode; and a **Chemical Source** to let chemists pull a registered compound's structure into a reaction.

## 2 · How they work

All three source types share a common model:

  * **You host a RESTful URL.** Signals calls it and expects JSON in response. A static file is sufficient for a read-only List; a dynamic service is required for keyed lookups and writes.
  * **Header authentication.** Each configuration supports one or more **HTTP headers (name + value)** — for example an API key — which Signals sends on every request so your server can authenticate the call. Use **Add HTTP Header** to define as many as your endpoint requires.
  * **Fetch Example Data & field mapping.** A button pulls a sample response so you can map external fields to Signals — choosing the key, descriptions, data types, and which fields to include. A **Test** control exercises the endpoint before you save.
  * **Response-time budgets.** To protect the UI, Signals gives up if your server is slow — **Lists at 30 seconds** , **Data & Chemical Sources at 20 seconds**.

All three are created under _System Configuration → Data Sources → Create Data Source_. Every configuration field is documented in the sections below; the System Configuration Guide covers the administrative procedure and the permissions needed to reach these screens.

**Proxy mode** Where the **Use Preconfigured Proxy** feature is enabled for the tenant, a source can route through a preconfigured proxy instead of calling your URL directly. **Source** then becomes a dropdown of available proxy URLs, **Destination URL** is populated from the chosen proxy, and a **Context** field supplies the trailing path segments of the destination. The data contract your endpoint must satisfy is unchanged.

**Two further source types, out of scope here** **Create Data Source** also offers **Internal Data Source** (drawing on data already inside Signals) and **External Ontology Source**. Neither requires you to build an endpoint, so neither is covered on this page; both are described in the System Configuration Guide.

## 3 · External Lists

An External List populates an attribute's dropdown from your server. It is read-only, and Signals holds a cached copy that is refreshed on a schedule.

**Refresh is configured on the attribute, not on the source** The source defines _where_ the values come from; refreshing is set where they are consumed. In **Attributes → Create Attribute → List** , select **External List** and choose the source. That attribute page then offers **Schedule a Refresh Now** for an immediate pull, a **Refresh Frequency** of **Hourly** , **Daily** , or **Never** , and a **Last Refreshed** timestamp.

**A new list attribute is empty until its first refresh** Creating the attribute does not populate it. Run **Schedule a Refresh Now** once, or users will see an empty dropdown and conclude the integration is broken.

#### Data format

A `GET` returns a top-level `data` array of objects. Objects may carry several fields; you pick which one is the list's **key** (the stored value) and, optionally, a description field.
    
    
    GET https://your-server/list  →
    { "data": [
        { "code": "BIO-100", "project": "Oncology Screen" },
        { "code": "CHM-204", "project": "Lead Optimization" }
    ] }

#### Configuration

Field| What it does  
---|---  
Source Name · Description| Identify the list.  
Destination URL| The endpoint Signals calls.  
HTTP Headers| Optional authentication headers sent with the request. Add as many as required.  
Fetch Example Data| Pull a sample response to map fields.  
Field mapping| For each external field: an **Internal Field Name** , and flags **Key** (the stored value — required, exactly one), **Desc.** (shown with the option), and **Include**. **Add Manual Field** covers values not present in the sample.  
  
Attach the list to a list-type attribute (_Configuration → Attributes_); any field or table using that attribute then shows your live options.

## 4 · External Data Sources

A Data Source fills an Admin-Defined-Table row when a user enters a key, and can push rows back to your system.

#### The URL carries the lookup value

The Destination URL is a template. Signals substitutes the key the user enters as `{id}`, and can also send `{username}` and `{user_alias}`:
    
    
    https://your-server/flasks/{id}
    e.g. https://abc.com?id={id}&un={username}&alias={user_alias}

#### Operations
    
    
    GET  /flasks/88             → { "id":"88", "name":"Flask A", "amount":250 }   // fetch by key
    POST /flasks  { … }         → creates & echoes the row
    PUT  /flasks/89 { … }       → updates & echoes the row

#### Nested responses are flattened automatically

A response does not have to be flat. Signals walks the JSON it receives and offers _every leaf value_ as a mappable field, naming each one by its path. Nested objects and arrays therefore require no flattening on your server.

In your response| Offered as a field  
---|---  
Nested object, to any depth| `address.city`, `a.b.c.d`  
Array of values| `tags[0]`, `tags[1]`, `tags[2]`  
Array of objects| `variants[0].ratio`, `variants[1].ratio`  
Array inside an array| `matrix[0][1]`  
Object inside a mixed array| `items[4].detail`  
Key that itself contains a dot| `["field.with.dots"]` — bracket-escaped, so it is not read as a path  
  
Keys containing spaces, hyphens, or mixed case are preserved exactly as sent, and `null` values map normally, arriving as empty cells.

**Empty objects and arrays cannot be mapped** An `{}` or `[]` is listed as a field but holds no value to convert, so it fails validation against every data type. Leave such fields unmapped — which does not prevent saving — or return a scalar value instead of an empty container.

**The mapping follows your example record** The field list is derived from the record fetched for the **Example ID**. If your endpoint later returns leaves that record did not contain, they have no mapping until you run **Fetch Example Data** again. Where a response shape varies between records, choose an example that contains every field you intend to map.

#### Data types and conversion

Each mapped field is assigned one of six data types:

TextNumberIntegerCheckboxDate/TimeExternal Hyperlink

Conversion is deliberately strict. A value that cannot be represented in the chosen type is reported by **Test Mapping** rather than being silently altered:

Value sent| Mapped to| Result  
---|---|---  
`3.14159`| Integer| Rejected Fractional values are never truncated to fit.  
`"red"`| Number| Rejected Text that is not numeric is not coerced.  
`"true"`| Checkbox| Rejected Checkbox requires a real JSON boolean, not the string.  
`"2026-07-28"`| Date/Time| Rejected A time component is required, as in `2026-07-28T14:30:00Z`.  
`"42"`| Number| Accepted Numeric strings are parsed.  
`true`| Checkbox| Accepted  
  
**Map identifiers to Text, not Number** A numeric-looking string is accepted as a Number, and its leading zeros are lost: the postcode `"02101"` becomes `2101`. Postcodes, part numbers, and similar identifiers must be mapped to **Text** to survive intact.

#### Configuration

Field| What it does  
---|---  
Source Name · Description · URL| Identify the source and its endpoint template.  
HTTP Headers| Optional authentication headers, **up to 20** per source. Use **Add HTTP Header** to add each one.  
Example ID| A sample key so Fetch Example Data has something to look up.  
Available operations| Tick GET to fetch, POST to create, PUT to update. GET-only = read-only lookup.  
Field mapping| Map each external field to a Signals **Data Type** and mark exactly one as the **Key**. Nested responses are flattened for you — see above.  
  
Use the source from an Admin-Defined Table: entering a key in a row triggers the `GET` and fills the mapped columns. With POST/PUT enabled, edited rows sync back to your server.

## 5 · External Chemical Sources

A Chemical Source is the chemistry-aware relative of a Data Source. For a key — a compound name or id — it returns a **chemical structure plus properties** , and drops them straight into a reaction's Reactants or Products grids through the ChemDraw plugin's **Quick Add**.

**Enable Stoichiometry Configuration** With this toggle on, the source is connected to the Reactants and Products tables in Stoichiometry, so end-users can add its products and reactants via Quick Add. This is what makes a Chemical Source more than a generic table lookup.

The External Chemical Source configuration panel showing Destination URL, Quick Add hint text, and stoichiometry column mapping.

#### The data contract

Like a Data Source, but the record includes a structure field (SMILES, MOL, …) alongside properties:
    
    
    GET https://your-server/chem/{id} // same {id}/{username}/{user_alias} placeholders
    
    GET /chem/benzene →
    { "id": "benzene", "name": "Benzene", "CAS": "71-43-2",
      "MW": 78.11, "MF": "C6H6", "smiles": "c1ccccc1" }

#### Configuration

Field| What it does  
---|---  
Enable Stoichiometry Configuration| Connects the source to Reactants/Products for Quick Add (see above).  
Source Name · Description · URL · HTTP Headers · Example ID| As for a Data Source.  
Quick Add Hint Text| The prompt shown in the Quick Add box for this source.  
Chemical structure field + Structure Format| Which response field holds the structure, and its format (e.g. SMILES). Tick **Base64 Encoded** or **Chemical Structure is Link** if the structure is encoded or referenced by URL rather than inline.  
Record Field → column mapping| Map your response fields to Stoichiometry columns (see below).  
  
Mapping the structure field and format, then each record field to a Stoichiometry column.

#### Mappable stoichiometry columns

Beyond the structure, a Chemical Source can populate any of these reaction columns:

Group| Columns  
---|---  
Identity| Product/Reactant Name · CAS Number · Reg ID · HELM · Supplier · Lot Number · Barcode  
Structure-derived| MF · FM · MW · EM  
Quantities| Load · Molarity · d (density) · % Wt · Purity · Conversion  
  
Use **Test Mapping** to confirm the fields resolve, then save. In a Chemical Drawing's stoichiometry grid, a user picks **Quick Add** and types a key (`benzene`); Signals fetches the record, renders the structure into the reaction, and fills the mapped columns.

## 6 · Limits

Limit| Detail  
---|---  
List size| Up to **20,000 items** per External List.  
Lists per tenant| Up to **200**.  
List response time| **30 seconds** before timing out.  
Data & Chemical Source response time| **20 seconds** before timing out.  
  
**Response time** These budgets are firm, and keyed sources are called during user interaction. Cache upstream lookups and pre-shape responses so that a request resolves quickly rather than triggering a live cross-system query.

## 7 · Next steps

For a hands-on walkthrough — including a single reference server that implements all three contracts (a list, a keyed data source with GET/POST/PUT, and a chemical source returning a structure) — see the tutorial **External Lists, Data Sources & Chemical Sources**. To read or write the entities these sources feed, see the REST API and Search pages.
