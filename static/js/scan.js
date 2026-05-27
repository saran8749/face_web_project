
const video=document.getElementById('video');
const canvas=document.getElementById('canvas');
const capture=document.getElementById('capture');
const loader=document.getElementById('loader');
const result=document.getElementById('result');

navigator.mediaDevices.getUserMedia({video:true}).then(s=>{video.srcObject=s}).catch(e=>{result.innerText='Camera denied: '+e});

capture.onclick=async()=>{
  const ctx=canvas.getContext('2d'); ctx.drawImage(video,0,0,canvas.width,canvas.height);
  const dataURL=canvas.toDataURL('image/jpeg');
  loader.style.display='block'; result.innerText='';
  try{
    const res = await fetch('/recognize',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({image:dataURL})});
    const j = await res.json();
    loader.style.display='none';
    if(j.status==='no_face'){ result.innerText='No face found.'; result.style.color='#f87171'; }
    else if(j.status==='ok'){ result.innerText=`Result: ${j.name} — matched: ${j.matched}`; result.style.color=j.matched? '#34d399':'#f87171'; }
    else { result.innerText=JSON.stringify(j); }
  }catch(err){ loader.style.display='none'; result.innerText='Error: '+err; result.style.color='#f87171'; }
};
