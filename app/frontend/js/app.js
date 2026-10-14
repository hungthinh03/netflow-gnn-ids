/* app.js - trạng thái, hiển thị và xử lý sự kiện của dashboard.
   Phụ thuộc: api.js (API) và data.js (flows, T0, SVC). Phải nạp sau hai file đó. */
/* ===== Trạng thái & tiện ích ===== */
const $=s=>document.querySelector(s);
const state={win:1800,thr:.65,view:'g',filter:'all',q:'',sel:null,pending:null,blocked:new Map([['103.27.14.6',{reason:'Chặn thủ công',scope:'block',dur:86400}]])};
const WL={300:'5 phút',1800:'30 phút',3600:'1 giờ'},TOT={300:'6.480',1800:'38.412',3600:'74.905'};
const vis=()=>flows.filter(f=>f.ago<state.win);
const isInt=ip=>ip.startsWith('192.168.');
const cls=f=>f.p>=state.thr?'atk':'ok';
const fam=f=>f.type==='Exploits'?'Chưa xác định (gần: Generic)':f.type;
const n2=x=>x.toFixed(2).replace('.',',');
const HINT={Backdoor:'Dấu hiệu backdoor: host nội bộ nguồn có thể đã bị nhiễm, IP đích có thể là máy chủ điều khiển. Cân nhắc xử lý cả hai.',Reconnaissance:'Quét nhiều cổng hoặc nhiều đích: thường nên xử lý IP nguồn.',Exploits:'Họ tấn công chưa xác định: hãy kiểm tra thủ công trước khi chặn.'};
const LBL={atk:'Tấn công',ok:'Bình thường'};
const DUR={3600:'1 giờ',86400:'24 giờ',0:'Không giới hạn'};
const fb=n=>n>=1024?(n/1024).toFixed(1)+' KB':n+' B';
const tmA=a=>new Date(T0-a*1000).toLocaleTimeString('vi-VN',{hour12:false}),tm=f=>tmA(f.ago);
const verb=ip=>isInt(ip)?'cách ly host':'chặn IP';
function toast(m,err){const t=$('#toast');t.textContent=m;t.className='on'+(err?' err':'');clearTimeout(toast.h);toast.h=setTimeout(()=>t.className='',2600)}

/* ===== Hiển thị ===== */
const sum=a=>a.reduce((x,y)=>x+y,0),pc=x=>(x*100).toFixed(1).replace('.',',')+'%',lo=t=>Math.max(0,Math.ceil(t*20)),AG={};
function buckets(){const w=state.win;if(AG[w])return AG[w];const n=w===300?5:30,step=w/n/60;let z=w;const r=()=>(z=z*16807%2147483647)/2147483647;
  return AG[w]={step,B:[...Array(n)].map((_,i)=>{const hot=n===30?((i>=11&&i<=16)||(i>=3&&i<=5)):i===3,h=Array(20).fill(0),nb=Math.round((900+r()*500)*step),na=Math.round(nb*(hot?.05+r()*.04:.01+r()*.015));
    for(let k=0;k<nb;k++)h[Math.floor(r()*r()*8)]++;for(let k=0;k<na;k++)h[8+Math.floor(r()*12)]++;return{h}})}}
function kpis(){const{B}=buckets(),T=sum(B.map(b=>sum(b.h))),A=sum(B.map(b=>sum(b.h.slice(lo(state.thr)))));
  const cell=(l,v,s,k='')=>`<div class="cell"><span class="l">${l}</span><b class="${k}">${v}</b><span class="s">${s}</span></div>`;
  $('#kpis').innerHTML=cell('Flow đã phân tích',T.toLocaleString('vi-VN'),'trong '+WL[state.win]+' gần nhất')
   +cell('Flow bị đánh dấu tấn công',A.toLocaleString('vi-VN'),pc(A/T)+' tổng flow','atk')
   +cell('Nguồn đang bị chặn',state.blocked.size,'gồm IP ngoài và host bị cách ly')
   +cell('Độ trễ suy luận p95','14 ms','PR-AUC trên tập validation: 0,96')}
function chart(){const{B,step}=buckets(),n=B.length,W=640,H=170,L=38,bw=(W-L-4)/n,g=n===5?10:3,base=H-22;
  const at=B.map(b=>sum(b.h.slice(lo(state.thr)))),tt=B.map(b=>sum(b.h)),mx=Math.max(1,...at),top=Math.ceil(mx/5)*5,sc=(base-22)/top,pk=at.indexOf(mx),A=sum(at),T=sum(tt);let o='';
  [0,top/2,top].forEach(v=>{const y=base-v*sc;o+=`<line x1="${L}" x2="${W-4}" y1="${y}" y2="${y}" stroke="var(--line)"/><text x="${L-6}" y="${y+4}" font-size="11" text-anchor="end" style="fill:var(--mut)">${v}</text>`});
  at.forEach((v,i)=>{const h=v*sc,x=L+i*bw+g/2;o+=`<rect x="${x}" y="${base-h}" width="${bw-g}" height="${h}" fill="var(--atk)"><title>${(n-i)*step} phút trước: ${v} tấn công / ${tt[i]} flow (${pc(v/tt[i])})</title></rect>`});
  o+=`<text x="${L+pk*bw+bw/2}" y="${base-mx*sc-5}" font-size="12" font-weight="600" text-anchor="middle" style="fill:var(--atk)">${mx}</text><text x="${L}" y="${H-5}" font-size="11" style="fill:var(--mut)">${WL[state.win]} trước</text><text x="${W-4}" y="${H-5}" font-size="11" text-anchor="end" style="fill:var(--mut)">Bây giờ</text>`;
  $('#chart').innerHTML=o;$('#ch').textContent='Cảnh báo tấn công theo '+(step===1?'phút':step+' phút');$('#csub').textContent=WL[state.win]+' gần nhất';
  $('#csum').innerHTML=`Tổng <b>${A.toLocaleString('vi-VN')}</b> flow bị đánh dấu tấn công trong ${WL[state.win]} (${pc(A/T)} tổng flow). Đỉnh <b>${mx}</b> flow, cách đây ${(n-pk)*step} phút.`}
const score=f=>`<span class="bar ${cls(f)}"><i style="width:${f.p*100}%"></i><b style="left:${state.thr*100}%"></b></span>${n2(f.p)}`;
const hIps=f=>[f.src,f.dst].filter(ip=>state.blocked.has(f.src===ip||f.dst===ip?ip:'')),handled=f=>f.fp||hIps(f).length>0;
const how=f=>f.fp?'cảnh báo sai':(state.blocked.get(hIps(f)[0]).scope==='isolate'?'cách ly host':'chặn IP');
const dtl=f=>[...hIps(f).map(ip=>(state.blocked.get(ip).scope==='isolate'?'Đã cách ly host ':'Đã chặn IP ')+ip),...(f.fp?['Đã đánh dấu là cảnh báo sai']:[])].join('; ');
const badge=(d,t)=>d===t?'<span class="b ok">Đã xử lý</span>':d?`<span class="b sus">Đã xử lý ${d}/${t}</span>`:'<span class="b sus">Chưa xử lý</span>';
const stt=f=>cls(f)!=='atk'?'<span class="mut">Không cần</span>':handled(f)?`${badge(1,1)} <span class="mut">(${how(f)})</span>`:badge(0,1);
function groups(){const M={};vis().forEach(f=>{const c=cls(f);if(c!=='atk')return;(M[f.src+'|'+f.type]=M[f.src+'|'+f.type]||{src:f.src,fl:[]}).fl.push(f)});
  return Object.values(M).map(g=>{g.top=g.fl.reduce((a,b)=>b.p>a.p?b:a);g.d=new Set(g.fl.map(x=>x.dst));g.pt=new Set(g.fl.map(x=>x.port));g.t0=Math.max(...g.fl.map(x=>x.ago));g.t1=Math.min(...g.fl.map(x=>x.ago));return g}).sort((a,b)=>b.top.p-a.top.p)}
function rows(){const g=state.view==='g',q=state.q,FH='<th title="Mô hình chỉ biết các họ đã huấn luyện, họ chưa thấy có thể bị xếp sai">Họ gần nhất (có thể sai)</th><th>Trạng thái</th>',SH='title="Điểm do mô hình tính, chưa hiệu chỉnh nên chưa phải xác suất"';
  $('#seg').hidden=g;document.querySelectorAll('#vseg button').forEach(b=>b.setAttribute('aria-pressed',b.dataset.v===state.view));
  $('#thead').innerHTML=g?`<tr><th>Khoảng thời gian</th><th>Nguồn</th><th>Đích / cổng</th><th>Số flow</th><th ${SH}>Điểm cao nhất</th><th>Kết luận</th>${FH}</tr>`:`<tr><th>Thời gian</th><th>Nguồn → Đích</th><th>Giao thức</th><th ${SH}>Điểm tấn công</th><th>Kết luận</th>${FH}</tr>`;
  let L,h;
  if(g){L=groups().filter(x=>!q||x.src.includes(q)||[...x.d].some(d=>d.includes(q)));$('#cnt').textContent=`${L.length} nhóm cảnh báo từ ${vis().length} flow mẫu trong ${WL[state.win]}. Nhấn vào dòng để xem chi tiết và xử lý.`;
    h=L.map(x=>{const f=x.top,c=cls(f),dn=x.fl.filter(handled).length,dp=x.d.size===1?[...x.d][0]:x.d.size+' đích',pp=x.pt.size===1?':'+[...x.pt][0]:', '+x.pt.size+' cổng';
      return`<tr class="${c}${dn===x.fl.length?' done':''}" data-act="open" data-id="${f.id}" tabindex="0"><td>${tmA(x.t0)} - ${tmA(x.t1)}</td><td>${x.src}</td><td>${dp}${pp}</td><td>${x.fl.length}</td><td>${score(f)}</td><td><span class="b ${c}">${LBL[c]}</span></td><td>${fam(f)}</td><td>${badge(dn,x.fl.length)}</td></tr>`}).join('')}
  else{L=vis().filter(f=>{const c=cls(f);return(state.filter==='all'||state.filter===c)&&(!q||f.src.includes(q)||f.dst.includes(q))});$('#cnt').textContent=`Hiển thị ${L.length} trong ${vis().length} flow mẫu trong ${WL[state.win]}. Nhấn vào dòng để xem chi tiết và xử lý.`;
    h=L.map(f=>{const c=cls(f);return`<tr class="${c}${c==='atk'&&handled(f)?' done':''}" data-act="open" data-id="${f.id}" tabindex="0"><td>${tm(f)}</td><td>${f.src} → ${f.dst}:${f.port}</td><td>${f.proto} ${SVC[f.port]||''}</td><td>${score(f)}</td><td><span class="b ${c}">${LBL[c]}</span></td><td>${c==='atk'?fam(f):'-'}</td><td>${stt(f)}</td></tr>`}).join('')}
  $('#rows').innerHTML=h||'<tr><td colspan="8" class="mut">Không có mục nào khớp. Thử bỏ lọc IP hoặc đổi cửa sổ thời gian.</td></tr>'}

function bl(){const L=[...state.blocked];
  $('#bl').innerHTML=L.length?L.map(([ip,v])=>`<li><div><b>${ip}</b><div class="sub">${v.scope==='isolate'?'Cách ly host':'Chặn IP'}, ${DUR[v.dur]}${v.reason?' - '+v.reason:''}</div></div><button class="btn" data-act="unblock" data-ip="${ip}">Bỏ chặn</button></li>`).join(''):'<li class="empty">Chưa chặn nguồn nào. Mở một cảnh báo và chọn Xử lý để chặn.</li>'}

function drawer(){const f=flows.find(x=>x.id===state.sel),d=$('#drawer');
  if(!f){d.classList.remove('open');d.setAttribute('aria-hidden','true');return}
  const c=cls(f),fan=vis().filter(x=>x.src===f.src),ports=new Set(fan.map(x=>x.port)).size,dsts=new Set(fan.map(x=>x.dst)).size,bk=state.blocked.has(f.src);
  const dd=(k,v)=>`<dt>${k}</dt><dd>${v}</dd>`;
  d.innerHTML=`<div class="dh"><div><div class="sub">Flow #${f.id}, lúc ${tm(f)}</div><h2>${f.src} → ${f.dst}</h2></div><button class="x" data-act="close" aria-label="Đóng">✕</button></div>
  <div class="verdict ${c}"><b>${n2(f.p)}</b><span>điểm tấn công, ${LBL[c].toLowerCase()} (ngưỡng ${n2(state.thr)})</span></div>
  ${c==='atk'?`<p>Họ gần nhất: <b>${fam(f)}</b><br><span class="sub">Mô hình chỉ biết các họ đã huấn luyện; họ chưa thấy có thể bị xếp sai.</span></p>`:''}
  <h3>Ngữ cảnh đồ thị</h3><p>Host nguồn gửi ${fan.length} flow tới ${dsts} đích và ${ports} cổng khác nhau trong cửa sổ đang xem.</p>
  <h3>Đặc trưng flow</h3><dl>${dd('Giao thức',f.proto)}${dd('Cổng đích',f.port+' ('+(SVC[f.port]||'khác')+')')}${dd('Thời lượng',f.dur+' s')}${dd('Số gói / dung lượng',f.pkts+' / '+fb(f.bytes))}${dd('TTL',f.ttl)}${dd('Cờ TCP',f.proto==='TCP'?f.flags:'-')}${dd('Truyền lại',f.retrans)}${dd('IAT trung bình',f.iat+' ms')}</dl>
  ${c==='atk'?`<h3>Xử lý</h3><p>${handled(f)?'<span class="b ok">Đã xử lý</span> '+dtl(f):'<span class="b sus">Chưa xử lý</span> Chưa có hành động nào cho flow này.'}</p>
  <div class="act">${hIps(f).map(ip=>`<button class="btn" data-act="unblock" data-ip="${ip}">Bỏ chặn ${ip}</button>`).join('')}${(!f.fp&&[f.src,f.dst].some(ip=>!state.blocked.has(ip)))?`<button class="btn danger" data-act="block" data-id="${f.id}">${hIps(f).length?'Xử lý thêm…':'Xử lý…'}</button>`:''}${f.fp?`<button class="btn" data-act="unfp" data-id="${f.id}">Bỏ đánh dấu cảnh báo sai</button>`:`<button class="btn" data-act="fp" data-id="${f.id}">Đánh dấu cảnh báo sai</button>`}</div>`:''}`;
  d.classList.add('open');d.setAttribute('aria-hidden','false')}

function render(){kpis();chart();rows();bl();drawer()}

/* ===== Hành động ===== */
const dlg=$('#dlg');
function setDlg(){const f=state.pending,ip=f[$('#dtg').value],i=isInt(ip);
  $('#dt').textContent=(i?'Cách ly host ':'Chặn IP ')+ip;
  $('#dp').textContent=i?'Host nội bộ sẽ bị tách khỏi mạng. Hãy kiểm tra kỹ trước khi xác nhận.':'Mọi kết nối từ và tới IP này sẽ bị chặn tại tường lửa.'}
function askBlock(f){state.pending=f;const o=(k,t)=>`<option value="${k}">${f[k]} (${t}${isInt(f[k])?', host nội bộ':''})</option>`;
  $('#dtg').innerHTML=o('src','nguồn')+o('dst','đích');$('#dh').textContent=HINT[f.type]||'';setDlg();
  $('#dr').value=`${f.type||'Lưu lượng bất thường'} (điểm ${n2(f.p)})`;dlg.returnValue='';dlg.showModal()}
$('#dtg').addEventListener('change',setDlg);
dlg.addEventListener('close',async()=>{if(dlg.returnValue!=='ok')return;
  const f=state.pending,role=$('#dtg').value,ip=f[role],b={ip,scope:isInt(ip)?'isolate':'block',target_role:role,reason:$('#dr').value,duration_s:+$('#dd').value,flow_id:f.id};
  try{await API.block(b);state.blocked.set(ip,{reason:b.reason,scope:b.scope,dur:b.duration_s});toast('Đã '+verb(ip)+' '+ip)}
  catch(e){toast('Không gọi được API chặn: '+e.message,1)}render()});

document.addEventListener('click',async e=>{const t=e.target.closest('[data-act]');if(!t)return;const a=t.dataset.act,f=flows.find(x=>x.id==t.dataset.id);
  if(a==='open'){state.sel=f.id;drawer()}
  else if(a==='close'){state.sel=null;drawer()}
  else if(a==='block')askBlock(f);
  else if(a==='unblock'){try{await API.unblock(t.dataset.ip);state.blocked.delete(t.dataset.ip);toast('Đã bỏ chặn '+t.dataset.ip)}catch(x){toast('Không gọi được API: '+x.message,1)}render()}
  else if(a==='fp'){try{await API.feedback(f.id,'benign');f.fp=true;toast('Đã ghi nhận cảnh báo sai')}catch(x){toast('Không gọi được API: '+x.message,1)}render()}
  else if(a==='unfp'){try{await API.feedback(f.id,'unset');f.fp=false;toast('Đã bỏ đánh dấu cảnh báo sai')}catch(x){toast('Không gọi được API: '+x.message,1)}render()}
  else if(a==='win'){state.win=+t.dataset.v;state.sel=null;document.querySelectorAll('#wseg button').forEach(b=>b.setAttribute('aria-pressed',b===t));render()}
  else if(a==='view'){state.view=t.dataset.v;rows()}
  else if(a==='filter'){state.filter=t.dataset.v;document.querySelectorAll('#seg button').forEach(b=>b.setAttribute('aria-pressed',b===t));rows()}});
document.addEventListener('keydown',e=>{if(e.key==='Enter'&&e.target.matches('tr[data-act]'))e.target.click();if(e.key==='Escape'&&state.sel){state.sel=null;drawer()}});
$('#q').addEventListener('input',e=>{state.q=e.target.value.trim();rows()});

render();
