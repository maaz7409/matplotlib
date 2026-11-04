# /code-review high on matplotlib PR #32515 (fresh set, 2026-11-04)

model claude-opus-5-5, effort high · wall 61s · cost $0.42

---

6 findings, most severe first:

1. `lib/matplotlib/cbook.py:1292`: The fix covers masked values only. A column whose values are all NaN, or one that becomes NaN-only once masked points are removed, still skips the empty-data branch and runs the statistics on NaNs. violin_stats handles this by dropping non-finite values through delete_masked_points.

   Failure scenario: boxplot_stats(np.ma.masked_array([np.nan, 5.0], mask=[False, True])) leaves x=[nan], so len(x)==1. np.mean and np.percentile then return NaN with RuntimeWarnings, and the fliers/whisker comparisons run on NaN. An equivalent fully-masked column takes the clean empty path instead, so the two cases behave differently and the root cause (non-usable data reaching the stats) is only partly fixed.

2. `lib/matplotlib/tests/test_cbook.py:185`: The new test only checks a 1-D, fully-masked array. It does not cover the realistic case of a 2-D masked array where one column is fully masked and the others are not, and it does not check Axes.boxplot rendering.

   Failure scenario: If the _reshape_2D column path (np.reshape(x, -1) on masked columns) or the mask handling for later columns regressed, for example by dropping the mask on 2-D input, this test would still pass. Meanwhile boxplot(np.ma.masked_array([[1,2],[3,4]], mask=[[1,0],[1,0]])) would raise IndexError from np.percentile again.

3. `lib/matplotlib/tests/test_cbook.py:192`: The test builds its expected values by calling boxplot_stats([]), the same function under test, and only loops over the keys present in that expected dict.

   Failure scenario: If a change to the empty-case branch (for example a wrong 'fliers' value or a missing key) affects both calls the same way, the test still passes. Any extra or stray keys in the all-masked result are never checked. Asserting literal NaN values and an empty fliers array would catch real regressions.

4. `lib/matplotlib/cbook.py:1286`: np.ma.asarray(x).data[~x.mask].ravel() re-implements MaskedArray.compressed(), and with nomask it relies on indexing by a scalar boolean (data[True]), which adds a new axis that ravel then removes.

   Failure scenario: The extra-dimension-then-ravel trick is hard to follow now that this line decides whether the empty branch runs. `x = np.ma.asarray(x).compressed()` does the same job in one clear call and returns a 1-D array for both masked and unmasked input.

5. `lib/matplotlib/cbook.py:1285`: The comment 'up-convert to an array, just to be safe' is now misleading. After this PR the conversion is required: the len(x)==0 check below depends on masked values already being removed.

   Failure scenario: A future refactor that trusts the comment could move or remove this 'optional' conversion back below the empty check. That would silently bring back the IndexError from np.percentile on all-masked columns.

6. `lib/matplotlib/cbook.py:1290`: This is a user-visible behavior change with no doc/api/next_api_changes/behavior entry. Fully-masked datasets passed to boxplot/boxplot_stats used to raise IndexError and now return NaN stats and draw an empty box.

   Failure scenario: Code that relied on the old exception to detect fully-masked inputs now gets NaN stats with no error. The repo has a precedent for documenting this kind of change: doc/api/next_api_changes/behavior/violinplot_empty.rst.

I ran no tests: matplotlib and pytest are not installed in this environment. A quick numpy check confirmed that before this PR, `np.percentile` on an empty array raised `IndexError`, so all-masked input used to crash. The fix itself is correct: removing masked values before the empty check works for lists, empty arrays, unmasked arrays and object arrays.

No CLAUDE.md applies to these files, so the conventions angle has no findings.
