"""Trace Agent .docx validators.

`schema_validator` checks the file is a syntactically valid .docx with a
recognizable internal structure. `spot_checker` extracts the rendered
text via docx2txt and confirms every section from the outline is
present. Failures from either validator feed the Trace Agent repair
loop (step 12)."""
