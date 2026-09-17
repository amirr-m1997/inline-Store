"""Build the offline, self-contained MEHRASL prototype. Python 3.9+; stdlib only."""
from __future__ import annotations

import base64
import json
from pathlib import Path


def build(root: Path) -> Path:
    required = ('index.html', 'styles.css', 'catalog-data.js', 'app.js')
    missing = [name for name in required if not (root / name).is_file()]
    if missing:
        raise FileNotFoundError('Missing project files: ' + ', '.join(missing))

    mime_types = {'.svg': 'image/svg+xml', '.png': 'image/png',
                  '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp'}
    assets: dict[str, str] = {}
    for path in sorted((root / 'assets').rglob('*')):
        if not path.is_file() or path.suffix.lower() not in mime_types:
            continue  # Do not include fonts, private data, or unrelated files.
        encoded = base64.b64encode(path.read_bytes()).decode('ascii')
        assets[path.relative_to(root).as_posix()] = (
            f'data:{mime_types[path.suffix.lower()]};base64,{encoded}'
        )

    document = (root / 'index.html').read_text(encoding='utf-8')
    document = document.replace(
        '<link rel="stylesheet" href="styles.css">',
        '<style>\n' + (root / 'styles.css').read_text(encoding='utf-8') + '\n</style>'
    )
    for name, data_uri in assets.items():
        document = document.replace(f'src="{name}"', f'src="{data_uri}"')
        document = document.replace(f'href="{name}"', f'href="{data_uri}"')
    # app.js resolves dynamically created image paths through this optional map.
    data_script = 'window.MEHRASL_ASSETS = ' + json.dumps(assets) + ';\n'
    data_script += (root / 'catalog-data.js').read_text(encoding='utf-8')
    document = document.replace(
        '<script src="catalog-data.js"></script>',
        '<script>\n' + data_script + '\n</script>'
    )
    document = document.replace(
        '<script src="app.js"></script>',
        '<script>\n' + (root / 'app.js').read_text(encoding='utf-8') + '\n</script>'
    )
    output = root / 'MehrAsl_Store_Preview.html'
    output.write_text(document, encoding='utf-8')
    return output


if __name__ == '__main__':
    try:
        target = build(Path(__file__).resolve().parent)
    except (OSError, ValueError) as error:
        raise SystemExit(f'Build failed: {error}') from error
    print(f'Created: {target.name} ({target.stat().st_size:,} bytes)')
