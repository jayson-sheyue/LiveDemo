'use strict';
const GLOBAL = new Set(['guide-content','source-content','source-links','show-guide','show-readme','model-rules','compare-models','compare-methods','compare-api','compare-why','compare-fit','feature-value','api-out-of-demo','workspaces']);
let catalog, active='talk', busy=false, controller, objectUrl=null, savedConfig=null, liveSocket=null, liveTimer=null, liveSession=null, player=null;
const primed=new Set();
let lastResumeHandle='';
let screenStream=null;
const $ = id => {
  if(GLOBAL.has(id)) return document.getElementById(id);
  const page=document.getElementById('page-'+active);
  if(page){const el=page.querySelector(`[data-id="${id}"]`); if(el) return el;}
  return document.getElementById(id);
};
function workspace(id){return (catalog.workspaces||[]).find(item=>item.id===id)||catalog.workspaces[0];}
function has(feature, spec){return ((spec||workspace(active)).features||[]).includes(feature);}
function val(id, fallback=''){const el=$(id); return el?el.value:fallback;}
function isOn(id){const el=$(id); return !!(el&&el.checked);}
function options(select,entries){if(!select)return; select.replaceChildren(); entries.forEach(([value,label])=>select.add(new Option(label,value)));}
function escapeHtml(value){return String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function featureNote(id){
  const b=(catalog&&catalog.feature_blurbs||{})[id];
  if(!b) return '';
  return `<div class="feature-note"><p><strong>开了会怎样</strong> ${escapeHtml(b.effect)}</p><p><strong>业务价值</strong> ${escapeHtml(b.value)}</p><p class="caution"><strong>不要用来</strong> ${escapeHtml(b.caution)}</p></div>`;
}
function featureBlock(id, controlHtml){
  return `<div class="feature-block">${controlHtml}${featureNote(id)}</div>`;
}
function report(state, summary, detail=''){
  const box=$('log-box'); if(!box) return;
  box.className='log-box '+state;
  $('log-state').textContent={idle:'待命',loading:'进行中',ok:'成功',error:'失败'}[state]||state;
  $('log-summary').textContent=summary;
  $('log-spinner').hidden=state!=='loading';
  const pre=$('log-detail');
  if(detail){pre.hidden=false;pre.textContent=detail;}else{pre.hidden=true;pre.textContent='';}
  if(state!=='idle') box.scrollIntoView({behavior:'smooth',block:'nearest'});
}
function fail(error, fallback){
  const summary=error&&error.name==='AbortError'?'已停止。已提交的请求仍可能计费。':((error&&error.message)||fallback||'操作失败');
  report('error', summary, error&&error.detail||'');
}
function config(){
  const spec=workspace(active);
  const sample=$('samples')&&$('samples').dataset.sampleId||'';
  return {
    engine: spec.id,
    model: val('model', spec.model),
    voice: has('voice')?val('voice','Kore'):'Kore',
    language: val('language', ''),
    languages: '',
    system_instruction: has('system')?val('system_instruction'):'',
    text: has('text')?val('text'):'',
    sample_id: sample,
    audio_b64: '',
    filename: $('filename')?$('filename').value:'',
    input_transcript: !has('input_transcript')||isOn('input_transcript'),
    output_transcript: !has('output_transcript')||isOn('output_transcript'),
    vocabulary: has('vocabulary')?val('vocabulary'):'',
    barge_in: !has('barge_in')||isOn('barge_in'),
    video: has('camera')&&isOn('camera'),
    screen: has('screen')&&isOn('screen'),
    session_resume: has('session_resume')&&isOn('session_resume'),
    resume_handle: '',
    compress: has('compress')&&isOn('compress'),
    affective: has('affective')&&isOn('affective'),
    proactive: has('proactive')&&isOn('proactive'),
    tools: has('tools')?val('tools'):'',
  };
}
function fillLanguages(){
  const spec=workspace(active);
  const sel=$('language'); if(!sel) return;
  const keep=val('language');
  const list=spec.languages||[];
  options(sel, list.map(item=>[item.code, `${item.label}${item.code?' · '+item.code:''}${item.stage&&item.stage!=='GA'?' · '+item.stage:''}`]));
  const prefer=list.some(item=>item.code===keep)?keep:(list[0]&&list[0].code||'');
  sel.value=prefer;
}
function fillVoices(){
  const sel=$('voice'); if(!sel) return;
  const keep=val('voice','Kore');
  options(sel, (catalog.voices||[]).map(item=>[item.name, `${item.name} · ${item.style}`]));
  sel.value=(catalog.voices||[]).some(item=>item.name===keep)?keep:'Kore';
}
function fillModels(){
  const spec=workspace(active);
  const sel=$('model'); if(!sel) return;
  const list=(catalog.models[spec.id])||[spec.model];
  options(sel, list.map(name=>[name, name]));
  sel.value=spec.model;
  const card=catalog.model_cards&&catalog.model_cards[sel.value];
  if($('capability')) $('capability').textContent=card||'';
}
function applySample(sample, button, quiet=false){
  if(busy) return;
  const c=sample.config||{};
  fillLanguages(); fillVoices(); fillModels();
  if($('language') && c.language!==undefined) $('language').value=c.language;
  if($('voice') && c.voice) $('voice').value=c.voice;
  if($('system_instruction')) $('system_instruction').value=c.system_instruction||'';
  if($('text')) $('text').value=c.text||'';
  if($('vocabulary')) $('vocabulary').value=c.vocabulary||'';
  if($('input_transcript')) $('input_transcript').checked=c.input_transcript!==false;
  if($('output_transcript')) $('output_transcript').checked=c.output_transcript!==false;
  if($('barge_in')) $('barge_in').checked=c.barge_in!==false;
  if($('session_resume')) $('session_resume').checked=c.session_resume!==false;
  if($('compress')) $('compress').checked=!!c.compress;
  if($('affective')) $('affective').checked=!!c.affective;
  if($('proactive')) $('proactive').checked=!!c.proactive;
  if($('tools')) $('tools').value=c.tools||'';
  if($('camera')){
    $('camera').checked=!!c.video;
    ensureStillCamera(!!$('camera').checked).catch(e=>fail(e,'无法打开摄像头'));
  }
  if($('screen')){
    $('screen').checked=!!c.screen;
    if(c.screen) ensureScreen(true).catch(e=>fail(e,'无法共享屏幕'));
    else stopScreen();
  }
  const samplesEl=$('samples');
  if(samplesEl) samplesEl.dataset.sampleId=sample.id||'';
  if($('expected')) $('expected').textContent=sample.expected?('样例预期：'+sample.expected):'';
  if($('sample-note')) $('sample-note').textContent=sample.note||'';
  document.querySelectorAll(`#page-${active} [data-id="samples"] button`).forEach(item=>item.classList.toggle('selected',item===button));
  if(!quiet) report('ok',`已导入「${sample.title}」。这是 ${workspace(active).nav} 页的样例。`,sample.note||'');
}
function renderSamples(){
  const root=$('samples'); if(!root) return;
  root.replaceChildren();
  const mine=(catalog.samples||[]).filter(sample=>sample.engine===active);
  const groups=new Map();
  mine.forEach(sample=>{const name=sample.group||'本页样例'; if(!groups.has(name)) groups.set(name,[]); groups.get(name).push(sample);});
  groups.forEach((items,name)=>{
    const block=document.createElement('div'); block.className='sample-group';
    const heading=document.createElement('small'); heading.textContent=name; block.append(heading);
    const chips=document.createElement('div'); chips.className='examples';
    items.forEach(sample=>{
      const button=document.createElement('button'); button.type='button'; button.textContent=sample.title;
      button.onclick=()=>applySample(sample,button); chips.append(button);
    });
    block.append(chips); root.append(block);
  });
  if(!mine.length){const p=document.createElement('p'); p.className='hint'; p.textContent='这一页还没有样例。'; root.append(p); return;}
  applySample(mine[0], root.querySelector('button'), true);
}
function htmlTable(rows){
  if(!rows||!rows.length) return '';
  const head=rows[0].map(cell=>`<th>${escapeHtml(String(cell))}</th>`).join('');
  const body=rows.slice(1).map(row=>'<tr>'+row.map(cell=>`<td>${cellHtml(cell)}</td>`).join('')+'</tr>').join('');
  return `<div class="compare-wrap"><table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
}
function cellHtml(value){
  return String(value).split(/(https:\/\/[^\s]+)/).map((part,i)=>i%2?`<a href="${escapeHtml(part)}" target="_blank" rel="noopener noreferrer">${escapeHtml(part)}</a>`:escapeHtml(part).replace(/\n/g,'<br>')).join('');
}
function pageIntro(spec){
  const pos=spec.positioning||{};
  const banner=pos.official?`<div class="mandate"><strong>${escapeHtml(pos.official)}</strong>${pos.this_page?`<p>${escapeHtml(pos.this_page)}</p>`:''}${pos.not_this?`<p class="not-for">${escapeHtml(pos.not_this)}</p>`:''}</div>`:'';
  const fit=(spec.fit||[]).map(item=>`<article class="fit-item"><strong>${escapeHtml(item.title)}</strong><p>${escapeHtml(item.body)}</p></article>`).join('');
  const surface=(spec.surface||[]).map(item=>`<li>${escapeHtml(item)}</li>`).join('');
  return `<section class="card page-intro">${banner}<div class="fit-row">${fit}</div>${spec.coverage?`<p class="hint coverage">${escapeHtml(spec.coverage)}</p>`:''}${spec.limit_note?`<p class="hint">${escapeHtml(spec.limit_note)}</p>`:''}${surface?`<div class="surface"><small>本页可试的 API 能力</small><ul>${surface}</ul></div>`:''}</section>`;
}
function pageDocs(spec){
  const docs=spec.docs||[];
  if(!docs.length) return '';
  const items=docs.map(d=>`<a class="doc-link" href="${escapeHtml(d.url)}" target="_blank" rel="noopener noreferrer"><strong>${escapeHtml(d.title)}</strong><small>${escapeHtml(d.why||'')}</small></a>`).join('');
  return `<section class="card docs-footer"><div class="card-heading"><h2>测通以后：接入你们系统</h2><span class="muted">官方文档</span></div><p class="hint">效果满意后再打开这些链接。本 Demo 不是 Google 产品；请求字段以对应页面为准。</p><div class="doc-grid">${items}</div></section>`;
}
function workspaceHTML(spec){
  const ok=feature=>has(feature, spec);
  const advList=(spec.advantages||[]).map(item=>`<li>${item}</li>`).join('');
  const advBox=advList?`<ul class="advantage-list">${advList}</ul>`:'';
  const actionLabel={talk:'▶ 开始对话',transcribe:'▶ 开始听写',textturn:'▶ 请模型说'}[spec.id]||'▶ 开始';
  const sourceCard = spec.id==='textturn' ? `
<section class="card">
<div class="card-heading"><h2><span class="step">01</span> 写一句发给它</h2><span class="muted">${spec.nav}</span></div>
<div class="sample-panel"><div class="sample-head"><strong>本页场景样例</strong><span class="muted">只导入 ${spec.nav}</span></div><div data-id="samples"></div><p data-id="sample-note" class="hint sample-note">样例不会跨页共用。</p></div>
<p data-id="expected" class="expected"></p>
<label>发给模型的文字<textarea data-id="text" placeholder="请用一句话介绍你自己。"></textarea></label>
${ok('camera')||ok('screen')?`<div data-id="preview-stage" class="preview-stage" hidden>${ok('screen')?`<video data-id="screen-preview" class="stage-video" playsinline muted hidden></video>`:''}${ok('camera')?`<video data-id="camera-preview" class="stage-video" playsinline muted hidden></video>`:''}</div>`:''}
<p class="hint">同一条 Live 长连接，差别是你打字、它说话。不是 Cloud TTS。摄像头或屏幕和对话页一样：约 1 帧/秒的 JPEG，会话开着就一直推。点停止才挂断。</p>
</section>` : `
<section class="card">
<div class="card-heading"><h2><span class="step">01</span> 准备说话</h2><span class="muted">${spec.nav}</span></div>
<div class="sample-panel"><div class="sample-head"><strong>本页场景样例</strong><span class="muted">只导入 ${spec.nav}</span></div><div data-id="samples"></div><p data-id="sample-note" class="hint sample-note">样例不会跨页共用。</p></div>
<p data-id="expected" class="expected"></p>
<div class="record-row">
${ok('mic')?`<button class="secondary live" data-id="live-btn" type="button">${spec.id==='talk'?'打开麦克风对话':'对着麦克风听写'}</button>`:''}
</div>
${ok('camera')||ok('screen')?`<div data-id="preview-stage" class="preview-stage" hidden>${ok('screen')?`<video data-id="screen-preview" class="stage-video" playsinline muted hidden></video>`:''}${ok('camera')?`<video data-id="camera-preview" class="stage-video" playsinline muted hidden></video>`:''}</div>`:''}
<p class="hint">${spec.id==='talk'?'浏览器麦是 16 kHz 单声道 PCM。模型回答是 24 kHz。默认可打断。摄像头或屏幕按官方约定发 JPEG，最多 1 帧/秒。':'对着麦克风说话即可。本页不推预录音频。这不是 Chirp StreamingRecognize。'}</p>
<input data-id="filename" type="hidden">
</section>`;
  const featureCard = `
<section class="card">
<div class="card-heading"><h2><span class="step">02</span> 本页相对别的工作台多出来的</h2><span class="muted">请求字段</span></div>
<p class="hint">每个开关下面写了开了会怎样、业务价值和不要用来。打断、工具、情感/主动音频必须在点开始之前选好。</p>
${ok('system')?featureBlock('system', `<label>系统指令<textarea data-id="system_instruction" rows="4" placeholder="RESPOND IN MANDARIN. YOU MUST RESPOND UNMISTAKABLY IN 普通话。"></textarea></label>`):''}
${ok('vocabulary')?featureBlock('vocabulary', `<label>自定义词表（专有名词，逗号分隔）<textarea data-id="vocabulary" rows="2" placeholder="webeye-internal-test"></textarea></label>`):''}
${ok('input_transcript')?featureBlock('input_transcript', `<label class="check"><input data-id="input_transcript" type="checkbox" checked> 显示你说的话（输入转写）</label>`):''}
${ok('output_transcript')?featureBlock('output_transcript', `<label class="check"><input data-id="output_transcript" type="checkbox" checked> 显示它说的话（输出转写）</label>`):''}
${ok('barge_in')?featureBlock('barge_in', `<label class="check"><input data-id="barge_in" type="checkbox" checked> 允许打断（服务端 VAD / barge-in）</label>`):''}
${ok('camera')?featureBlock('camera', `<label class="check"><input data-id="camera" type="checkbox"> 打开摄像头（JPEG · 1 帧/秒）</label>`):''}
${ok('screen')?featureBlock('screen', `<label class="check"><input data-id="screen" type="checkbox"> 共享屏幕（JPEG · 1 帧/秒；与摄像头同时开时合成画中画）</label>`):''}
${ok('session_resume')?featureBlock('session_resume', `<label class="check"><input data-id="session_resume" type="checkbox" checked> 会话恢复（goAway 后可接着聊）</label>`):''}
${ok('compress')?featureBlock('compress', `<label class="check"><input data-id="compress" type="checkbox"> 上下文压缩（滑动窗口；音视频超过约 2 分钟需要它）</label>`):''}
${ok('affective')?featureBlock('affective', `<label class="check"><input data-id="affective" type="checkbox"> Affective Dialog（按语气回答 · Preview）</label>`):''}
${ok('proactive')?featureBlock('proactive', `<label class="check"><input data-id="proactive" type="checkbox"> Proactive Audio（无关话题可不接话 · Preview）</label>`):''}
${ok('tools')?featureBlock('tools', `<label>工具<select data-id="tools"><option value="">不接工具</option><option value="demo">演示函数 · 现在几点 / 实验室状态</option><option value="search">Google 搜索接地</option></select></label>`):''}
<p class="hint">${spec.id==='talk'?'视频是 JPEG 1fps，模型不回传画面。官方不允许搜索工具和自定义函数写在同一次 setup。':spec.id==='textturn'?'和对话页同一套会话。你打字，它开口。没有麦克风，所以没有语音打断和 Proactive Audio。摄像头/屏幕同样约 1 帧/秒。':spec.id==='transcribe'?'只出字幕，不会回答问题。没有说话人分离、没有多声道。会话恢复和压缩可以开。':''}</p>
</section>`;
  return `<section class="engine-page" id="page-${spec.id}" ${spec.id==='talk'?'':'hidden'}>
<div class="hero"><div><div class="eyebrow">${spec.eyebrow}</div><h1>${spec.title}</h1><p>${spec.lead}</p></div><div class="hero-wave" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div></div>
<div class="notice" data-id="connection">正在读取配置…</div>${advBox}${pageIntro(spec)}
<div class="workspace">
<div class="editor-col">${sourceCard}${featureCard}</div>
<aside>
<section class="card">
<div class="card-heading"><h2><span class="step">03</span> ${spec.nav}</h2><span class="pill">LIVE</span></div>
<label>模型<select data-id="model"></select></label>
${ok('voice')?`<label>声音<select data-id="voice"></select></label>`:''}
<label>语言 / locale<select data-id="language"></select></label>
${spec.language_hint?`<p class="hint">${escapeHtml(spec.language_hint)}</p>`:''}
<p data-id="capability" class="hint"></p>
<button class="primary" data-id="primary" type="button"><span class="spinner" aria-hidden="true"></span><span class="btn-text">${actionLabel}</span></button>
<div class="button-row">
<button class="secondary" data-id="preview" type="button">预览请求 · 不收费</button>
<button class="secondary" data-id="resume" type="button" disabled>接着上次</button>
<button class="secondary" data-id="stop" type="button" disabled>停止</button>
</div>
<div data-id="log-box" class="log-box idle">
<div class="log-head"><span data-id="log-spinner" class="spinner" hidden></span><strong>操作记录</strong><span data-id="log-state">待命</span></div>
<p data-id="log-summary">本页只提交 ${spec.nav} 的请求。</p>
<pre data-id="log-detail" hidden></pre>
</div>
</section>
</aside>
</div>
<section class="card output">
<div class="card-heading"><h2>${spec.id==='transcribe'?'字幕':'会话'}</h2><span data-id="status">等待第一段内容</span></div>
<div data-id="empty-output" class="empty"><span>▁ ▃ ▆ ▂ ▅ ▇ ▃ ▁</span><p>在 ${spec.nav} 页产生的内容只出现在这里。</p></div>
<div data-id="result" hidden>
<div data-id="turns" class="turn-log"></div>
<p data-id="transcript" class="transcript"></p>
<audio data-id="result-player" controls hidden></audio>
<p data-id="metrics" class="hint"></p>
<div class="button-row"><button class="secondary" data-id="export" type="button">导出本次配置</button></div>
</div>
<details data-id="preview-panel"><summary>请求预览</summary><p data-id="plan-info"></p><pre data-id="request-preview"></pre></details>
</section>
${pageDocs(spec)}
</section>`;
}
function showOutput(){
  if($('result')) $('result').hidden=false;
  if($('empty-output')) $('empty-output').hidden=true;
}
function appendTurn(kind, label, text, interim=false){
  showOutput();
  const box=$('turns'); if(!box||!text) return;
  let last=box.lastElementChild;
  if(last && last.dataset.kind===kind && (interim || last.dataset.interim==='1')){
    last.querySelector('p').textContent=text;
    last.classList.toggle('interim', interim);
    last.dataset.interim=interim?'1':'0';
    return;
  }
  const el=document.createElement('div');
  el.className='turn '+kind+(interim?' interim':'');
  el.dataset.kind=kind;
  el.dataset.interim=interim?'1':'0';
  el.innerHTML=`<small>${escapeHtml(label)}</small><p>${escapeHtml(text)}</p>`;
  box.append(el);
  box.scrollTop=box.scrollHeight;
}
function stopCapture(session){
  if(!session) return;
  if(session.videoTimer){clearInterval(session.videoTimer); session.videoTimer=null;}
  try{session.proc&&session.proc.disconnect(); session.ctx&&session.ctx.close();}catch{}
  if(session.ownsStream && session.stream){
    session.stream.getTracks().forEach(track=>track.stop());
  }
  bindPreviewVideos();
}
function cameraStream(){
  if(!(has('camera')&&isOn('camera'))) return null;
  if(stillCam && stillCam.getVideoTracks().some(track=>track.readyState==='live')) return stillCam;
  const stream=liveSession&&liveSession.stream;
  if(stream && stream.getVideoTracks().some(track=>track.readyState==='live')) return stream;
  return stillCam;
}
function bindVideo(el, stream){
  if(!el) return false;
  if(!stream){
    el.pause(); el.srcObject=null; el.hidden=true; el.classList.remove('pip-layer');
    return false;
  }
  if(el.srcObject!==stream) el.srcObject=stream;
  el.hidden=false;
  el.play().catch(()=>{});
  return el.videoWidth>0;
}
function bindPreviewVideos(){
  const stage=$('preview-stage');
  const cam=$('camera-preview');
  const screen=$('screen-preview');
  const camStream=cameraStream();
  const wantScreen=has('screen')&&isOn('screen')&&screenStream;
  const wantCam=!!camStream;
  bindVideo(screen, wantScreen?screenStream:null);
  bindVideo(cam, wantCam?camStream:null);
  if(cam) cam.classList.toggle('pip-layer', !!(wantCam && wantScreen));
  if(stage) stage.hidden=!(wantCam||wantScreen);
  return {cam, screen, wantCam, wantScreen};
}
function drawPipFrame(canvas){
  const {cam, screen, wantCam, wantScreen}=bindPreviewVideos();
  const ctx=canvas.getContext('2d');
  if(wantScreen && screen && screen.videoWidth){
    canvas.width=Math.min(768, screen.videoWidth);
    canvas.height=Math.round(canvas.width*screen.videoHeight/screen.videoWidth)||1;
    ctx.fillStyle='#111';
    ctx.fillRect(0,0,canvas.width,canvas.height);
    ctx.drawImage(screen,0,0,canvas.width,canvas.height);
    if(wantCam && cam && cam.videoWidth){
      const pipW=Math.max(96, Math.round(canvas.width*0.28));
      const pipH=Math.round(pipW*cam.videoHeight/cam.videoWidth)||Math.round(pipW*0.75);
      const x=canvas.width-pipW-12;
      const y=canvas.height-pipH-12;
      ctx.fillStyle='#fff';
      ctx.fillRect(x-3,y-3,pipW+6,pipH+6);
      ctx.drawImage(cam,x,y,pipW,pipH);
    }
    return true;
  }
  if(wantCam && cam && cam.videoWidth){
    canvas.width=Math.min(640, cam.videoWidth);
    canvas.height=Math.round(canvas.width*cam.videoHeight/cam.videoWidth)||1;
    ctx.drawImage(cam,0,0,canvas.width,canvas.height);
    return true;
  }
  return false;
}
function startJpegPump(session){
  const wantVideo=(has('camera')&&isOn('camera'))||(has('screen')&&isOn('screen'));
  if(!wantVideo) return;
  bindPreviewVideos();
  const canvas=document.createElement('canvas');
  if(session.videoTimer) clearInterval(session.videoTimer);
  session.videoTimer=setInterval(()=>{
    if(!liveSocket||liveSocket.readyState!==1) return;
    if(!drawPipFrame(canvas)) return;
    canvas.toBlob(blob=>{
      if(!blob||!liveSocket||liveSocket.readyState!==1) return;
      const reader=new FileReader();
      reader.onload=()=>{
        const b64=String(reader.result).split(',')[1];
        if(b64) liveSocket.send(JSON.stringify({type:'video', data:b64}));
      };
      reader.readAsDataURL(blob);
    }, 'image/jpeg', 0.7);
  }, 1000);
}
async function startCapture(){
  stopStillCamera();
  const wantCam=has('camera')&&isOn('camera');
  const wantBarge=!has('barge_in')||isOn('barge_in');
  const constraints={audio:{echoCancellation:true, noiseSuppression:true, autoGainControl:true}};
  if(wantCam) constraints.video={facingMode:'user', width:{ideal:640}, height:{ideal:480}};
  const stream=await navigator.mediaDevices.getUserMedia(constraints);
  const ctx=new AudioContext({sampleRate:16000});
  const src=ctx.createMediaStreamSource(stream);
  const proc=ctx.createScriptProcessor(4096,1,1);
  const mute=ctx.createGain();
  mute.gain.value=0;
  const chunks=[];
  proc.onaudioprocess=event=>{
    const data=event.inputBuffer.getChannelData(0);
    let sum=0;
    for(let i=0;i<data.length;i++) sum+=data[i]*data[i];
    const rms=Math.sqrt(sum/data.length);
    const playing=!!(player&&player.isPlaying());
    if(playing && !wantBarge) return;
    if(playing && rms<0.055) return;
    if(!playing && rms<0.006) return;
    const buf=new Int16Array(data.length);
    for(let i=0;i<data.length;i++) buf[i]=Math.max(-1,Math.min(1,data[i]))*32767;
    chunks.push(buf);
  };
  src.connect(proc); proc.connect(mute); mute.connect(ctx.destination);
  const session={stream, ctx, proc, chunks, videoTimer:null, ownsStream:true, startVideo(){}};
  session.startVideo=()=>startJpegPump(session);
  return session;
}
class PcmPlayer{
  constructor(rate=24000){
    this.ctx=new AudioContext({sampleRate:rate});
    this.next=0;
    this.sources=[];
  }
  playB64(b64){
    const raw=Uint8Array.from(atob(b64), c=>c.charCodeAt(0));
    const view=new DataView(raw.buffer);
    const count=Math.floor(raw.byteLength/2);
    const f32=new Float32Array(count);
    for(let i=0;i<count;i++) f32[i]=view.getInt16(i*2,true)/32768;
    const buf=this.ctx.createBuffer(1, f32.length, this.ctx.sampleRate);
    buf.getChannelData(0).set(f32);
    const src=this.ctx.createBufferSource();
    src.buffer=buf; src.connect(this.ctx.destination);
    const now=this.ctx.currentTime;
    if(this.next<now) this.next=now;
    src.start(this.next);
    this.next+=buf.duration;
    this.sources.push(src);
    src.onended=()=>{this.sources=this.sources.filter(item=>item!==src);};
  }
  isPlaying(){
    if(!this.ctx) return false;
    if(this.sources.length) return true;
    return this.next > this.ctx.currentTime + 0.08;
  }
  interrupt(){
    this.sources.forEach(src=>{try{src.stop();}catch{}});
    this.sources=[];
    this.next=this.ctx.currentTime;
  }
  close(){ try{this.ctx.close();}catch{} }
}
function stopAll(){
  controller?.abort();
  if(liveTimer){clearInterval(liveTimer); liveTimer=null;}
  if(liveSession){stopCapture(liveSession); liveSession=null;}
  if(liveSocket){try{liveSocket.send(JSON.stringify({type:'stop'})); liveSocket.close();}catch{} liveSocket=null;}
  if(player){player.interrupt(); player.close(); player=null;}
  pendingText='';
  setBusy(false);
  bindPreviewVideos();
}
function setBusy(value){
  busy=value;
  const typingLive=active==='textturn' && liveSocket && liveSocket.readyState===1;
  ['preview','live-btn','barge_in','affective','proactive','tools','compress','session_resume'].forEach(id=>{if($(id)) $(id).disabled=value;});
  if($('camera') && active!=='textturn') $('camera').disabled=value;
  if($('primary')){
    $('primary').disabled=value && !typingLive;
    $('primary').classList.toggle('busy', value && !typingLive);
    const label=$('primary').querySelector('.btn-text');
    if(label && active==='textturn') label.textContent=typingLive?'▶ 再发一句':'▶ 请模型说';
  }
  if($('stop')) $('stop').disabled=!value;
  markResume();
}
function connectionText(){
  const ready=catalog.project_configured&&catalog.adc_configured;
  const talk=catalog.engine_locations&&catalog.engine_locations.talk||'us-central1';
  const cap=catalog.engine_locations&&catalog.engine_locations.transcribe||'global';
  if(ready) return `✓ 已配置 Cloud 项目与 ADC。对话/打字走 ${talk}，听写走 ${cap}。两个区域不一样，不要混用。`;
  if(catalog.project_configured) return '○ 已填项目，但未检测到 ADC。请运行 gcloud auth application-default login 后重启。';
  if(catalog.adc_configured) return '○ 已有 ADC，请在 .env 填写 GOOGLE_CLOUD_PROJECT 并重启。';
  return '○ 预览不需要凭据。真正连 Live 请配置 ADC 与项目，并启用 aiplatform.googleapis.com。';
}
async function post(path,data,signal){
  const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data),signal});
  if(!response.ok){
    let body; try{body=await response.json();}catch{}
    const d=body&&body.detail;
    const err=Error(typeof d==='string'?d:(d&&d.message)||`请求失败（${response.status}）`);
    err.detail=typeof d==='string'?d:(d&&d.detail)||(body?JSON.stringify(body,null,2):'HTTP '+response.status);
    throw err;
  }
  return response;
}
async function preview(){
  if(busy) return; setBusy(true); report('loading','正在预览请求，不会调用 Live API…');
  try{
    const p=await(await post('/api/preview',config())).json();
    if($('plan-info')) $('plan-info').textContent=`LIVE · ${p.model} · ${p.location}${p.warnings&&p.warnings.length?' · '+p.warnings.join(' '):''}`;
    if($('request-preview')) $('request-preview').textContent=JSON.stringify({page:active,config:config(),google:p.request,endpoint:p.endpoint},null,2);
    if($('preview-panel')) $('preview-panel').open=true;
    report('ok','预览成功，没有调用 Google。',(p.warnings||[]).join('\n'));
  }catch(e){fail(e,'预览失败');}
  finally{setBusy(false);}
}
let stillCam=null;
function stopStillCamera(){
  stillCam?.getTracks().forEach(track=>track.stop());
  stillCam=null;
  bindPreviewVideos();
}
async function ensureStillCamera(on){
  if(!on){ stopStillCamera(); return; }
  if(stillCam){ bindPreviewVideos(); return; }
  const stream=await navigator.mediaDevices.getUserMedia({
    video:{facingMode:'user', width:{ideal:640}, height:{ideal:480}},
    audio:false,
  });
  stillCam=stream;
  bindPreviewVideos();
}
function cameraOnlySession(){
  return {stream:stillCam, videoTimer:null, ownsStream:false, startVideo(){ startJpegPump(this); }};
}
async function onCameraToggle(on){
  try{
    await ensureStillCamera(on);
    if(liveSocket && liveSocket.readyState===1 && has('camera')){
      if(!liveSession) liveSession=cameraOnlySession();
      if(on || (has('screen')&&isOn('screen'))) startJpegPump(liveSession);
      else if(liveSession.videoTimer && !(has('screen')&&isOn('screen'))){
        clearInterval(liveSession.videoTimer); liveSession.videoTimer=null;
      }
    }
  }catch(e){ fail(e,'无法打开摄像头'); }
}
function stopScreen(){
  screenStream?.getTracks().forEach(track=>track.stop());
  screenStream=null;
  bindPreviewVideos();
}
async function ensureScreen(on){
  if(!on){ stopScreen(); return; }
  if(screenStream){ bindPreviewVideos(); return; }
  screenStream=await navigator.mediaDevices.getDisplayMedia({
    video:{frameRate:1, width:{ideal:640, max:1280}, height:{ideal:360, max:720}},
    audio:false,
  });
  const track=screenStream.getVideoTracks()[0];
  if(track) track.addEventListener('ended', ()=>{
    if($('screen')) $('screen').checked=false;
    stopScreen();
  });
  bindPreviewVideos();
}
async function onScreenToggle(on){
  try{
    await ensureScreen(on);
    if(liveSocket && liveSocket.readyState===1 && has('screen')){
      if(!liveSession) liveSession=cameraOnlySession();
      if(on || (has('camera')&&isOn('camera'))) startJpegPump(liveSession);
      else if(liveSession.videoTimer){
        clearInterval(liveSession.videoTimer); liveSession.videoTimer=null;
      }
    }
  }catch(e){ fail(e,'无法共享屏幕'); }
}
function markResume(){
  if($('resume')) $('resume').disabled=!lastResumeHandle || busy;
}
let liveFailed=false;
let liveOutText='';
let pendingText='';
function mergeTranscript(acc, part){
  if(!part) return acc;
  if(!acc) return part;
  if(part.startsWith(acc)) return part;
  if(acc.startsWith(part)) return acc;
  return acc+part;
}
function handleLiveEvent(data){
  if(data.type==='error'){
    liveFailed=true;
    const err=Error(data.message||'会话失败'); err.detail=data.detail||'';
    fail(err,'会话失败'); stopAll(); return;
  }
  if(data.type==='start'){
    savedConfig=Object.assign({page:active},config(),{model:data.model,location:data.location});
    report('loading',`已连接 ${data.model} @ ${data.location}`,(data.warnings||[]).join('\n'));
  }
  if(data.type==='ready'){
    if(liveSession&&liveSession.startVideo) liveSession.startVideo();
    if(active==='textturn'){
      report('loading','会话已建立。可以继续打字发送。点停止才挂断。');
      if(pendingText && liveSocket && liveSocket.readyState===1){
        liveSocket.send(JSON.stringify({type:'text', text:pendingText}));
        appendTurn('user','你写', pendingText);
        pendingText='';
      }
      setBusy(true);
    }else{
      report('loading','会话已建立。可以说；它说话时再开口即可打断。');
    }
  }
  if(data.audio_b64){
    if(!player) player=new PcmPlayer(data.output_rate||24000);
    player.playB64(data.audio_b64);
  }
  if(data.interrupted){
    if(player) player.interrupt();
    if(liveOutText) appendTurn('model','它说', liveOutText+'（被打断）', false);
    liveOutText='';
    appendTurn('model','模型 · 被打断','播放已停止，可以接着说');
  }
  if(data.input_transcript) appendTurn('user','你说', data.input_transcript, data.input_final===false);
  const spoken=data.output_transcript||data.model_text;
  if(spoken){
    liveOutText=mergeTranscript(liveOutText, spoken);
    appendTurn('model','它说', liveOutText, true);
  }
  if(data.function_calls){
    data.function_calls.forEach(call=>appendTurn('model','工具调用', `${call.name} ${JSON.stringify(call.args||{})}`));
  }
  if(data.function_results){
    data.function_results.forEach(item=>appendTurn('model','工具结果', `${item.name} → ${item.result}`));
  }
  if(data.resume_handle && data.resumable!==false){
    lastResumeHandle=data.resume_handle;
    markResume();
    if($('metrics')) $('metrics').textContent='已拿到恢复句柄。断线后可点「接着上次」。';
    showOutput();
  }
  if(data.go_away) report('loading','服务即将断开（goAway）。大约 10 分钟的 WebSocket 限额。若已打开会话恢复，稍后可点「接着上次」。');
  if(data.turn_complete){
    if(liveOutText) appendTurn('model','它说', liveOutText, false);
    liveOutText='';
    if($('status')) $('status').textContent=active==='textturn'?'这一轮结束，可以再打一句':'这一轮结束，可以继续说';
    report('loading', active==='textturn'?'这一轮结束。连接还在，改字后再发即可。点停止才挂断。':'这一轮结束。连接还在，可以继续说。点停止才挂断。');
  }
  if(data.type==='done'){
    if(!liveFailed) report('ok','会话结束。');
    stopAll();
  }
}
async function openLive(opts={}){
  const resume=!!opts.resume;
  if(liveSocket){ stopAll(); return; }
  if(busy) return;
  if(resume){
    if(!lastResumeHandle){ report('error','还没有恢复句柄。请先开一次并勾选「会话恢复」。'); return; }
    if($('session_resume')) $('session_resume').checked=true;
  }
  const r=config();
  r.sample_id='';
  if(resume) r.resume_handle=lastResumeHandle;
  setBusy(true); liveFailed=false; liveOutText='';
  if(!resume && $('turns')) $('turns').replaceChildren();
  if($('transcript')) $('transcript').textContent='';
  showOutput();
  let session;
  try{
    if(has('mic')) session=await startCapture();
    else if((has('camera')&&isOn('camera')) || (has('screen')&&isOn('screen'))){
      if(has('camera')&&isOn('camera')) await ensureStillCamera(true);
      session=cameraOnlySession();
    }
    if(has('screen')&&isOn('screen')) await ensureScreen(true);
    const socket=new WebSocket(`${location.protocol==='https:'?'wss':'ws'}://${location.host}/ws/live`);
    liveSocket=socket;
    await new Promise((resolve,reject)=>{socket.onopen=resolve; socket.onerror=()=>reject(Error('无法建立 WebSocket'));});
    socket.send(JSON.stringify(r));
    socket.onmessage=event=>{
      const data=JSON.parse(event.data);
      handleLiveEvent(data);
    };
    socket.onclose=()=>{
      if(liveSocket===socket){
        liveSocket=null;
        if(busy){ if(!liveFailed) report('ok','连接已关闭。'); stopAll(); }
      }
    };
    if(session){
      liveSession=session;
      bindPreviewVideos();
      if(session.chunks){
        liveTimer=setInterval(()=>{
          if(!liveSocket||liveSocket.readyState!==1) return;
          while(session.chunks.length){
            const part=session.chunks.shift();
            liveSocket.send(part.buffer);
          }
        }, 200);
      }
    }
    report('loading', resume?'正在用上次句柄重连…':(active==='textturn'?'正在打开会话。连上后会把你写的字发出去。点停止才挂断。':'正在听。说完一句等它答完；点停止结束会话。'));
    if($('status')) $('status').textContent='会话进行中';
  }catch(e){
    if(session) stopCapture(session);
    liveSocket=null; pendingText=''; setBusy(false); fail(e,'无法开始会话');
  }
}
function sendTypedTurn(){
  const text=val('text').trim();
  if(!text){ report('error','请先输入要发给模型的文字。'); return; }
  if(liveSocket && liveSocket.readyState===1){
    liveSocket.send(JSON.stringify({type:'text', text}));
    appendTurn('user','你写', text);
    report('loading','已发送。等它说完可以再改字发送。点停止才挂断。');
    return;
  }
  if(busy) return;
  pendingText=text;
  return openLive();
}
function primaryAction(){
  if(active==='textturn') return sendTypedTurn();
  return openLive();
}
function bindWorkspace(root, spec){
  const click=(id, fn)=>{const el=root.querySelector(`[data-id="${id}"]`); if(el) el.onclick=fn;};
  click('primary', primaryAction); click('preview', preview); click('stop', stopAll);
  click('resume', ()=>openLive({resume:true}));
  click('live-btn', openLive);
  const cam=root.querySelector('[data-id="camera"]');
  if(cam) cam.onchange=()=>onCameraToggle(cam.checked);
  const screen=root.querySelector('[data-id="screen"]');
  if(screen) screen.onchange=()=>onScreenToggle(screen.checked);
  click('export', ()=>{if(!savedConfig)return; const u=URL.createObjectURL(new Blob([JSON.stringify(savedConfig,null,2)],{type:'application/json'})); const a=document.createElement('a'); a.href=u; a.download=`${spec.id}-config.json`; a.click(); setTimeout(()=>URL.revokeObjectURL(u),1000);});
}
function page(name){
  if(!catalog) return;
  if(liveSocket && name!==active) stopAll();
  const engines=(catalog.workspaces||[]).map(item=>item.id);
  const isEngine=engines.includes(name);
  document.querySelectorAll('.engine-page').forEach(el=>el.hidden=el.id!=='page-'+name);
  ['learn','sources'].forEach(id=>{const el=document.getElementById(id); if(el) el.hidden=name!==id;});
  document.querySelectorAll('.nav').forEach(b=>b.classList.toggle('active',b.dataset.page===name));
  if(isEngine){
    active=name;
    if(!primed.has(name)){
      primed.add(name);
      fillModels(); fillLanguages(); fillVoices(); renderSamples();
      const notice=$('connection'); if(notice) notice.textContent=connectionText();
    }
    if(has('camera') && isOn('camera')) ensureStillCamera(true).catch(()=>{});
    else if(!liveSession) stopStillCamera();
    if(has('screen') && isOn('screen')) ensureScreen(true).catch(()=>{});
    else bindPreviewVideos();
  }else{
    stopStillCamera();
  }
  window.scrollTo({top:0,behavior:'smooth'});
}
function inlineMarkdown(value){return escapeHtml(value).replace(/\[([^\]]+)\]\((https:\/\/[^)]+)\)/g,'<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>').replace(/`([^`]+)`/g,'<code>$1</code>').replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>');}
function renderMarkdown(src){
  const lines=src.replace(/\r\n/g,'\n').split('\n'), out=[]; let i=0;
  while(i<lines.length){
    const line=lines[i];
    if(line.startsWith('```')){const buf=[]; i++; while(i<lines.length&&!lines[i].startsWith('```')){buf.push(escapeHtml(lines[i])); i++;} i++; out.push('<pre><code>'+buf.join('\n')+'</code></pre>'); continue;}
    if(line.startsWith('|')&&lines[i+1]&&/^\|?\s*-+/.test(lines[i+1])){
      const rows=[]; while(i<lines.length&&lines[i].startsWith('|')){if(!/^\|?\s*-+/.test(lines[i])) rows.push(lines[i]); i++;}
      out.push('<table>'+rows.map((row,index)=>{const cells=row.split('|').slice(1,-1).map(cell=>inlineMarkdown(cell.trim())); const tag=index?'td':'th'; return '<tr>'+cells.map(cell=>`<${tag}>${cell}</${tag}>`).join('')+'</tr>';}).join('')+'</table>'); continue;
    }
    if(/^---+$/.test(line.trim())){out.push('<hr>'); i++; continue;}
    const heading=line.match(/^(#{1,3})\s+(.*)$/); if(heading){out.push(`<h${heading[1].length}>${inlineMarkdown(heading[2])}</h${heading[1].length}>`); i++; continue;}
    if(/^\s*[-*]\s+/.test(line)){const items=[]; while(i<lines.length&&/^\s*[-*]\s+/.test(lines[i])){items.push('<li>'+inlineMarkdown(lines[i].replace(/^\s*[-*]\s+/,''))+'</li>'); i++;} out.push('<ul>'+items.join('')+'</ul>'); continue;}
    if(/^\s*\d+\.\s+/.test(line)){const items=[]; while(i<lines.length&&/^\s*\d+\.\s+/.test(lines[i])){items.push('<li>'+inlineMarkdown(lines[i].replace(/^\s*\d+\.\s+/,''))+'</li>'); i++;} out.push('<ol>'+items.join('')+'</ol>'); continue;}
    if(!line.trim()){i++; continue;}
    const buf=[line]; i++; while(i<lines.length&&lines[i].trim()&&!/^(#{1,3}\s|```|\||---|[-*]\s|\d+\.\s)/.test(lines[i])) buf.push(lines[i++]);
    out.push('<p>'+inlineMarkdown(buf.join(' '))+'</p>');
  }
  return out.join('');
}
async function loadDoc(kind,target){const response=await fetch('/api/doc/'+kind); if(!response.ok) throw Error('文档加载失败'); const data=await response.json(); $(target).innerHTML=renderMarkdown(data.text); return data.text;}
async function init(){
  try{
    catalog=await(await fetch('/api/catalog')).json();
    const host=$('workspaces');
    (catalog.workspaces||[]).forEach(spec=>{
      host.insertAdjacentHTML('beforeend', workspaceHTML(spec));
      bindWorkspace(document.getElementById('page-'+spec.id), spec);
    });
    $('model-rules').innerHTML=htmlTable(catalog.model_rules);
    $('compare-models').innerHTML=htmlTable(catalog.compare_models);
    $('compare-methods').innerHTML=htmlTable(catalog.compare_methods);
    $('compare-api').innerHTML=htmlTable(catalog.compare_api);
    $('compare-why').innerHTML=htmlTable(catalog.why_not_live);
    $('compare-fit').innerHTML=htmlTable(catalog.fit_guide);
    if($('feature-value')) $('feature-value').innerHTML=htmlTable(catalog.feature_value);
    $('api-out-of-demo').innerHTML=htmlTable(catalog.api_out_of_demo);
    page('talk');
    try{await loadDoc('guide','guide-content');}catch(e){$('guide-content').textContent='学习指南加载失败：'+e.message;}
    try{
      const text=await loadDoc('sources','source-content'); const seen=new Set();
      for(const match of text.matchAll(/\[([^\]]+)\]\((https:\/\/[^)]+)\)/g)){
        if(seen.has(match[2])) continue; seen.add(match[2]);
        const a=document.createElement('a'); a.className='source-link'; a.href=match[2]; a.target='_blank'; a.rel='noopener noreferrer'; a.textContent=match[1]+' ↗';
        const sub=document.createElement('small'); sub.textContent=new URL(match[2]).hostname; a.append(sub); $('source-links').append(a);
      }
    }catch(e){$('source-content').textContent='官方资料加载失败：'+e.message;}
  }catch(e){fail(e,'初始化失败');}
}
document.querySelectorAll('[data-page]').forEach(b=>b.onclick=()=>page(b.dataset.page));
$('show-guide').onclick=()=>loadDoc('guide','guide-content').catch(e=>fail(e,'文档加载失败'));
$('show-readme').onclick=()=>loadDoc('readme','guide-content').catch(e=>fail(e,'文档加载失败'));
window.addEventListener('beforeunload',()=>{controller?.abort(); if(objectUrl) URL.revokeObjectURL(objectUrl); stopStillCamera(); stopAll();});
init();
