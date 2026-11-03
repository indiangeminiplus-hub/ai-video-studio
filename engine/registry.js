// Shared registries for style packs (loaded first). A pack file in engine/packs/ adds:
//   MODULES (scene renderers), CAPTION_STYLES[name] = (caption, t) => html, and a PACKS entry
//   { id, name, icon, desc, caption, items:[{type,label,make:T=>scene}], recipe?:ctx=>({scenes,caption_style,music}) }
// so AI Video Studio can list its graphics and build a starter edit. Spec: references/packs.md.
window.PACKS = window.PACKS || [];
window.CAPTION_STYLES = window.CAPTION_STYLES || {};
// Brand kit: timeline.brand overrides these (colours, fonts, logo, contact) for every pack.
function BR() {
  return {
    primary: '#FF5A36', accent: '#FFD84A', dark: '#111214', light: '#FFFFFF', muted: '#A7A9B0',
    font: 'var(--sans)', disp: 'var(--disp)', logo: '', name: '', handle: '', phone: '', website: '',
    ...((typeof TL !== 'undefined' && TL && TL.brand) || {}),
  };
}
// Common helpers for packs.
const cidOf = o => (o && o.cid ? ` data-cid="${o.cid}"` : '');
const fadeIO = (t, t0, t1, din = .3, dout = .25) => clamp(prog(t, t0, din)) * (t1 == null ? 1 : 1 - clamp(prog(t, t1 - dout, dout)));
