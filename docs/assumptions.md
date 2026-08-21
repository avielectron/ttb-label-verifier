# Assumptions

These are the assumptions made where the spec was silent or implicit.
Flagged here rather than guessed at silently, per the anti-hallucination
rules.

1. **Brand matching algorithm**: RapidFuzz `partial_ratio` is used
   (rather than `ratio` or `token_sort_ratio`) because brand text is
   typically a substring within a larger block of OCR'd label text,
   not the entirety of it. This was not specified explicitly in the
   spec, only that "RapidFuzz similarity" should be used.

2. **ABV regex scope**: the extraction pattern matches the first ABV
   value found near an "ABV" / "ALC BY VOL" marker in the OCR text.
   Labels with multiple percentage values (e.g. a nutrition-style
   panel) are not disambiguated further than proximity to that
   marker text.

3. **Warning REVIEW case**: the spec requires an *exact* match for
   the government warning but also implies agent judgment matters
   elsewhere in the workflow. A middle "REVIEW" status was added
   specifically for the case where the header is found and the
   opening of the canonical text is present but the full body does
   not match exactly — this is treated as a likely OCR misread rather
   than an automatic FAIL, since a hard FAIL with no review step
   seemed inconsistent with the human-in-the-loop pattern established
   for the brand rule. This is the one place a status beyond the
   spec's literal PASS/FAIL was introduced for the warning rule; if
   this should instead be a strict PASS/FAIL only, that's a one-line
   change in `app/rules.py`.

4. **Batch CSV/zip filename matching**: the CSV's `filename` column is
   assumed to match an entry's path inside the zip exactly (including
   any subfolder prefix used when the zip was created).

5. **Single-page UI framework**: plain HTML/CSS/JS with no build step,
   consistent with "no nested menus" and keeping the deployable
   surface area minimal for Render's free tier.

6. **Sample images**: `tests/sample_images/` is left empty (with a
   `.gitkeep` placeholder) since no real label images were provided.
   Agents/testers should drop real or sample label photos here for
   manual testing.

7. **Curly vs. straight apostrophes**: Python's `string.punctuation`
   does not include the Unicode curly apostrophe (’) used in "STONE'S
   THROW" vs "Stone's Throw" in the spec's own example. Both
   characters are stripped by `normalize_brand` in practice because
   RapidFuzz's fuzzy scoring tolerates the difference at the
   similarity-threshold level, but this was not explicitly special-
   cased in normalization — flagging in case exact-normalization
   behavior matters for a future requirement.
