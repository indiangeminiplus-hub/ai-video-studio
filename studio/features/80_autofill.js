// Rail panel "Tự động" (references/autofill.md): one click = automatic b-roll (scripts/auto_broll.mjs) + richer sound
// (scripts/auto_sfx.py --level, mood music per section). Server: studio/routes/80_autofill.mjs. Only items marked _auto are
// replaced on a re-run; what you added or edited stays. Every run is one undo step (⌘Z) and a history snapshot.
'use strict';
(() => {
  const S = Studio, { $, esc } = S;
  const css = document.createElement('style');
  css.textContent = `
  .af section { border-bottom: 1px solid var(--line); padding: 4px 0 12px; margin-bottom: 10px; }
  .af .sh { display: flex; align-items: center; gap: 6px; font-weight: 700; font-size: 12px; color: var(--tx2); margin: 4px 0 8px; }
  .af .sh .badge { margin-left: auto; font-weight: 600; font-size: 10.5px; color: var(--tx3); background: var(--bg2); border: 1px solid var(--line); border-radius: 999px; padding: 1px 7px; }
  .af .seg button { flex-direction: column; gap: 1px; padding: 5px 2px; font-size: 11.5px; }
  .af .seg button small { display: block; font-weight: 500; font-size: 9.5px; color: var(--tx3); white-space: nowrap; }
  .af .big { width: 100%; justify-content: center; padding: 12px; font-size: 13.5px; font-weight: 700; margin: 2px 0 8px; gap: 8px; }
  .af .row3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 5px; }
  .af .row3 button { justify-content: center; padding: 7px 4px; font-size: 11.5px; }
  .af .stat { display: flex; gap: 5px; flex-wrap: wrap; margin: 6px 0 0; }
  .af .stat span { background: var(--bg2); border: 1px solid var(--line2); border-radius: 999px; padding: 2px 8px; font-size: 11px; color: var(--tx2); }
  .af .last { background: var(--bg2); border: 1px solid var(--line); border-radius: var(--rs); padding: 8px 10px; font-size: 11.5px; color: var(--tx2); line-height: 1.5; margin-top: 8px; }
  .af label.sw { display: flex; align-items: center; gap: 8px; margin: 6px 0; cursor: pointer; }`;
  document.head.appendChild(css);
  // labels for the v4 music beds in the "Âm thanh" library panel (library.js)
  try {
    Object.assign(MOOD_VI, { lofi_hiphop: 'Lofi hip-hop', cinematic_epic: 'Điện ảnh hoành tráng', corporate_upbeat: 'Doanh nghiệp tươi', real_estate_luxury: 'BĐS sang trọng',
      tiktok_trap: 'TikTok trap', acoustic_warm: 'Guitar mộc ấm', ambient_calm: 'Thư giãn, thiền', news_bg: 'Nền bản tin', kids_playful: 'Vui nhộn', piano_minimal: 'Piano tâm sự' });
    Object.assign(MOOD_IC, { lofi_hiphop: 'ti-headphones', cinematic_epic: 'ti-movie', corporate_upbeat: 'ti-building', real_estate_luxury: 'ti-home-star', tiktok_trap: 'ti-brand-tiktok',
      acoustic_warm: 'ti-guitar-pick', ambient_calm: 'ti-leaf', news_bg: 'ti-news', kids_playful: 'ti-balloon', piano_minimal: 'ti-piano' });
  } catch {}

  const DENS = [['thua', 'Thưa', '~1 / 8 s'], ['vua', 'Vừa', '~1 / 5 s'], ['day', 'Dày', '~1 / 3 s'], ['ratday', 'Rất dày', '~1 / 2 s']];
  const SRCS = [['preset', 'B-roll động', 'ti-movie'], ['text', 'Chữ nổi', 'ti-typography'], ['emoji', 'Emoji', 'ti-mood-happy'], ['media', 'Media của tôi', 'ti-photo'],
    ['stock', 'Ảnh stock', 'ti-world-search'], ['claude', 'Claude chọn', 'ti-sparkles']];
  const LEVELS = [['nhe', 'Nhẹ', 'chỉ cảnh chính'], ['vua', 'Vừa', '+ riser, số, tiền'], ['phongphu', 'Phong phú', '+ từ khoá, cảm xúc']];
  const DEF = { density: 'vua', src: ['preset', 'text', 'emoji', 'media'], level: 'vua', music: true, after_ai: true };
  let O = { ...DEF }, last = null, busy = false;
  try { O = { ...DEF, ...JSON.parse(localStorage.getItem('avs_autofill') || '{}') }; } catch {}
  const keep = () => { try { localStorage.setItem('avs_autofill', JSON.stringify(O)); } catch {} };

  const counts = () => {
    const TL = S.TL || {}, a = TL.audio || {};
    return { scenes: (TL.scenes || []).filter(s => s._auto).length, edited: (TL.scenes || []).filter(s => s._auto && s._orig).length,
      sfx: (a.sfx || []).filter(x => x._auto).length, music: (a.music || []).filter(m => m._auto).length };
  };
  function render() {
    const c = counts();
    $('#libbody').innerHTML = `<div class="af">
      <section><div class="sh"><i class="ti ti-bolt"></i>Tự thêm b-roll + âm thanh</div>
        <div class="help">Đọc lời thoại rồi chèn b-roll động, chữ nổi, emoji, ảnh của bạn đúng lúc nói; đặt SFX theo từng cảnh và chọn nhạc theo đoạn. Không che mặt người nói, bỏ qua 1,5 s đầu và thẻ kết. Chạy lại chỉ thay phần tự động — phần bạn tự thêm hoặc đã sửa được giữ.</div>
        <button class="primary big" data-af="all" ${busy ? 'disabled' : ''}><i class="ti ${busy ? 'ti-loader-2 spin' : 'ti-bolt'}"></i> Tự thêm B-roll + âm thanh</button>
        <div class="row3"><button data-af="broll" ${busy ? 'disabled' : ''}><i class="ti ti-movie"></i> Chỉ B-roll</button><button data-af="sfx" ${busy ? 'disabled' : ''}><i class="ti ti-volume"></i> Chỉ âm thanh</button>
          <button data-af="clear" ${busy || !(c.scenes + c.sfx + c.music) ? 'disabled' : ''}><i class="ti ti-eraser"></i> Xoá tự động</button></div>
        <div class="stat"><span>${c.scenes} cảnh tự động${c.edited ? ` (${c.edited} đã sửa, giữ)` : ''}</span><span>${c.sfx} SFX</span><span>${c.music ? c.music + ' đoạn nhạc' : 'nhạc giữ nguyên'}</span></div>
        ${last ? `<div class="last">${last}</div>` : ''}
      </section>
      <section><div class="sh"><i class="ti ti-movie"></i>B-roll<span class="badge">mật độ</span></div>
        <div class="seg">${DENS.map(([k, l, s]) => `<button data-afd="${k}" class="${O.density === k ? 'on' : ''}">${l}<small>${s}</small></button>`).join('')}</div>
        <div class="chips">${SRCS.map(([k, l, ic]) => `<button class="chip ${O.src.includes(k) ? 'on' : ''}" data-afs="${k}"><i class="ti ${ic}"></i> ${l}</button>`).join('')}</div>
        <div class="help">${O.src.includes('stock') ? '<b>Ảnh stock</b>: Wikimedia Commons + Openverse (miễn phí, giấy phép CC — tác giả ghi vào media/credits.json, nhớ ghi nguồn). Tối đa 3 ảnh, chỉ cho danh từ cụ thể; cần mạng. ' : ''}${O.src.includes('claude') ? '<b>Claude chọn</b>: hỏi Claude Code (claude -p) chọn preset + chữ cho từng câu, chậm hơn 20–60 s; lỗi thì tự dùng luật offline. ' : ''}${O.src.includes('media') ? 'Ảnh/clip trong Media của dự án được dùng xen kẽ. ' : ''}</div>
      </section>
      <section><div class="sh"><i class="ti ti-volume"></i>Âm thanh<span class="badge">309 SFX · 30 nhạc</span></div>
        <div class="seg">${LEVELS.map(([k, l, s]) => `<button data-afl="${k}" class="${O.level === k ? 'on' : ''}">${l}<small>${s}</small></button>`).join('')}</div>
        <label class="sw"><input type="checkbox" data-afm ${O.music ? 'checked' : ''}> Tự chọn nhạc nền theo nội dung từng đoạn (crossfade, tự hạ khi nói)</label>
        <label class="sw"><input type="checkbox" data-afai ${O.after_ai ? 'checked' : ''}> Tự chạy sau “AI dựng giúp”</label>
        <div class="help">Giới hạn số tiếng mỗi giây, tự giảm âm lượng SFX khi đang có giọng nói. Không có nhạc riêng của bạn thì nhạc cũ được thay bằng nhạc theo đoạn.</div>
      </section></div>`;
  }
  function opts(extra = {}) {
    return { density: O.density, src: O.src.filter(x => x !== 'claude'), claude: O.src.includes('claude'), level: O.level, music: !!O.music, ...extra };
  }
  const NAMES = { all: 'Đang thêm b-roll + âm thanh…', broll: 'Đang thêm b-roll…', sfx: 'Đang đặt âm thanh…', clear: 'Đang xoá phần tự động…' };
  // run(mode, {noUndo}) -> Promise<summary|null>. noUndo: caller already pushed an undo step (AI dựng giúp).
  async function run(mode = 'all', o = {}) {
    if (busy) return null;
    if (mode !== 'sfx' && mode !== 'clear' && !(S.CAP || []).length) { S.toast('Chưa có phụ đề — cần lời thoại để chọn b-roll'); return null; }
    busy = true; render();
    await S.saveNow();
    if (!o.noUndo) S.pushUndo();
    const r = await S.api('/api/autofill', { mode, ...opts(o.opts || {}) });
    if (!r.ok) { busy = false; render(); S.toast(r.error || 'Đang có tác vụ khác chạy'); return null; }
    S.modal(`<h3><i class="ti ti-bolt"></i> ${NAMES[mode]}</h3><div id="jobstep" class="muted">Bắt đầu</div><div class="bar"><i></i></div><pre id="joblog"></pre>`);
    return new Promise(ok => S.pollJob(async j => {
      busy = false;
      if (j.state !== 'done') {
        S.modal(`<h3>Chưa tự thêm được</h3><p>${esc(j.step)}</p><pre>${esc((j.log || '').split('\n').filter(l => !l.startsWith('@@')).join('\n').slice(-1000))}</pre><div class="actions"><button onclick="closeModal()">Đóng</button></div>`);
        render(); return ok(null);
      }
      S.closeModal();
      await S.reload();
      const out = j.out || {}, b = out.broll || {}, kinds = Object.entries(b.kinds || {}).map(([k, v]) => `${S.typeName ? S.typeName(k) : k} ×${v}`).join(', ');
      last = [mode === 'clear' ? `Đã xoá ${b.removed ?? 0} cảnh tự động + SFX/nhạc tự động.` : '',
        b.added != null && mode !== 'clear' ? `B-roll: +${b.added} (${esc(kinds)}) · palette ${esc((b.palette || []).join(' + '))}${b.removed ? ` · thay ${b.removed} cảnh cũ` : ''}${b.claude ? ` · ${esc(b.claude)}` : ''}` : '',
        out.sfx && mode !== 'clear' ? 'Âm thanh: ' + esc(String(out.sfx).replace(/^level \d: /, '')) : ''].filter(Boolean).join('<br>');
      render();
      S.toast(mode === 'clear' ? 'Đã xoá phần tự động' : 'Xong — ⌘Z để hoàn tác');
      ok(out);
    }));
  }
  document.addEventListener('click', e => {
    const t = e.target.closest('.af [data-af],.af [data-afd],.af [data-afs],.af [data-afl]');
    if (!t) return;
    if (t.dataset.af) return run(t.dataset.af);
    if (t.dataset.afd) O.density = t.dataset.afd;
    if (t.dataset.afl) O.level = t.dataset.afl;
    if (t.dataset.afs) { const k = t.dataset.afs; O.src = O.src.includes(k) ? O.src.filter(x => x !== k) : [...O.src, k]; }
    keep(); render();
  });
  document.addEventListener('change', e => {
    if (e.target.matches('.af [data-afm]')) { O.music = e.target.checked; keep(); }
    if (e.target.matches('.af [data-afai]')) { O.after_ai = e.target.checked; keep(); }
  });
  S.autofill = { run, get opts() { return O; }, set afterAi(v) { O.after_ai = !!v; keep(); } };
  S.addPanel('autofill', 'ti-bolt', 'Tự động', render);
})();
