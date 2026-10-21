# Changelog

## 0.2.0 — 2026-10-21

- Preserve every original column dtype in `propagate_groups`, including nullable,
  categorical, and timezone-aware columns.
- Render integral floating-point header pieces as `2024` rather than `2024.0`;
  retain fractional numbers, infinities, and original string headings.
- Prevent subheader prefixes from ending inside a Unicode word: `Region` no
  longer consumes `Regional total`.
- Add `match_mode="full"` to `extract_subheaders` and `untangle` for explicit
  whole-field matching with one capture. The default prefix mode still supports
  documented rules such as `^REGION:`. Use a full capture rule when trailing
  text must remain a data row.

## 0.1.0 — 2026-10-21

- Initial independently installable release of untanglepy.
- Typed public API, original implementations, executable examples, tests, and reproducible benchmarks.

Publication state is recorded in RELEASE.md; this version number alone does not imply a PyPI upload.
