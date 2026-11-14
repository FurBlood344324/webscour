# webscour on npm

This package exists so that an agent can find the skill by name:

```bash
npx skills add webscour
pi install npm:webscour
```

It carries `SKILL.md` and its references, and a `wsc` shim. **The tool itself is Python**, standard
library only, and npm does not install it. Install that first:

```bash
pipx install webscour
# or: uv tool install webscour
# or: curl -LsSf https://wsc.ashina.live/install.sh | sh
```

Then `wsc` works normally, and `npx webscour <args>` forwards to it.

If you run the shim before installing the tool it prints the three commands above and exits 1. It
never downloads or installs anything by itself: a package that fetches a binary during install is
the thing this project argues against.

- Source, docs and the full README: https://github.com/FurBlood344324/webscour
- PyPI: https://pypi.org/project/webscour/
- Licence: MIT
