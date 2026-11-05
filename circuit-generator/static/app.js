const $ = s => document.querySelector(s);
let S = {data: null, view: 'schematic'};
const esc = t => String(t).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

async function api(url, body) {
  const r = await fetch(url, body ? {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)} : {});
  const j = await r.json();
  if (!r.ok) { alert(j.error || 'Request failed'); throw new Error(j.error); }
  return j;
}
function show(d) { S.data = d; $('#title').textContent = d.name; drawSvg(); drawTable(); drawChecks(d.validation); drawBuildSteps(); }
function drawSvg() { $('#canvas').innerHTML = S.data.svg[S.view]; }
function label(id) {
  const i = S.data.circuit.instances.find(x => x.id === id);
  return `${i.id} <small style="color:#8ea0b5">${esc(i.name)}${i.value ? ' ' + esc(i.value) : ''}</small>`;
}
function drawTable() {
  $('#rows').innerHTML = S.data.circuit.connections.map(c =>
    `<tr><td>${label(c.from.c)}</td><td>${esc(c.from.p)}</td><td>${label(c.to.c)}</td><td>${esc(c.to.p)}</td><td class="k k-${c.kind}">${c.kind}</td></tr>`).join('');
}
function drawChecks(v) {
  $('#badge').className = v.valid ? 'badge-ok' : 'badge-bad';
  $('#badge').textContent = v.valid ? 'VALID' : 'ISSUES FOUND';
  $('#checks').innerHTML = v.checks.map(c => `<div class="chk"><b><span>${esc(c.name)}</span><span class="${c.passed ? 'pass' : 'fail'}">${c.passed ? '✔ pass' : '✖ fail'}</span></b>` +
    c.messages.map(m => `<div class="msg ${m.level}">${esc(m.msg)}</div>`).join('') + '</div>').join('');
}
function drawBuildSteps() {
  $('#buildSteps').innerHTML = S.data.build_steps.map(step =>
    `<article class="build-step"><h4>Step ${step.step_number}: ${esc(step.title)}</h4>` +
    `<p><b>Components:</b> ${step.components.map(esc).join(', ') || 'None'}</p>` +
    (step.connections.length ? `<p><b>Connect:</b></p><ul>${step.connections.map(c => `<li>${esc(c.instruction)} <small>(${esc(c.kind)})</small></li>`).join('')}</ul>` : '') +
    `<p><b>How:</b> ${esc(step.how_to_connect)}</p>` +
    `<p class="expected"><b>Expected output:</b> ${esc(step.expected_output)}</p>` +
    step.warnings.map(w => `<p class="warning"><b>Warning:</b> ${esc(w)}</p>`).join('') +
    `</article>`).join('');
}
function download(href, name) { const a = document.createElement('a'); a.href = href; a.download = name; a.click(); }
const fname = ext => `${(S.data.name || 'circuit').toLowerCase().replace(/\W+/g, '-')}-${S.view}.${ext}`;
function needCircuit() { if (!S.data) { alert('Generate or build a circuit first.'); return false; } return true; }

$('#btnRandom').onclick = async () => show(await api('/api/random', {}));
$('#btnBuild').onclick = () => { $('#builder').hidden = !$('#builder').hidden; };
$('#btnBuildGo').onclick = async () => {
  const comps = [...document.querySelectorAll('#picker input:checked')].map(i => i.value);
  show(await api('/api/build', {components: comps}));
};
$('#btnValidate').onclick = async () => { if (needCircuit()) { const v = await api('/api/validate', {circuit: S.data.circuit}); S.data.validation = v; drawChecks(v); } };
$('#btnDownload').onclick = () => needCircuit() && download(URL.createObjectURL(new Blob([S.data.svg[S.view]], {type: 'image/svg+xml'})), fname('svg'));
$('#btnPng').onclick = () => {
  if (!needCircuit()) return;
  const svg = S.data.svg[S.view], img = new Image(), sc = 2;
  img.onload = () => {
    const cv = document.createElement('canvas'); cv.width = img.width * sc; cv.height = img.height * sc;
    const x = cv.getContext('2d'); x.scale(sc, sc); x.drawImage(img, 0, 0);
    cv.toBlob(b => download(URL.createObjectURL(b), fname('png')));
  };
  img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
};
document.querySelectorAll('.tabs button').forEach(b => b.onclick = () => {
  document.querySelectorAll('.tabs button').forEach(x => x.classList.toggle('on', x === b));
  S.view = b.dataset.v; if (S.data) drawSvg();
});
(async () => {
  const comps = await api('/api/components');
  $('#picker').innerHTML = Object.entries(comps).map(([k, v]) => `<label><input type="checkbox" value="${k}">${esc(v.name)}</label>`).join('');
  const ex = await api('/api/examples');
  $('#examples').innerHTML = ex.map(e => `<button class="ex" data-k="${e.key}">${esc(e.name)}<small>${esc(e.desc)}</small></button>`).join('');
  document.querySelectorAll('.ex').forEach(b => b.onclick = async () => show(await api('/api/example/' + b.dataset.k)));
})();
