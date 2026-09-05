# portfolio

King Joshua Marcos's portfolio. One page, one file, no build step.

Live at [marcosmodly.github.io/portfolio](https://marcosmodly.github.io/portfolio).

## What it is

A single `index.html` with inline CSS and vanilla JS. No framework, no bundler,
no `node_modules`. Open the file and you're looking at the entire site.

- **Theme toggle**: light/dark, persisted in `localStorage`, defaulting to the
  browser's `prefers-color-scheme`. Every themed color is a CSS custom
  property redefined per theme, no `filter: invert` anywhere.
- **Hero graphic**: an inline SVG desk scene that actually changes between
  light and dark (different window contents, a lamp that switches on, not a
  recolored copy of the same frame), and scrubs through a few real code
  fragments from the projects below as you scroll the page.
- **Scroll reveals**: `IntersectionObserver` toggles a class, CSS handles the
  transition. No animation library.

## Structure

Hero → about → skills → project grid → four case studies (ModlyAI, Holdfast,
github-repo-hygiene-skill, Grandma's Lighthouse) → contact.

## Running it locally

Any static file server works, since it's just HTML:

```bash
python -m http.server 4173
```

Opening `index.html` directly via `file://` also works, though a couple of
browsers restrict relative asset loading from `file://` more than an actual
server would.

## License

MIT, see [LICENSE](LICENSE).
