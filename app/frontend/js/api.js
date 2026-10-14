/* api.js - lớp gọi API của dashboard.
   Đây là điểm tích hợp với backend (FastAPI). Mọi thao tác ghi (chặn, bỏ chặn, phản hồi)
   đều đi qua đối tượng API; để API.base = null thì chạy giả lập, không gọi mạng. */
/* ===== Lớp API: đặt API.base = 'http://127.0.0.1:8000' để gọi backend thật =====
   GET    /api/flows?window=30m               -> danh sách flow + điểm tấn công
   POST   /api/blocklist  {ip,scope,reason,duration_s,flow_id}
   DELETE /api/blocklist/{ip}
   POST   /api/flows/{id}/feedback {label:'benign'}                          */
const API={base:null,
  async call(m,p,b){
    if(!API.base){await new Promise(r=>setTimeout(r,250));return{ok:true,mock:true}}
    const r=await fetch(API.base+p,{method:m,headers:{'Content-Type':'application/json'},body:b&&JSON.stringify(b)});
    if(!r.ok)throw new Error('HTTP '+r.status);return r.json()},
  block:b=>API.call('POST','/api/blocklist',b),
  unblock:ip=>API.call('DELETE','/api/blocklist/'+encodeURIComponent(ip)),
  feedback:(id,label)=>API.call('POST','/api/flows/'+id+'/feedback',{label})};
