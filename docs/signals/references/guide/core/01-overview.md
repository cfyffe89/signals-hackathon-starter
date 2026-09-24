# Overview

Welcome. Signals is an electronic data-capture and management application built on a resilient, scalable cloud architecture. This guide shows you how to extend it — reading and writing data, reacting to events, and connecting your own systems.

## Introduction

Signals is delivered as a SaaS application and updated frequently with minimal disruption to end-users. This documentation walks through the principles, concepts, and components you'll use to build integrations — from a one-off script to a fully automated data pipeline.

If you're here to do something specific, the table below points you straight to the right component and page. If you're new to Signals, read on through Core Concepts first.

## What you can build

Signals offers four integration surfaces. Most real solutions combine several — but you can start with just one.

I want to…| Use| Learn more  
---|---|---  
Read or write Signals data from my own application| **REST API**| REST API  
Find or extract specific entities (and keep an external copy in sync)| **Search**| Search  
Add a button in Signals that opens my web app for a custom workflow| **External Actions**| External Actions  
React automatically when users sign, create, or export records| **External Notifications**| External Notifications  
Populate dropdowns or table rows from my systems of record| **External Lists & Data Sources**| External Data Sources & Lists  
  
## Before you start

A few facts that get you to a first successful call. Full details live on the REST API page.

What| Value  
---|---  
**API base URL**|  https://<your-tenant>/api/rest/v1.0  
**Interactive API docs**|  Swagger UI at `https://<your-tenant-url>/docs/extapi/swagger/index.html` — test endpoints live in your browser. Reach it via _System Configuration → System Settings → API Key → "Open External API Document."_  
**OpenAPI Specification**|  Download the complete OpenAPI 3.0 specification file (`openapi.yaml`) directly from Signals Notebook under _System Configuration → System Settings → API Key → "Open External API Document"_ by clicking the **Download** button next to it.  
**Authentication**|  An API key in the `x-api-key` header (server-to-server), or an OAuth bearer token (user-attributed actions). Keys are generated in _System Settings → API Key_.  
**Versioning**|  APIs are versioned (`v1.0`); new endpoints appear in the Swagger UI as they're released, so existing integrations keep working.  
  
**Verifying your credentials** To confirm a key is working, call `GET /api/rest/v1.0/version`, which returns the release, or `GET /api/rest/v1.0/profiles/me`, which returns the user the key belongs to.

## General Principles

These principles guide how the integration surfaces are designed — and how we suggest you approach building on them.

**Simple should be simple.** Common use cases built on well-defined APIs should be straightforward to implement.

**Supportability.** Integrations, however complex, should never impede the supportability of the application.

**Don't mess with what isn't broken.** Existing systems shouldn't need major changes to serve a specific integration.

**Future vision.** Integration is central to a transformative future — automatic data capture, data pipelining, and more.

**Adherence to standards.** Experienced developers should find the technology familiar, lowering the barrier to implementation.

## Core Concepts · Entities

In Signals Notebook, nearly everything you interact with is an **Entity** — from top-level Notebooks and Experiments down to an individual text element or table. Every entity has a unique identifier, referred to as its **Entity ID** , **eid** , or simply **id**. You'll use these constantly to address specific entities through the API.

An Entity ID is a `type:uuid` string. For example, an experiment:
    
    
    experiment:03ae2d17-e94d-466a-ba83-94d89a3cea2f

### Common entities and their internal types

The `type` prefix in an eid — and the `type` you filter on in Search — uses these internal names:

Area| Entity| Internal type  
---|---|---  
Notebook & experiment| Notebook| journal  
Experiment| experiment  
Text element| text  
Worksheet| worksheet  
Tables| Admin Defined Table| grid  
Materials Table| materialsTable  
Variations Table| variationsGrid  
Hierarchical Table| hierarchicalGrid  
Chemistry| Chemical Drawing| chemicalDrawing  
Samples & inventory| Sample| sample  
Samples container (in an experiment)| samplesContainer  
Inventory container| container  
Inventory asset / batch / material library| asset · batch · assetType  
Plates| Plate| plate  
Plate map| plateMap  
Biopolymers| Monomer| monomer  
Monomer library| monomerLibrary  
Tasks| Task| task  
Task container| taskContainer  
Files & analysis| Image| imageResource  
Uploaded file| uploadedResource  
Spotfire for Signals| signals_spotfiredxp  
  
This is the common set, and your tenant may hold others. To list the types that actually exist in your tenant, ask the Search API for the distinct values of the `type` field. The `/entities/search/terms` endpoint returns each value with a count rather than returning the entities themselves:
    
    
    POST /api/rest/v1.0/entities/search/terms
    
    {
      "query": { "$match": { "field": "isTemplate", "value": false } },
      "field": "type"
    }
    
    
    // each entry is a type present in your tenant, with how many exist
    { "data": [
        { "attributes": { "term": "monomer",         "count": 1256 } },
        { "attributes": { "term": "sample",          "count": 270  } },
        { "attributes": { "term": "chemicalDrawing", "count": 253  } },
        { "attributes": { "term": "experiment",      "count": 111  } }
    ] }

The same endpoint works on any field, so it is also the way to discover the values in use for a custom field. See the Search page for the full query language.

### Finding an Entity's ID

You can get an eid three ways:

  * **From an API response** — most calls return entities with their `id` in the `data` object. See the REST API page for how responses are structured.
  * **From the app** — open the entity in Signals; its eid appears in the browser URL.
  * **By searching** — `POST /entities/search` returns matching entities and their ids. See the Search page.

## Key terms

A few terms recur throughout the guide — worth knowing up front.

Entity / eid
    Any addressable object in Signals, and its unique `type:uuid` identifier.

digest
    A version stamp on an entity. Send it back on an update so the server can detect if someone else changed the entity in the meantime.

template
    A reusable blueprint an entity was created from. Real content has `isTemplate: false` — most queries filter templates out.

state
    An entity's workflow status, e.g. `open` or `closed`.

fields / tags
    An entity's named data values. In search responses these are exposed as searchable _tags_.

## System Configuration

Administrators configure a tenant — including every integration point in this guide — from the **System Configuration** area, reached at your tenant's URL. Setting up External Actions, Notifications, and Data Sources requires administrator access.

Step-by-step setup for those features lives in the **System Configuration Guide** , opened from the drop-down menu within System Configuration. This developer guide focuses on what your code does; the configuration guide covers the admin screens.

## External Servers & architecture

Most integrations run through an **external server** you host — a bridge between Signals' APIs and your own systems. It's where you handle authentication, transform data between formats, and orchestrate multi-step workflows, keeping that complexity out of Signals itself.

An external server typically lets you:

  * **Exchange data** with Signals via the REST API and push it downstream into your digital lab.
  * **Receive events** from External Notifications and trigger automated workflows.
  * **Serve data** to Signals as External Lists and Data Sources, in the shape Signals expects.
  * **Authenticate and authorize** access, so only permitted users and applications reach sensitive data.

### How it fits together

Signals SaaS cloud Your External Server LIMS Registry Data lake / BI REST API External Actions Notifications Lists & Data Sources

Signals reaches your external server through four channels; your server bridges to your own systems of record.

A fuller solution uses several channels together. For example: an **External List** keeps project codes current in Signals; an **External Data Source** pulls instrument metadata into a table by barcode; an **External Action** registers a sample in your LIMS; and a **Notification handler** archives an experiment automatically when it's signed and closed.

## Where to go next

**REST API →** Authentication, responses, digests, error handling. **Search →** Find and extract exactly the data you need. **External Actions →** Launch your app from a button in Signals. **External Notifications →** React automatically to Signals events. **External Data Sources & Lists →**Feed dropdowns and tables from your systems. **Tutorials →** End-to-end, hands-on walkthroughs.
