async function getJSON(url){const r=await fetch(url);if(!r.ok)throw new Error(await r.text());return r.json()}
function value(obj,key){return obj[key]??"-"}
async function refresh(){
 try{
  const [health,devices,rows]=await Promise.all([getJSON("/api/health"),getJSON("/api/devices"),getJSON("/api/telemetry?limit=20")]);
  document.getElementById("connection").textContent="Dashboard online";
  document.getElementById("device-count").textContent=devices.length;
  document.getElementById("message-count").textContent=rows.length;
  document.getElementById("mqtt-status").textContent=health.localMqttConnected?"Đã kết nối":"Mất kết nối";
  if(document.activeElement?.type!=="range") document.getElementById("devices").innerHTML=devices.length?devices.map(d=>{
   const p=JSON.parse(d.last_payload||"{}");
   const fanSpeed = Number(p.fan_speed_percent ?? 0);
   const encodedId = encodeURIComponent(d.device_id);
   return `<div class="device"><h3>${escapeHTML(d.device_id)}</h3><p>Nhiệt độ: <b>${value(p,"temperature")} °C</b></p><p>Độ ẩm: <b>${value(p,"humidity")} %</b></p><p>Gesture: <b>${escapeHTML(value(p,"gesture"))}</b></p><p>Confidence: <b>${value(p,"confidence")}</b> · Inference: <b>${value(p,"inference_ms")} ms</b></p><p>Số cử chỉ: <b>${value(p,"gesture_count")}</b></p><label class="fan-control" for="fan-${encodedId}">Tốc độ quạt: <output id="fan-value-${encodedId}">${fanSpeed}</output>%<input id="fan-${encodedId}" type="range" min="0" max="100" step="1" value="${fanSpeed}" oninput="showFanSpeed('${encodedId}',this.value)" onchange="setFanSpeed('${encodedId}',this.value)"></label><p>Lần cuối: ${escapeHTML(d.last_seen)}</p></div>`;
  }).join(""):'<p class="muted">Chưa nhận dữ liệu từ thiết bị.</p>';
  document.getElementById("telemetry").innerHTML=rows.length?rows.map(r=>`<tr><td>${escapeHTML(r.device_id)}</td><td>${value(r.payload,"temperature")}</td><td>${value(r.payload,"humidity")}</td><td>${escapeHTML(value(r.payload,"gesture"))}</td><td>${value(r.payload,"confidence")}</td><td>${value(r.payload,"inference_ms")}</td><td>${value(r.payload,"gesture_count")}</td><td>${value(r.payload,"fan_speed_percent")} %</td><td>${escapeHTML(r.received_at)}</td></tr>`).join(""):'<tr><td colspan="9">Chưa có dữ liệu</td></tr>';
 }catch(e){document.getElementById("connection").textContent="Dashboard offline";console.error(e)}
}
function escapeHTML(s){return String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
function showFanSpeed(id,value){const output=document.getElementById(`fan-value-${id}`);if(output)output.value=value}
async function setFanSpeed(id,value){
 try{const r=await fetch(`/api/devices/${id}/command`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({method:"setFanSpeed",params:Number(value)})});if(!r.ok)throw new Error(await r.text());}
 catch(e){alert("Gửi lệnh thất bại: "+e.message)}
}
refresh();setInterval(refresh,3000);
