# Teignmouth, Exmouth and Sidmouth wheelchair-access comparison

## Purpose

This note explains why Exmouth and Sidmouth are useful nearby comparison towns for the Teignmouth
wheelchair-access work.
It is not a certification or access audit. It is a planning note that combines live MCP-Geo route filtering with
official public accessibility information and route-to-audit recommendations.

## Comparison roles

- `Teignmouth`: constrained test case, especially around the peninsula and steeper path network.
- `Exmouth`: strongest positive comparator for a broad, rail-served station-to-town-centre-to-seafront route network.
- `Sidmouth`: compact-core comparator with short visitor-to-seafront distances and current accessibility improvements, but not a like-for-like rail-arrival case.

## Why Exmouth remains the strongest positive comparator

Exmouth is a strong positive comparator because it is:

- nearby on the same Devon coast
- a rail-served coastal town with a clear town-centre and seafront core
- officially promoted as highly accessible at destination level
- large enough to test whether MCP-Geo identifies broader, flatter, better-lit route networks

Official context:

- Visit Exmouth states that Exmouth is "one of the most accessible towns in Devon", that the high street and town centre are very level, that the promenade is flat, and that the town has disabled parking bays and beach wheelchairs:
  <https://www.visitexmouth.co.uk/accessibility>
- Visit Exmouth also says Exmouth Beach Wheelchairs are available on Queen's Drive:
  <https://www.visitexmouth.co.uk/exmouth-beach-wheelchairs>
- National Rail lists Exmouth station as `step-free category A` with accessible toilets and a Changing Places toilet:
  <https://www.nationalrail.co.uk/stations/exmouth/>

## Why Sidmouth is still worth adding

Sidmouth is useful for a different reason. It appears to offer a compact visitor core where key destinations are close
to one another and very close to the mapped accessible network, even though the town is not as strong as Exmouth on
overall preferred-route length.

Official context:

- Visit Sidmouth says the town beach has beach mats and ramps and that flat, solid routes make exploring Sidmouth
  accessible to people using mobility aids:
  <https://www.visitdevon.co.uk/sidmouth/things-to-do/activities/>
- Visit Sidmouth’s accessibility page says Sidmouth does not have a train station, says pavements and promenades are
  mostly level and wide enough for scooters and wheelchairs, notes lowered kerbs, accessible toilets, and seasonal
  beach matting:
  <https://www.visitdevon.co.uk/sidmouth/visitor-information/accessibility-in-sidmouth-and-east-devon/>
- Sidmouth’s Tourist Information Centre is on Ham Lane and is also the local point for visitor information and RADAR-key support:
  <https://www.visitdevon.co.uk/sidmouth/visitor-information/information-centre/>
- Sidmouth Town Council lists Market Place and other accessible public toilets and notes RADAR-key access arrangements:
  <https://sidmouth.gov.uk/community-services/public-conveniences/>

## MCP-Geo comparison snapshot

These figures are from live extracts on `2026-03-07`. They are useful for directional comparison, but the bboxes are not identical in shape or area.

| Metric | Teignmouth core | Exmouth core | Sidmouth core |
| --- | --- | --- |
| BBox | `[-3.5025, 50.5405, -3.4905, 50.5495]` | `[-3.4215, 50.6095, -3.3960, 50.6238]` | `[-3.2445, 50.6760, -3.2330, 50.6826]` |
| Road links | `422` | `910` | `237` |
| Path links | `306` | `532` | `140` |
| Pavement polygons | `145` | `276` | `85` |
| Preferred route length | `2.84 km` | `5.32 km` | `1.26 km` |
| Use-with-care route length | `4.17 km` | `18.90 km` | `5.68 km` |
| Barrier length | `1.25 km` | `2.60 km` | `0.44 km` |
| Anchor gap 1 | `Teignmouth station` about `26 m` | `Exmouth railway station` about `22 m` | `Tourist Information Centre` about `5 m` |
| Anchor gap 2 | `Shopmobility` about `27 m` | `Exmouth indoor market` about `28 m` | `Sidmouth Market` about `12 m` |

Interpretation:

- Exmouth produces a much larger continuous preferred network than Teignmouth under the same conservative filtering rules.
- Exmouth also produces a much larger use-with-care network because the tested footprint is broader and includes more residential and seafront movement corridors.
- Sidmouth produces a smaller preferred network than Exmouth, but its anchor gaps are materially shorter than both Exmouth and Teignmouth.
- Teignmouth remains the tighter and more constrained case, especially around the peninsula and steeper path network.

## What the comparison suggests

Exmouth shows the strongest accessible spine between the station, town centre, and seafront. In the current extract the best-named preferred corridors include:

- `Victoria Road`
- `Cyprus Road`
- `Esplanade`
- `Queens Drive`
- `BEACH GARDENS`
- `MANOR GARDENS`

That is the kind of pattern expected in a flatter destination with a broad promenade and more continuous public realm.

Sidmouth reads differently. It shows a smaller but tighter accessible core with very short approach distances to the
visitor anchors. In the current extract the best-named preferred corridors include:

- `The Esplanade`
- `Station Road`
- `All Saints Road`
- `EAST STREET`

That suggests Sidmouth is a useful benchmark for compact seafront-town-centre movement, but not a substitute for Exmouth
as the strongest positive accessibility comparator.

## What this does not prove

Even in Exmouth, the map still does **not** prove:

- dropped kerbs are present and flush
- crossings are safe and convenient
- parking bays are usable on the day
- beach-wheelchair storage or hire points are always open
- routes are free of clutter, bins, A-boards, café furniture, or works

The map is best used as a pre-audit route hypothesis, not as a final assurance document.

## Organisations and registers worth using next

There is no single authoritative UK register of “accessible towns”. For formal assessment, the best route is to combine mapping with professional audit and lived-experience validation.

Recommended stack:

1. `MCP-Geo`
   use it to define candidate accessible corridors, likely barriers, parking questions, bus-stop questions, and priority audit routes.
2. `NRAC`
   the National Register of Access Consultants is the clearest route to a formal town-centre or destination access audit by an accredited specialist:
   <https://www.nrac.org.uk/>
3. `AccessAble`
   VisitBritain now points businesses and destinations toward AccessAble Detailed Access Guides, including guided and on-site assessment routes:
   <https://www.visitbritain.org/business-advice/make-your-business-accessible-and-inclusive/providing-accessibility-information>
4. `Euan’s Guide`
   use it for lived-experience review evidence and community validation rather than formal certification:
   <https://www.euansguide.com/about-us/>
5. `Changing Places`
   use the national map to verify high-need toilet provision separately from route quality:
   <https://www.changing-places.org/install-toilet>

Important context:

- VisitBritain confirms `AccessibilityGuides.org` closed on `30 June 2024`:
  <https://www.visitbritain.org/accessibilityguidesorg-now-closed>

## Recommended next step

If the objective is a defendable public-facing accessibility comparison between towns:

1. keep `Teignmouth` as the constrained case
2. use `Exmouth` as the positive comparator
3. run a corridor-by-corridor ground audit in all three places with an NRAC consultant or equivalent specialist
4. pair that with disabled-user walkthroughs to capture dropped kerbs, crossing comfort, clutter, gradient feel, and transfer points

That would turn the current MCP-Geo outputs into a practical and evidentially stronger accessibility profile.
