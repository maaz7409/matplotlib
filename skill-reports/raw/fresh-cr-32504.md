# /code-review high on matplotlib PR #32504 (fresh set, 2026-11-04)

model claude-opus-5-5, effort high · wall 56s · cost $0.38

---

8 findings, most severe first:

1. `lib/matplotlib/__init__.py:506`: The new pdflatex version regex `pdfTeX .*-(\d+\.\d+\.\d+)` only matches TeX Live-style banners. When it does not match, `_get_executable_info('pdflatex')` raises ExecutableNotFoundError, and test_rcupdate calls it with no guard, so the test errors out instead of running or skipping.

   Failure scenario: On Windows with MiKTeX, `pdflatex -version` prints `MiKTeX-pdfTeX 4.19 (MiKTeX 24.4)`. There is no `-X.Y.Z` after `pdfTeX `, so impl() raises ExecutableNotFoundError. needs_pgf_pdflatex passed (pdflatex works), and the call at test_backend_pgf.py:162 then turns test_rcupdate into an ERROR. The same happens for any other pdfTeX distribution or banner format, including a future one with no three-part `-1.40.x` suffix.

2. `lib/matplotlib/tests/baseline_images/test_backend_pgf/pgf_rcupdate2.pdf:1`: The baseline was regenerated with pdfTeX 1.40.26 (TeX Live 2024), replacing a 1.40.22 baseline. The test is only compared for versions ≤1.40.26, so environments with older pdfTeX are now checked against a baseline made by a different engine version, with tolerance 0.

   Failure scenario: On CI or a developer machine with TeX Live 2022 (pdfTeX 1.40.22, which produced the old baseline), the xfail does not apply, so compare_figure('pgf_rcupdate2.pdf', tol=0) runs against the 1.40.26 output. Any rendering difference between 1.40.22 and 1.40.26 now fails a test that used to pass. In practice the only version guaranteed to pass is exactly 1.40.26.

3. `lib/matplotlib/tests/baseline_images/test_backend_pgf/pgf_rcupdate2.pdf:1`: The committed baseline was produced from a dirty local dev build (Creator/Producer `v3.12.0.dev810+g1359e47de.d20261103`), not from a clean checkout of this branch.

   Failure scenario: The `.dYYYYMMDD` suffix means the working tree had uncommitted changes when the baseline was made. If any of those changes affected PGF output (for example, unmerged hatch edits), the baseline holds output that this PR's code cannot reproduce. Clean checkouts with pdfTeX ≤1.40.26 then fail the image comparison.

4. `lib/matplotlib/tests/test_backend_pgf.py:161`: The pdfTeX-version xfail runs before the existing `sfmath`/`ucs` package skip check. Environments missing those packages now report XFAIL instead of SKIP.

   Failure scenario: Take a system with pdfTeX 1.40.27 and no ucs.sty. Before this change the second rc_set called pytest.skip('needs ucs.sty'). Now pytest.xfail fires first. The result is an XFAIL that claims a pdfTeX-version incompatibility when the real reason is a missing package, which hides the actual environment problem.

5. `lib/matplotlib/tests/test_backend_pgf.py:161`: pytest.xfail is called inside a loop that runs both rc_sets in one test. On new pdfTeX the whole test becomes XFAIL, and the imperative xfail cannot become strict or XPASS if the problem is later fixed.

   Failure scenario: With pdfTeX >1.40.26, the first rc_set (xelatex) still runs and is compared. If that comparison regresses, the test reports a failure. If it passes, the test reports XFAIL, which blends a real pass with an expected failure. Separately, if a future pdfTeX or a matplotlib fix makes pgf_rcupdate2 match again, nobody is told (no XPASS) and the comparison stays disabled indefinitely. Parametrizing over the rc_sets and using `pytest.mark.xfail(condition, strict=True)` on the second case avoids both problems.

6. `lib/matplotlib/tests/test_backend_pgf.py:162`: The xfail only hides the version-dependent output instead of fixing the root cause. A version-conditional tolerance or a regenerated baseline would keep the test meaningful on current TeX distributions.

   Failure scenario: Most current TeX Live installs (2025 and later, pdfTeX ≥1.40.27) never run the pdflatex rcupdate comparison again. Real regressions in PGF hatch color or linewidth handling for pdflatex (what this rc_set was added to cover) go undetected on those systems. Something like `tol = 13.2 if pdftex_version > ...` already exists in this test for old Ghostscript and would keep coverage.

7. `lib/matplotlib/__init__.py:377`: "pdflatex" was added as a supported name in `_get_executable_info`, but the docstring's list of supported executables was not updated.

   Failure scenario: The docstring still says supported values are "dvipng", "gs", "inkscape", "magick", "pdftocairo", "pdftops". A maintainer reading it will think `_get_executable_info('pdflatex')` raises ValueError, and the documented contract no longer matches the code.

8. `lib/matplotlib/tests/test_backend_pgf.py:162`: This test-only version check adds a new executable branch to shared library code in `matplotlib/__init__.py` (`_get_executable_info`), even though the test module already detects pdflatex through `_check_for_pgf`.

   Failure scenario: The library's `_get_executable_info` dispatch now carries a pdflatex case used by a single test. It also has a weaker regex than the other entries, as finding 1 shows. A small helper local to the test, or a module-level `_pdftex_version` computed once with try/except, would keep the fragile parsing out of the public-ish API.
