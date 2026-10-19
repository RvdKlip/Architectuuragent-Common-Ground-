"""Bouw het deelbare HTML-bestand met lokale afbeelding, code en PDF-lezer."""
from pathlib import Path
import base64

ROOT = Path(__file__).resolve().parents[1]


def build():
    template = (ROOT/'web/index.template.html').read_text(encoding='utf-8')
    replacements = {
        '__ROTTERDAM_LOGO__': 'data:image/svg+xml;base64,'+base64.b64encode((ROOT/'assets/rotterdam/logo.svg').read_bytes()).decode(),
        '__ARCHITECTURE_ARTWORK__': 'data:image/png;base64,'+base64.b64encode((ROOT/'assets/architecture-hero.png').read_bytes()).decode(),
        '__PDFJS_MAIN__': base64.b64encode((ROOT/'assets/vendor/pdfjs/pdf.mjs').read_bytes()).decode(),
        '__PDFJS_WORKER__': base64.b64encode((ROOT/'assets/vendor/pdfjs/pdf.worker.mjs').read_bytes()).decode(),
        '__APP_JS__': '\n'.join((ROOT/'web'/filename).read_text(encoding='utf-8')
                               for filename in ['document_reader.js', 'app.js', 'epics.js', 'psa.js']).replace('</script', '<\\/script'),
        '__PDFJS_LICENSE__': (ROOT/'assets/vendor/pdfjs/LICENSE').read_text(encoding='utf-8').replace('&', '&amp;').replace('<', '&lt;'),
        '__HOUSE_STYLES__': (ROOT/'assets/housestyles.json').read_text(encoding='utf-8'),
        '__JSPDF_LIBRARY__': '\n'.join(line.rstrip() for line in (ROOT/'assets/vendor/jspdf/jspdf.umd.min.js').read_text(encoding='utf-8').splitlines()).replace('</script', '<\\/script'),
        '__JSPDF_LICENSE__': (ROOT/'assets/vendor/jspdf/LICENSE').read_text(encoding='utf-8').replace('&', '&amp;').replace('<', '&lt;'),
    }
    for placeholder, content in replacements.items():
        if placeholder not in template:
            raise ValueError('Ontbrekende placeholder: '+placeholder)
        template = template.replace(placeholder, content)
    (ROOT/'index.html').write_text(template, encoding='utf-8')
    print('index.html gebouwd:', len(template.encode('utf-8')), 'bytes')


if __name__ == '__main__':
    build()
