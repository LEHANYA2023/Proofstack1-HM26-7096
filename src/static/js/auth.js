const role = location.pathname.split('/').pop();
const config = {
 student:{label:'01 / CANDIDATE',title:'Build proof. Not just a resume.',copy:'Turn projects, research, communication and real work into evidence recruiters can inspect.',email:'student@proofstack.dev'},
 expert:{label:'02 / HUMAN REVIEW',title:'Make feedback useful.',copy:'Review evidence with context, leave honest feedback, and mentor the next generation.',email:'expert@proofstack.dev'},
 recruiter:{label:'03 / HIRING',title:'See the person behind the application.',copy:'Discover freshers across technical and non-technical tracks with transparent evidence.',email:'recruiter@proofstack.dev'},
 institution:{label:'04 / TRUST LAYER',title:'Make student readiness visible.',copy:'Verify students and help your campus build evidence that travels with them.',email:'institution@proofstack.dev'}
}[role] || null;
if(config){
 document.getElementById('role-label').textContent=config.label; document.getElementById('login-title').textContent=config.title; document.getElementById('login-copy').textContent=config.copy;
 document.getElementById('role-mini').textContent=config.label; document.getElementById('demo-account').innerHTML=`<code>${config.email}</code>`;
}
function saveSession(data){localStorage.setItem('proofstack_token',data.token); localStorage.setItem('proofstack_user',JSON.stringify(data.user));}
document.getElementById('login-form').addEventListener('submit', async e=>{e.preventDefault(); const err=document.getElementById('login-error'); err.textContent=''; try{const r=await fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:email.value,password:password.value,role})}); const d=await r.json(); if(!r.ok) throw new Error(d.error||'Login failed'); saveSession(d); location.href='/'+role;}catch(x){err.textContent=x.message;}});
