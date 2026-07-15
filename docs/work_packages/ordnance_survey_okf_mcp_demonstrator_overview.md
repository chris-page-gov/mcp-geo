# Ordnance Survey data discovery with OKF and MCP

Discussion brief for Ordnance Survey<br>
Prepared: 15 July 2026<br>
Repository: <https://github.com/chris-page-gov/mcp-geo><br>
Shareable demonstrator: <https://chris-page-gov.github.io/mcp-geo/discovery/>

## The proposition

This demonstrator explores one practical question:

> Can a person or software agent discover the right Ordnance Survey data by subject and place,
> understand why it is authoritative and how it can be used, and then move safely from discovery
> to a read-only operation?

It combines three independently useful pieces:

- **Open Knowledge Format (OKF)** provides a portable, deterministic description of the data,
  resources and operations available. It makes sources, spatial meaning, access routes and
  callable capabilities visible before anything is executed.
- **Model Context Protocol (MCP)** provides the governed delivery and execution layer. A client
  can read the same OKF resources and invoke an existing OS-backed operation without putting the
  server's credential into the knowledge pack.
- **The discovery UI** demonstrates the human experience: text search, ordinary facets and a map
  operate over the same records, and a selected record exposes both its provenance and its MCP
  request contract.

The aim is not to reproduce a consumer web map. It is to make the value behind the map easier to
discover: products and feature semantics, identifiers, geographic applicability, currency and
provenance, access routes, and the operations supported by the data.

## What is available now

The checked-in demonstrator contains a deterministic OKF pack with:

- **404 searchable records**: 103 MCP tools, 28 stable MCP resources and 273 OS API catalogue
  entries;
- **210 spatial profiles**, covering location, named coverage, coordinate reference systems,
  spatial filters and geometry meaning; and
- **15 read-only MCP bindings** across OS Places, OS Features and OS Linked Identifiers.

The six JSON assets are a descriptor, manifest, overview, records, spatial index and MCP binding
index. Integrity hashes allow drift to be detected, and rebuilding the pack makes no network
calls. The snapshot contains no credential values.

### Shareable GitHub Pages experience

The Pages URL is the self-contained, public discussion surface. It provides:

- keyword search and metadata facets;
- synchronized List and Map views over the discoverable records;
- an Explorer House journey linking Places, NGD feature discovery and Linked Identifiers;
- spatial, source and access metadata for selected records; and
- inspectable read-only MCP request templates.

It uses the checked-in snapshot, so it remains useful without an API key or a running MCP server.
The public UI does **not** imply that a displayed query anchor is a dataset extent, or that a
nearby building feature is joined to an address unless OS returns an authoritative relationship.
The Pages build intentionally has no credential prompt and cannot execute live OS calls: people
can inspect the generated MCP request, but credentials and execution stay on the governed server.

### Live MCP and OS-backed experience

The repository server adds capabilities that a static Pages site cannot provide:

- MCP `resources/list` and `resources/read` delivery of all six OKF resources over HTTP or STDIO;
- execution of the existing read-only OS tools through generated binding templates;
- a server-managed OS credential, normalized errors and the repository's authentication boundary;
  and
- the proxied OS Light vector basemap when permitted and configured.

The credentialled flow was rehearsed on 15 July 2026 using the Explorer House postcode. It
successfully resolved an address, discovered the then-current NGD building collection, returned
nearby building geometries, queried Linked Identifiers and executed a generated binding over MCP.
The retained evidence records only statuses and counts; no key or reusable returned identifier was
written to the repository. Those results are time-sensitive and should not be treated as a
permanent data snapshot.

## How the pieces fit together

```text
OS catalogue + MCP tool/resource registries
                 |
                 v
       deterministic OKF builder
                 |
       OKF descriptor and indexes
          /                     \
 public discovery UI       MCP resources/read
          |                     |
   discover and select    bind and execute safely
          \                     /
           source and result audit
```

This follows the lifecycle discussed in the API-to-MCP presentation:

1. **Publish** authoritative metadata and capability contracts as a versioned OKF pack.
2. **Discover** by text, facets or spatial context.
3. **Bind** the selected record to an explicit MCP tool and argument contract.
4. **Execute** a safe, read-only operation through the governed server boundary.
5. **Audit** the source, arguments, identifiers and outcome without overstating relationships.

MCP does not replace API, product or metadata governance. OKF makes those decisions portable and
inspectable; MCP provides a standard route from an understood capability to controlled use.

## Suggested demonstration

The Pages-only discussion takes approximately three minutes:

1. Open <https://chris-page-gov.github.io/mcp-geo/discovery/> and select the
   **Explorer House** example.
2. Search for `building` and refine to OS Features.
3. Switch between List and Map to show that spatial eligibility is an explicit discovery facet.
4. Open a Places, Features or Linked Identifiers record and inspect its source, coverage, CRS,
   geometry meaning and access statement.
5. Reveal the **Use via MCP** request to show that discovery produces an executable but still
   reviewable contract.

For the live server extension, use values returned by each operation rather than slideware
identifiers: resolve postcode `SO16 0AS`; select an address and its returned UPRN; discover the
current building collection; query a small bounding box around the returned point; then inspect
Linked Identifiers exactly as returned. A feature near an address is not asserted to be the same
real-world object without an authoritative returned relationship.

## Data, access and security boundaries

- The published catalogue is the repository's **checked-in snapshot**, not a claim that product
  currency, licence, access tier or withdrawal metadata has been ratified by OS.
- The demonstrator describes Great Britain coverage for the featured APIs; it does not claim
  complete United Kingdom coverage.
- Explorer House is a sourced **query location**, not an OS site boundary, dataset centroid or
  authoritative coverage extent.
- The OKF generator and output contain no OS API key. Public discovery is deliberately key-free.
- In the server flow, the OS key remains server-managed and is not included in browser arguments,
  MCP binding records or retained rehearsal evidence.
- Live execution is read-only. Missing server credentials produce the explicit `NO_API_KEY`
  condition rather than causing the UI or pack to fabricate a result.
- The two OKF extensions, `okf-geospatial.v1` and `okf-mcp-binding.v1`, are exemplar profiles for
  joint evaluation, not ratified standards.

## Proposed 4–6 week joint work package

Take forward one vertical slice: **spatial discovery from an address to the relevant OS data and
capabilities around it**.

| Stage | Indicative timing | Joint outcome |
| --- | --- | --- |
| Discovery contract | Week 1 | Agree three user tasks, authoritative metadata sources, terminology, baseline and measurable targets. |
| Production-shaped OKF profile | Weeks 1–2 | Validate product/API/collection mappings, provenance, spatial semantics, access, licence and currency fields; retain deterministic generation and integrity checks. |
| Governed MCP slice | Weeks 2–3 | Harden the Places → current NGD Features → Linked Identifiers flow with server-managed access, normalized failures and audit evidence. |
| OKF Explorer integration | Weeks 3–4 | Move the Map view into the reusable OKF Explorer, with one shared result pipeline and deep-linked text, facets, viewport and selection. |
| Staff pilot and hardening | Week 5 | Test agreed discovery tasks, accessibility, performance, metadata quality, source freshness and no-result/error paths. |
| Optional scale and handoff | Week 6 | Add a wider product family and agree ownership, export cadence, release policy and the next measured backlog. |

Week 5 is the minimum complete package; Week 6 is an explicit scale and handoff option.

## Success measures to agree with OS

The pilot should begin with a baseline and a numeric target owned by OS. Candidate measures are:

- time and success rate for choosing the correct product, collection and operation for three
  representative tasks;
- whether users can distinguish a product, API operation, returned feature, coverage area and
  query location without facilitation;
- complete, source-backed access and spatial metadata, with unknown or partial values visible
  rather than silently omitted;
- identical stable record IDs and counts across List and Map for the same query state;
- successful discovery and execution of the read-only flow by a clean MCP client, including
  truthful credential, zero-result and upstream-error paths;
- byte-identical rebuilds from unchanged sources and explainable diffs when sources change; and
- no OS secret in generated files, browser persistence, client arguments or retained evidence.

## Questions for the joint discussion

1. Which three discovery tasks most need improvement, and who is the first target user?
2. What are OS's authoritative systems of record for products, datasets, NGD collections, API
   operations, versions, withdrawals, licences, access tiers and geographic coverage?
3. Which metadata most clearly conveys the value behind OS mapping: currency, lineage,
   completeness, identifiers, precision, feature semantics, change history or service assurance?
4. Which distinctions between product, dataset, collection, feature type, operation and download
   must the OKF profile preserve?
5. What relationship would OS regard as authoritative between an address UPRN, an NGD building
   feature and linked identifiers?
6. What does OS's current MCP work already expose, which clients matter, and which contracts are
   expected to remain stable?
7. What access, licence, attribution, rate-limit, caching and demonstration rules should the
   pilot observe?
8. Which measurable outcome would justify continuation, and who would own metadata export,
   profile decisions, MCP contracts, Explorer integration and release cadence?
9. Which additional OS product family would best test whether the approach generalises?

## Further detail

The repository contains the full implementation notes, six-minute live script, acceptance
criteria and staged delivery gates in `docs/work_packages/os_okf_mcp_discovery.md`. The
credential-safe live check is recorded in
`docs/work_packages/os_okf_mcp_live_rehearsal_2026-07-15.md`.
