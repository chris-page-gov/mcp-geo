---
aliases: [IPR, licensing, governance, Cranfield, Defra agreement]
tags: [strategy, governance, licensing, IPR, cranfield, defra, landis]
---

# Governance and Licensing

## Ownership and IPR

LandIS data is jointly owned by **Cranfield University** and the **Crown (Defra)**. The formal arrangement:

- Cranfield University holds soil information and data for England and Wales across published maps, reports, unpublished field records, and digital data in LandIS
- A legal agreement between Cranfield and the Crown grants Cranfield the **exclusive right to licence** the digital data
- Defra and Cranfield "jointly own" the IPR

This arrangement means Cranfield is the licensing authority, operating under a framework agreed with Defra.

## Historic Licensing Model (Pre-2026)

The historic model was complex and user-status dependent:

| User Type | Access Terms |
|---|---|
| Crown bodies (Defra, EA etc.) | Royalty-free; administrative fee only |
| Non-Crown public bodies (LAs, NRW etc.) | Subject to commercial terms or significant restrictions |
| Academic/bona fide research | Administrative fee, no royalties (special condition) |
| Commercial users | Commercial licence required |
| Third parties (e.g. consultants) | Had to approach Cranfield directly |

**Time-limited licences** (1 year): derived data must be deleted at licence expiry. This was a major reproducibility barrier — any dataset, model, or product derived from LandIS was subject to deletion unless the licence was renewed.

**NRW restriction**: Natural Resources Wales metadata records explicitly state that NRW may not publish or disseminate LandIS data and third parties must approach the owner directly.

## The 2026 Open Access Agreement

A Defra procurement notice (February 2025) documents the decision:

> Cranfield and Defra agreed for Cranfield to make **"the majority"** of key datasets openly available, explicitly to support ELMS, Nature Recovery, ALC, NCEA, and net zero work.

Cranfield's January 2026 press release confirmed an open access portal (portal.landis.org.uk) would launch during 2026 with free access to extensive data.

## Provenance and Ordnance Survey

NATMAP Vector is registered to an OS 1:50,000 base (redigitised 1999). Any derived outputs may need to carry Ordnance Survey crown copyright notices. This is an [[Open Questions|unresolved open question]] for the portal's licensing terms.

## Governance Implications for MCP

Any MCP server or AI tool built on LandIS data must:

1. **Attach licence and version information** to every output — the provenance layer is non-negotiable
2. **Track the transition**: historic time-limited licence constraints may still apply to some cached or archived data, even if the portal moves to open terms
3. **Avoid encouraging prohibited reuse** where restrictions remain for specific datasets
4. **Version-control outputs** so they can be audited against the dataset version that generated them
5. **Reference the open-access licence text** explicitly — once it is confirmed at portal.landis.org.uk

> [!warning] Rapid Licensing Transition Risk
> The open access transition creates a period of ambiguity. Confusion between historic licence models (delete derived data after 1 year) and new open terms could cause compliance failures if not handled explicitly in tool design.

## The Assurance Layer

This governance context is why the [[MCP Overview|MCP design]] includes a mandatory **assurance layer** that automatically binds:
- ISO metadata
- Cranfield versioning
- "Not suitable for detailed site assessment" caveats
- Licence references

to every single output from the system.

---

## Sources
- [Defra procurement notice](https://www.find-tender.service.gov.uk/Notice/005506-2025)
- [Cranfield National Soil Map case study](https://www.cranfield.ac.uk/case-studies/national-soil-map)
- [NRW metadata record](https://test.metadata.naturalresources.wales/geonetwork/srv/api/records/EXT_DS119264)
- [Defra digital blog](https://defradigital.blog.gov.uk/2023/12/05/world-soil-day-how-were-improving-access-to-soils-data-and-information-for-england-and-wales/)

---
*← [[00 - Home|Home]]  |  See also: [[Open Access Transition]], [[Open Questions]], [[MCP Overview]]*
