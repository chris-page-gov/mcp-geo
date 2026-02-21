# assurance-checklist.md

## One-page assurance questions (for non-technical leads)

### A) Purpose, benefit, and scope

* What **public value** does this deliver, and for whom?
* What is the **question family** we are committing to answer (and what is explicitly out of scope)?
* Who is the **service owner** (accountability), and who owns each dataset?

### B) Data protection and legal basis (when personal data is involved)

* Are we processing personal data? If yes, what is the lawful basis and how do we evidence minimisation/purpose limitation? ([ICO][11])
* Have we done a DPIA (or equivalent) proportionate to risk?
* What is the retention policy for prompts, logs, and outputs?

### C) Security and operational resilience

* Have we followed secure-by-design lifecycle guidance (design → deployment → operations), including monitoring and incident management? ([NCSC][12])
* What are the controls against common LLM app risks (prompt injection, insecure output handling)? ([owasp.org][17])
* Is access controlled at the **capability** boundary (not just the dataset boundary)?

### D) Governance model (Five Safes as a practical lens)

* **Safe Projects:** is the use appropriate, approved, and time-bounded?
* **Safe People:** who can use it, and what training/terms apply?
* **Safe Settings:** where does it run; how is access constrained?
* **Safe Data:** what minimisation, de-identification, and sensitivity handling applies?
* **Safe Outputs:** what checking prevents disclosure in results? ([GOV.UK][16])

### E) Transparency and accountability

* Does this constitute an “algorithmic tool” that should have an ATRS record (or similar transparency artefact)? ([GOV.UK][15])
* Can we show: inputs → transformations → outputs → provenance, for a sample of real queries? ([w3.org][7])

### F) Quality, testing, and “trust signals”

* What benchmark questions do we test on every release (regression suite)?
* Do answers carry: sources, assumptions, uncertainty, and limitations?
* What does “fail safe” look like (e.g., refuse + signpost + log)?
