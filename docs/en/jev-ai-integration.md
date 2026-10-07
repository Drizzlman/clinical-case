# Jev AI (TypeSafe): applicability in the Clinical Case Scoring Platform

## Context

Jev is TypeSafe AI's first "System One" model (released 2026-09-15). It is **not an LLM**:
it does not generate text. It takes `state` (text/JSON/array) plus a map of typed questions
and returns typed answers with calibrated probabilities in 70–500 ms. Three primitives:
`noul` (yes/no), `choice` (one of predefined options), `score` (rating on a defined scale).

This document answers whether Jev is useful here and why — primarily in the context of the
"cheap tokens and optimization" idea.

## 4. What Jev can and cannot do here

| System task | Component | Jev | Why |
|---|---|---|---|
| Extract a structured case from raw text (title/description/questions/options) | pipeline | ❌ | This is free-form text generation; Jev generates no text, and `choice`/`score` only work over predefined options/scales |
| Deterministic score computation | backend | ❌ (and unnecessary) | A system invariant is reproducible determinism; Jev is probabilistic |
| Extraction quality assessment | pipeline / harness | ✅ | Verification is Jev's target use case |
| Input gate/classification (is it clinical text, specialty) | pipeline / input | ✅ | `noul` + `choice` over a fixed category list |
| Case prioritization/difficulty | service | ✅ | `score` on a scale |

**Conclusion:** Jev does not replace the system core (extraction + scoring); it augments it
with auxiliary "small decisions".

## 5. Where Jev fits first

1. **Harness judge for extraction quality** — checks/scores output on top of the current
   per-field precision/recall/F1. Verifying other models' outputs is Jev's target use case.
2. **Input gate before extraction**: `is_clinical` (`noul`) + `specialty` (`choice`) — filter
   irrelevant input and route.
3. **Guardrail before `POST /cases`** — validate a case before writing to the DB.
4. **Case prioritization/difficulty** (`score`) — an auxiliary signal for the methodologist.

**Anti-list (not suitable):** replacing the extraction LLM; any step in deterministic scoring;
the user-facing hot path in the backend.

## 6. Pros (facts)

- **Speed:** 70–500 ms versus seconds for an LLM.
- **Price:** $0.042 per 1M input tokens, **output tokens are free**.
- **No response parsing:** typed output, "zero structured-output errors" by construction.
- **Calibrated confidence:** `choice`/`score` carry confidence, `noul` a 0–1 probability;
  thresholds "automate / review" can be built on this.
- **Simple integration:** a single `POST /v1/systemone` endpoint; official Python SDK
  `typesafe-sdk` (async client available, ≥3.10).
- **Multiple questions per call** — answered in parallel against one `state`.

**On "cheap tokens":** Jev's low price is a direct consequence of it **not performing
generation** (it picks from predefined answers rather than writing text). So the savings do
not carry over to the main workload — extracting a case from text, which needs an LLM
generator. Jev makes only the auxiliary decisions (verification, classification, scoring)
cheaper, and there the savings are real.

## 7. Cons and risks

| Risk | What it is | Mitigation |
|---|---|---|
| **Russian language** | The system's data (raw.txt, golden) is Russian; non-English is officially stated to possibly perform worse | Test on the golden set before adopting |
| **Cloud only** | No self-hosting; inference only at the vendor | For clinical data, account for egress and data policy |
| **Privacy** | Raw clinical text leaves to a third party; free tier may be used for training | Do not send real data to the free tier; key only via env / Secret Manager |
| **Maturity/access** | Early access / waitlist; the API was overloaded at launch | Do not put it on the critical path; provide a fallback |
| **Calibration ≠ guarantee** | Official docs require thresholds and human review | Treat it as a signal, not the truth |
| **Untrusted sites** | Many unofficial "resellers" surround Jev | Use only `typesafe.ai` and the official SDK |
| **Closedness** | Model architecture is undisclosed; the vendor is young | Treat it as an external dependency with risk |

## Conclusion

Jev is useful as a cheap, fast layer for verification/classification/scoring around the
system, but **not** as a replacement for LLM extraction and **not** as a replacement for
deterministic score computation. Its value lies in auxiliary decisions, not in saving on the
main extraction workload.
