/* data.js - dữ liệu mẫu để chạy mockup.
   Tạo ra mảng toàn cục `flows` cùng các hằng T0, SVC mà app.js dùng.
   Khi nối backend thật, thay file này bằng đoạn nạp dữ liệu từ GET /api/flows. */
/* ===== Dữ liệu mẫu (thay bằng GET /api/flows) ===== */
let seed=7;const rnd=()=>(seed=seed*16807%2147483647)/2147483647;
const pick=a=>a[Math.floor(rnd()*a.length)];
const T0=Date.now(),SVC={22:'ssh',23:'telnet',53:'dns',80:'http',443:'https',445:'smb',3389:'rdp',8080:'http-alt'};
const SC=[['45.155.205.233','192.168.225.23','TCP',22,9,.86,.99,'Reconnaissance',300],
['185.125.190.98','192.168.225.40','TCP',80,6,.72,.93,'Exploits',9000],
['192.168.225.11','34.107.221.82','TCP',443,5,.55,.81,'Backdoor',60000],
['103.27.14.6','192.168.225.1','UDP',53,4,.45,.62,'Fuzzers',800],
['192.168.225.1','91.189.91.97','TCP',443,8,.02,.2,'',120000],
['192.168.225.23','8.8.8.8','UDP',53,7,.01,.08,'',400],
['192.168.225.57','142.250.66.46','TCP',443,8,.02,.15,'',250000],
['192.168.225.40','185.125.190.98','TCP',80,3,.28,.4,'',5000]];
const flows=[];let fid=2040;
SC.forEach(([src,dst,proto,port,n,lo,hi,type,bm])=>{for(let i=0;i<n;i++){
  const recon=type==='Reconnaissance',bytes=Math.floor(60+rnd()*bm);
  flows.push({id:++fid,ago:Math.floor(3600*rnd()**2),src,dst,proto,port:recon?pick([22,23,3389,445,8080]):port,
    bytes,pkts:Math.max(1,Math.floor(bytes/(recon?60:520))),dur:+(recon?rnd()*.3:rnd()*12).toFixed(2),
    ttl:pick([64,128,254]),flags:recon?'SYN':'SYN,ACK,PSH,FIN',retrans:recon?0:Math.floor(rnd()*4),
    iat:Math.floor(recon?rnd()*20:20+rnd()*400),p:+(lo+rnd()*(hi-lo)).toFixed(2),type,fp:false})}});
flows.sort((a,b)=>a.ago-b.ago);

let flows = [];
let T0 = Date.now();

async function loadFlows(window = "30m") {
  const result = await API.flows(window);

  flows = result.items;
  T0 = Date.now();

  return result;
}
