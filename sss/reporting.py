"""Standalone offline report. Evidence displays never confer execution authority."""
import html
import json
from pathlib import Path
from .records import digest

STYLE='body{font:16px system-ui;margin:0;background:#f4f6fa;color:#172338}header{padding:24px;background:#172338;color:white}main{max-width:1350px;margin:auto;padding:24px}input,select,button{font:inherit;padding:9px;border:1px solid #bcc8d8;border-radius:6px}input{width:50%}.note{padding:14px;background:#e6edf5;border-left:4px solid #476b92}article{background:white;margin:12px 0;padding:16px;border:1px solid #d6dfeb;border-radius:8px}h1{margin:0 0 8px}h2{font-size:18px}.state{float:right;padding:4px 8px;border-radius:5px;background:#e8edf4}.qualified{background:#d4efdf}.unavailable,.regressed,.not_qualified{background:#ffe4df}small{color:#516179}a{color:#195b9e}code{font-size:13px}#map{overflow:auto;background:white;border:1px solid #d6dfeb;margin:16px 0}svg text{font-size:11px;fill:#172338}svg rect{fill:#edf3fb;stroke:#9aaec8}svg path{stroke:#b5c3d7;fill:none}pre{white-space:pre-wrap;overflow-wrap:anywhere}button{cursor:pointer}input,select{max-width:100%;box-sizing:border-box}code,small{overflow-wrap:anywhere}@media(max-width:600px){main{padding:16px}input,select{width:100%;margin-bottom:8px}.state{float:none;display:inline-block}h2{margin-top:12px}}'

def report_html(graph,assessments=()):
    if digest(graph.document())!=graph.identity:raise ValueError("Changed graph definition")
    rows=list(assessments)
    if any(r.get('graph_id')!=graph.identity for r in rows):raise ValueError('Report results belong to another graph')
    for row in rows:
        if row.get('skill_id') not in graph.nodes or not row.get('profile_id') or not row.get('suite_id'):raise ValueError('Unbound assessment')
    data=dict(graph=graph.document(),graph_id=graph.identity,assessments=rows)
    encoded=json.dumps(data,ensure_ascii=True).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    body="""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Skills cubed report</title><style>STYLE</style><header><h1>Skills cubed</h1><div>Skills, Scoring, Stability</div></header><main><p class="note">A graph of independently tested abilities. Implemented tests and model mastery are separate. Missing evidence stays unmeasured. This report has no training or execution controls.</p><p><input id="search" aria-label="Find a skill" placeholder="Find arithmetic, memory, Linux, proof..."><select id="profile" aria-label="Model and application profile"><option value="">All profiles</option></select></p><p id="counts"></p><details><summary>Prerequisite graph (scroll to explore)</summary><div id="map"></div></details><section id="skills"></section><p><small id="identity"></small></p></main><script type="application/json" id="data">DATA</script><script>
const data=JSON.parse(document.getElementById('data').textContent), nodes=data.graph.nodes;
const byId=Object.fromEntries(nodes.map(n=>[n.id,n]));
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const profiles=[...new Set(data.assessments.map(r=>r.profile_id))];
for(const id of profiles){const o=document.createElement('option');o.value=id;o.textContent=id;document.querySelector('#profile').append(o);}
function render(){const query=document.querySelector('#search').value.toLowerCase(),profile=document.querySelector('#profile').value;
const visible=nodes.filter(n=>(n.id+' '+n.title+' '+n.domains.join(' ')).toLowerCase().includes(query));
document.querySelector('#counts').textContent=`${nodes.filter(n=>n.status==='implemented').length} skills with implemented bounded test families; ${nodes.filter(n=>n.status==='planned').length} planned; ${data.assessments.length} recorded qualifications/attempts.`;
document.querySelector('#skills').innerHTML=visible.map(n=>{const results=data.assessments.filter(r=>r.skill_id===n.id&&(!profile||r.profile_id===profile));return `<article id="${esc(n.id)}"><span class="state">${esc(n.status)} tests</span><h2>${esc(n.title)}</h2><code>${esc(n.id)}</code><p>Prerequisites: ${n.requires.length?n.requires.map(p=>`<a href="#${esc(p)}">${esc(byId[p].title)}</a>`).join(', '):'none'}</p><p><small>Bands: ${esc(n.bands.join(', '))}; groups: ${esc(n.domains.join(', '))}</small></p>${results.length?results.map(r=>`<details><summary>${esc(r.status)} — ${esc(r.profile_id)}</summary><pre>${esc(JSON.stringify(r,null,2))}</pre></details>`).join(''):'<p>Model proficiency: <strong>unmeasured</strong></p>'}</article>`}).join('');}
document.querySelector('#search').addEventListener('input',render);document.querySelector('#profile').addEventListener('change',render);
const depths={},depth=k=>depths[k]??(depths[k]=byId[k].requires.length?1+Math.max(...byId[k].requires.map(depth)):0);
const counts={},pos={};for(const n of nodes){const d=depth(n.id),r=counts[d]||0;counts[d]=r+1;pos[n.id]=[d*230+10,r*58+10];}
const width=(Math.max(...Object.keys(counts).map(Number))+1)*230,height=Math.max(...Object.values(counts))*58+20;
const edges=nodes.flatMap(n=>n.requires.map(p=>{const[a,b]=pos[p],[x,y]=pos[n.id];return `<path d="M${a+205},${b+20} C${a+225},${b+20} ${x-20},${y+20} ${x},${y+20}"/>`})).join('');
const boxes=nodes.map(n=>{const[x,y]=pos[n.id];return `<a href="#${esc(n.id)}"><g><title>${esc(n.title)}</title><rect x="${x}" y="${y}" width="205" height="40" rx="5"/><text x="${x+7}" y="${y+24}">${esc(n.title.slice(0,29))}</text></g></a>`}).join('');
document.querySelector('#map').innerHTML=`<svg role="img" aria-label="Skill prerequisite graph" width="${width}" height="${height}">${edges}${boxes}</svg>`;
document.querySelector('#identity').textContent='Frozen graph '+data.graph_id;render();
</script></html>"""
    return body.replace('STYLE',STYLE).replace('DATA',encoded)

def write_report(graph,path,assessments=()):
    path=Path(path)
    with path.open('x',encoding='utf-8') as stream:stream.write(report_html(graph,assessments))
    return dict(path=str(path),sha256=digest(path.read_text(encoding='utf-8')))
