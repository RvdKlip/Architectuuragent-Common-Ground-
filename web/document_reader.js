/* Documenten blijven lokaal; PDF.js en zijn worker zijn ingebed in index.html. */
const DocumentReader = (() => {
  const MAX_BYTES = 20000000;
  const MAX_TEXT = 1000000;
  let pdfModule;
  function assertText(text) {
    if (text.length > MAX_TEXT) throw Error('Meer dan 1.000.000 tekens: inhoud niet gebruikt voor advies.');
    if (text.replace(/\W/g, '').length < 20) throw Error('Te weinig uitleesbare tekst; scans hebben OCR nodig.');
    return text;
  }
  function embeddedModule(id) {
    const bytes = Uint8Array.from(atob(document.getElementById(id).textContent.trim()), char => char.charCodeAt(0));
    return URL.createObjectURL(new Blob([bytes], {type: 'text/javascript'}));
  }
  async function pdfLibrary() {
    if (!pdfModule) pdfModule = (async () => {
      const module = await import(embeddedModule('pdfjs-main'));
      module.GlobalWorkerOptions.workerSrc = embeddedModule('pdfjs-worker');
      return module;
    })();
    return pdfModule;
  }
  async function readPdf(buffer, name) {
    const library = await pdfLibrary();
    const task = library.getDocument({data: new Uint8Array(buffer), isEvalSupported: false,
      useSystemFonts: true, useWasm: false, useWorkerFetch: false, enableXfa: false});
    let pdf;
    try {
      pdf = await task.promise;
      if (pdf.numPages > 300) throw Error('Meer dan 300 pagina’s: inhoud niet gebruikt voor advies.');
      const contexts = [], warnings = [];
      let length = 0;
      for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber++) {
        const page = await pdf.getPage(pageNumber);
        const content = await page.getTextContent();
        const text = content.items.map(item => item.str || '').join(' ');
        length += text.length;
        if (length > MAX_TEXT) throw Error('Te veel tekst: inhoud niet gebruikt voor advies.');
        if (!text.trim()) warnings.push('Pagina '+pageNumber+' heeft geen uitleesbare tekst; afbeeldingen zijn niet geanalyseerd.');
        else contexts.push({source: name+' p.'+pageNumber, text});
        page.cleanup();
      }
      assertText(contexts.map(context => context.text).join('\n'));
      return {contexts, warnings};
    } finally {
      await task.destroy();
    }
  }
  async function inflate(bytes, method) {
    if (method === 0) return bytes;
    if (method !== 8 || typeof DecompressionStream === 'undefined') throw Error('Deze browser kan dit Word-bestand niet uitpakken. Gebruik de Python-app.');
    const reader = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('deflate-raw')).getReader();
    let total = 0;
    const chunks = [];
    try {
      while (true) {
        const {done, value} = await reader.read();
        if (done) break;
        total += value.length;
        if (total > MAX_BYTES) throw Error('Uitgepakte Word-inhoud is groter dan 20 MB.');
        chunks.push(value);
      }
    } catch (error) {
      await reader.cancel();
      throw error;
    }
    const result = new Uint8Array(total);
    let offset = 0;
    for (const chunk of chunks) { result.set(chunk, offset); offset += chunk.length; }
    return result;
  }
  async function readDocx(buffer, name) {
    const view = new DataView(buffer), bytes = new Uint8Array(buffer);
    let end = -1;
    for (let i = buffer.byteLength - 22; i >= Math.max(0, buffer.byteLength - 65557); i--) {
      if (view.getUint32(i, true) === 0x06054b50) { end = i; break; }
    }
    if (end < 0) throw Error('Ongeldig DOCX-bestand.');
    const entries = view.getUint16(end + 10, true);
    let cursor = view.getUint32(end + 16, true), total = 0;
    const texts = [];
    for (let index = 0; index < entries; index++) {
      if (cursor + 46 > bytes.length || view.getUint32(cursor, true) !== 0x02014b50) throw Error('Ongeldige Word-archiefstructuur.');
      const flags = view.getUint16(cursor + 8, true), method = view.getUint16(cursor + 10, true);
      const compressed = view.getUint32(cursor + 20, true), uncompressed = view.getUint32(cursor + 24, true);
      const filenameLength = view.getUint16(cursor + 28, true), extraLength = view.getUint16(cursor + 30, true), commentLength = view.getUint16(cursor + 32, true);
      const local = view.getUint32(cursor + 42, true);
      const filename = new TextDecoder().decode(bytes.slice(cursor + 46, cursor + 46 + filenameLength));
      cursor += 46 + filenameLength + extraLength + commentLength;
      if (!/^word\/(document|header\d+|footer\d+)\.xml$/.test(filename)) continue;
      if (flags & 1) throw Error('Versleutelde Word-bestanden worden niet gelezen.');
      if (uncompressed > MAX_BYTES || local + 30 > bytes.length || view.getUint32(local, true) !== 0x04034b50) throw Error('Ongeldige of te grote Word-inhoud.');
      const start = local + 30 + view.getUint16(local + 26, true) + view.getUint16(local + 28, true);
      if (start + compressed > bytes.length) throw Error('Onvolledig Word-bestand.');
      const xmlBytes = await inflate(bytes.slice(start, start + compressed), method);
      total += xmlBytes.length;
      if (total > MAX_BYTES) throw Error('Uitgepakte Word-inhoud is groter dan 20 MB.');
      const xmlText = new TextDecoder('utf-8', {fatal: true}).decode(xmlBytes);
      if (/<!DOCTYPE/i.test(xmlText)) throw Error('Onverwachte XML-documentdefinitie.');
      const xml = new DOMParser().parseFromString(xmlText, 'application/xml');
      if (xml.getElementsByTagName('parsererror').length) throw Error('Ongeldige XML in Word-bestand.');
      const paragraphs = Array.from(xml.getElementsByTagNameNS('*', 'p'));
      texts.push(paragraphs.map(paragraph => Array.from(paragraph.getElementsByTagNameNS('*', 't')).map(node => node.textContent).join('')).join('\n'));
    }
    const text = assertText(texts.join('\n'));
    return {contexts: [{source: name, text}], warnings: []};
  }
  async function read(file) {
    if (file.size > MAX_BYTES) throw Error('Groter dan 20 MB: inhoud niet gebruikt voor advies.');
    const extension = file.name.split('.').pop().toLowerCase();
    const buffer = await file.arrayBuffer();
    if (extension === 'pdf') return readPdf(buffer, file.name);
    if (extension === 'docx') return readDocx(buffer, file.name);
    if (extension === 'txt' || extension === 'md') {
      const text = assertText(new TextDecoder('utf-8', {fatal: true}).decode(buffer));
      return {contexts: [{source: file.name, text}], warnings: []};
    }
    throw Error('Dit bestandstype wordt niet gelezen.');
  }
  return {read};
})();
