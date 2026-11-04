# /code-review high on matplotlib PR #32537 (fresh set, 2026-11-04)

model claude-opus-5-5, effort high · wall 44s · cost $0.30

---

The PR adds one file, `right_to_left_text.py`, at the repo root (48 lines). No CLAUDE.md applies anywhere in the repo, so the conventions angle found nothing, and I didn't run a verify pass. The most important finding is the first one: matplotlib already lays out text through libraqm, which does bidi reordering itself (`src/ft2font.cpp` around lines 340–376). Reversing word order by hand on top of that scrambles the text instead of fixing it.

10 findings, most severe first:

1. `right_to_left_text.py:32`: reverse_mixed_text reverses word groups by hand, but matplotlib already shapes and reorders text through libraqm (src/ft2font.cpp, default auto-detected direction), so the text gets reordered twice.

   Failure scenario: text_direction('rtl', "Python اور matplotlib میں اردو؟") returns "میں اردو؟ matplotlib اور Python". Passing that to fig.text runs it through raqm's bidi algorithm again, so a sentence that rendered correctly before now shows its Latin and Arabic runs in the wrong order.

2. `right_to_left_text.py:22`: Consecutive Arabic/Urdu words are joined in logical order while the group order is reversed, so the words inside an RTL phrase keep the wrong order for the visual-order output this function is trying to build.

   Failure scenario: "میں اردو؟" stays as "میں اردو؟" inside the reversed string. A purely left-to-right renderer, the case the reversal is meant for, then shows میں to the left of اردو, which flips the meaning of the RTL phrase. The characters inside each word are not reversed either.

3. `right_to_left_text.py:8`: contains_arabic only matches U+0600–U+06FF, so other RTL characters are classed as LTR.

   Failure scenario: Hebrew (U+0590–U+05FF), Arabic Supplement (U+0750–U+077F), Arabic Extended-A (U+08A0–U+08FF) and the presentation forms (U+FB50–U+FDFF, U+FE70–U+FEFF) are not treated as RTL. For example, a Hebrew sentence passed with 'rtl' is split into single-word groups and fully reversed word by word.

4. `right_to_left_text.py:16`: Neutral tokens such as numbers or punctuation between RTL words count as LTR, which breaks one RTL phrase into several groups that are then reversed.

   Failure scenario: "اردو 2024 میں" gives three groups ['اردو', '2024', 'میں'], reversed to "میں 2024 اردو". A standalone hyphen or emoji between Urdu words has the same effect. The PR's own promise that phrases are kept together does not hold.

5. `right_to_left_text.py:11`: text.split() with no arguments collapses all whitespace, so newlines, tabs and repeated spaces are lost.

   Failure scenario: text_direction('rtl', "سطر اول\nline two") returns a single line, and multi-line text labels are merged into one. Even with 'ltr' and 'rtl' behaving consistently otherwise, the whitespace in the 'rtl' result differs from the input.

6. `right_to_left_text.py:38`: text_direction falls through and returns None for any direction other than 'ltr' or 'rtl' instead of raising ValueError.

   Failure scenario: text_direction('RTL', s) or text_direction('auto', s) returns None. fig.text(..., None) then draws the string 'None' or fails later, far from the actual mistake.

7. `right_to_left_text.py:45`: The file runs figure creation and savefig at module level, sits in the repo root outside lib/, and is never wired into the package, tests or docs.

   Failure scenario: Importing or collecting this file writes repro_direction.png into the current directory, and that file isn't covered by .gitignore. Users can't import the helpers from matplotlib. This looks like a local repro script committed by mistake.

8. `right_to_left_text.py:46`: The demo never calls text_direction or reverse_mixed_text, so the new functions are dead code and are never exercised or checked.

   Failure scenario: Both fig.text calls pass the raw text, with or without an RLM prefix. Nothing tests the new functions, so the bugs above go unnoticed.

9. `right_to_left_text.py:47`: The RLM mark is embedded as an invisible literal character instead of the escape "\u200f".

   Failure scenario: Reviewers and editors see what looks like an empty string "" + text. The mark is easy to delete by accident or to lose when the file's encoding is normalized, and the intent can't be read from the source.

10. `right_to_left_text.py:7`: The file breaks the repo's ruff rules selected in pyproject.toml: W291, E302 and E265.

    Failure scenario: Line 2 "import re " has trailing whitespace (W291). The defs at lines 7, 10 and 38 have only one blank line before them (E302). The comments at lines 6, 17, 20, 31, 36 and 37 start with '#' and no space (E265). The ruff/pre-commit lint fails on this PR.
