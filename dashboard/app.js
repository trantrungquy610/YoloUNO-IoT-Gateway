async function getJSON(url){const r=await fetch(url);if(!r.ok)throw new Error(await r.text());return r.json()}
function value(obj,key){return obj[key]??"-"}
async function refresh(){
 try{
  const [health,devices,rows]=await Promise.all([getJSON("/api/health"),getJSON("/api/devices"),getJSON("/api/telemetry?limit=20")]);
  document.getElementById("connection").textContent="Dashboard online";
  document.getElementById("device-count").textContent=devices.length;
  document.getElementById("message-count").textContent=rows.length;
  document.getElementById("mqtt-status").textContent=health.localMqttConnected?"Đã kết nối":"Mất kết nối";
  document.getElementById("devices").innerHTML=devices.length?devices.map(d=>{
   const p=JSON.parse(d.last_payload||"{}");
   return `<div class="device"><h3>${escapeHTML(d.device_id)}</h3><p>Nhiệt độ: <b>${value(p,"temperature")} °C</b></p><p>Độ ẩm: <b>${value(p,"humidity")} %</b></p><p>Lần cuối: ${escapeHTML(d.last_seen)}</p><button onclick="toggleLed('${encodeURIComponent(d.device_id)}',true)">Bật LED</button> <button onclick="toggleLed('${encodeURIComponent(d.device_id)}',false)">Tắt LED</button></div>`;
  }).join(""):'<p class="muted">Chưa nhận dữ liệu từ thiết bị.</p>';
  document.getElementById("telemetry").innerHTML=rows.length?rows.map(r=>`<tr><td>${escapeHTML(r.device_id)}</td><td>${value(r.payload,"temperature")}</td><td>${value(r.payload,"humidity")}</td><td>${escapeHTML(r.received_at)}</td></tr>`).join(""):'<tr><td colspan="4">Chưa có dữ liệu</td></tr>';
 }catch(e){document.getElementById("connection").textContent="Dashboard offline";console.error(e)}
}
function escapeHTML(s){return String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
async function toggleLed(id,state){
 try{const r=await fetch(`/api/devices/${id}/command`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({method:"setLedSwitchValue",params:state})});if(!r.ok)throw new Error(await r.text());alert("Đã gửi lệnh đến thiết bị qua MQTT local");}
 catch(e){alert("Gửi lệnh thất bại: "+e.message)}
}
refresh();setInterval(refresh,3000);
