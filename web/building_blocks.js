/* Lokale adviesregels. De namen en relaties komen uit de broncatalogus. */
(function(root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.BuildingBlockAdvice = factory();
})(globalThis, function() {
  'use strict';
  function escapeRegex(value) { return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }
  function recommend(catalogue, contexts) {
    return catalogue.abbs.map(block => {
      const evidence = [];
      for (const context of contexts) {
        const text = context.text.toLowerCase();
        const terms = block.terms.filter(term => new RegExp('(?<![\\p{L}\\p{N}_])' + escapeRegex(term.toLowerCase()) + '[\\p{L}\\p{N}_]*', 'u').test(text));
        if (!terms.length) continue;
        const first = new RegExp('(?<![\\p{L}\\p{N}_])' + escapeRegex(terms[0].toLowerCase()) + '[\\p{L}\\p{N}_]*', 'u').exec(text);
        evidence.push({source: context.source, terms,
          excerpt: context.text.slice(Math.max(0, first.index - 45), first.index + first[0].length + 100).trim()});
      }
      return {id: block.id, evidence, score: evidence.reduce((total, match) => total + match.terms.length, 0)};
    }).filter(item => item.evidence.length).sort((a, b) => b.score - a.score);
  }
  function selection(catalogue, advice, overrides) {
    const recommended = new Map(advice.map(item => [item.id, item]));
    const abbIds = new Set(catalogue.abbs.filter(block => overrides[block.id] ?? recommended.has(block.id)).map(block => block.id));
    const related = new Set(catalogue.abbs.filter(block => abbIds.has(block.id)).flatMap(block => block.sbb_ids));
    const abbById = new Map(catalogue.abbs.map(block => [block.id, block]));
    const selected = [];
    for (const block of [...catalogue.abbs, ...catalogue.sbbs]) {
      const defaultValue = block.type === 'ABB' ? abbIds.has(block.id) : related.has(block.id);
      if (!(overrides[block.id] ?? defaultValue)) continue;
      const parents = (block.abb_ids || []).filter(id => abbIds.has(id)).map(id => abbById.get(id));
      const mappings = parents.length ? parents : (block.abb_ids || []).map(id => abbById.get(id));
      const evidence = block.type === 'ABB' ? recommended.get(block.id)?.evidence || [] : parents.flatMap(parent => recommended.get(parent.id)?.evidence || []);
      selected.push({id: block.id, type: block.type, name: block.name, layer: block.layer,
        manual: Object.hasOwn(overrides, block.id), evidence,
        mappings: mappings.map(parent => ({id:parent.id,name:parent.name,quote:parent.quote,line:parent.line,section:parent.section})),
        abb_ids: block.abb_ids || [], quote: block.quote || null, line: block.line || null, section: block.section || null});
    }
    return {status: 'Geadviseerd gebruik — te beoordelen door de architect', method: catalogue.method,
      catalogue_source: catalogue.source, selected, recommendations: advice, overrides: {...overrides}};
  }
  return {recommend, selection};
});
