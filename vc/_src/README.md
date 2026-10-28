# VC landing pages

One unlisted page per VC, served at `/Portfolio/vc/<slug>/`. Pages carry `noindex, nofollow` and aren't linked from the main site.

- `data/_profile.json`: my shared profile (links, stats, track record, engagement formats).
- `data/<slug>.json`: one file per VC (facts, summary, reasons, VC-level scores, companies with six 0–5 scores and a "where I'd help" line).
- `build.py`: generates `vc/<slug>/index.html` from the data. Run from the repo root:

```
python3 vc/_src/build.py
```

Company score = sum of the six dimensions / 30 × 100. Strong (green) 70+, medium (orange) 50–69, low (yellow) under 50.
This folder starts with an underscore, so GitHub Pages (Jekyll) doesn't publish it.
