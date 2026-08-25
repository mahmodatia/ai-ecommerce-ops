# Branding

The interface uses one replaceable logo asset:

```text
frontend/assets/logo.svg
```

Recommended source: square SVG with a transparent background. A simple mark works best because the UI also displays it at favicon and compact sidebar sizes.

Brand text is configured in:

```text
frontend/js/brand.js
```

Current product name: `AI Ops`
Current descriptor: `E-commerce Automation`

To use PNG/WebP instead, place the file under `frontend/assets/` and change `logoPath` once in `brand.js`.
