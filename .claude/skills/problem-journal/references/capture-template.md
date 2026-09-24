# Problem Journal — capture-file template (canonical)

The one canonical copy of the Capture-mode file template; `SKILL.md` step 3 points here. The Status / Steps / Resolution field rules stay in `SKILL.md`.

```markdown
---
tags:
  - error
author:
  - jacgit18
Description: "<one-sentence description>"
Comments:
Purpose: This documentation discusses this error in this context.
Status: Capture
Started:
EditDate: <today, YYYY-MM-DD>
Relates:
Peer Reviewed:
dg-publish:
---
## Error Details
```dataviewjs
const { Description } = dv.current();

dv.header(3, "Description");
dv.paragraph(
  `${Description}`,
);
```

### Steps to Reproduce

1. `[Step 1]`

### Expected Behavior

`[Describe what the expected behavior should be.]`

### Actual Behavior

`[Describe the actual behavior observed during the error.]`

## Environment

- Operating System: `[Enter OS or Environment]`
- Software Version: `[Enter Software Version]`
- Relevant Settings/Configuration: `[Specify any relevant settings or configuration]`

## Error Messages

<the actual error text/stack trace, verbatim>

## Screenshots

N/A (text-only session)

## Additional Notes

`[Add any additional notes or context that might be helpful.]`

## Resolution Steps

`[Document steps taken or proposed resolutions.]` — leave as-is if not yet resolved.

## Related Issues/References

`[Link to any related issues or external references.]`
```
