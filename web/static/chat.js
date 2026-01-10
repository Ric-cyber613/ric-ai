const api = (path, opts={}) => {
  // include credentials and CSRF token for POSTs
  opts.credentials = opts.credentials || 'same-origin'
  if((opts.method||'GET').toUpperCase() === 'POST'){
    opts.headers = opts.headers || {}
    if(window.csrfToken){ opts.headers['X-CSRF-Token'] = window.csrfToken }
    opts.headers['Content-Type'] = opts.headers['Content-Type'] || 'application/json'
  }
  return fetch(path, opts).then(r => r.json())
}

const messages = document.getElementById('messages')
const input = document.getElementById('input')
const send = document.getElementById('send')
const modeSel = document.getElementById('mode')
const useResearch = document.getElementById('useResearch')
const creativityEl = document.getElementById('creativity')

// KB elements
const kbList = document.getElementById('kbList')
const kbQ = document.getElementById('kbQ')
const kbA = document.getElementById('kbA')
const kbAdd = document.getElementById('kbAdd')

// Model elements
const modelNameEl = document.getElementById('modelName')
const loadModelBtn = document.getElementById('loadModelBtn')
const modelStatus = document.getElementById('modelStatus')

function appendMessage(who, text){
  const d = document.createElement('div')
  d.className = 'message ' + (who==='You'?'you':'ric')
  d.textContent = who + ': ' + text
  messages.appendChild(d)
  messages.scrollTop = messages.scrollHeight
}

async function loadKB(){
  try{
    const res = await api('/api/kb')
    if(res.ok){
      kbList.innerHTML = ''
      res.kb.forEach(e => {
        const li = document.createElement('li')
        li.textContent = `${e.id}: ${e.question}`
        li.title = e.answer
        li.onclick = () => alert(`Q: ${e.question}\n\nA: ${e.answer}`)
        kbList.appendChild(li)
      })
    }
  }catch(e){ console.warn('kb load', e) }
}

kbAdd.onclick = async () => {
  const q = kbQ.value.trim(), a = kbA.value.trim()
  if(!q || !a) return alert('Question and Answer required')
  const res = await api('/api/kb', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({question:q, answer:a})})
  if(res.ok){ kbQ.value=''; kbA.value=''; loadKB(); appendMessage('Ric','Knowledge added.') }
  else alert('Error: ' + (res.error||'unknown'))
}

loadModelBtn.onclick = async () => {
  const model = modelNameEl.value.trim()
  if(!model) return alert('Enter a model name (e.g., gpt2)')
  const res = await api('/api/load_model', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({model})})
  if(res.ok){ updateStatus(); alert('Model loaded') }
  else alert('Error: ' + (res.error||'unknown'))
}

async function updateStatus(){
  try{
    const res = await api('/api/status')
    if(res.ok){
      const t = res.transformer
      modelStatus.textContent = `Mode: ${res.mode} — Model: ${t.model || 'none'} (available:${t.available}, loaded:${t.loaded})`
      // set mode selector
      if(modeSel.value !== res.mode) modeSel.value = res.mode
    }
  }catch(e){ console.warn('status', e) }
}

send.onclick = async () => {
  const text = input.value.trim()
  if(!text) return
  appendMessage('You', text)
  input.value = ''
  const body = {text, creativity: parseFloat(creativityEl.value), mode: modeSel.value, use_research: Boolean(useResearch && useResearch.checked)}
  // show research indicator
  if(body.use_research){ appendMessage('Ric','(searching the web for relevant info...)') }  const res = await api('/api/respond', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)})
  if(res.ok){
    appendMessage('Ric', res.response)
  } else {
    appendMessage('Ric', 'Error: ' + (res.error||'unknown'))
  }
}

input.addEventListener('keyup', (e)=>{ if(e.key==='Enter') send.click() })

// auth UI elements
const loginUser = document.getElementById('loginUser')
const loginPass = document.getElementById('loginPass')
const loginBtn = document.getElementById('loginBtn')
const registerBtn = document.getElementById('registerBtn')
const forgotBtn = document.getElementById('forgotBtn')
const logoutBtn = document.getElementById('logoutBtn')
const userInfo = document.getElementById('userInfo')
const loginEmail = document.getElementById('loginEmail')

async function authStatus(){
  try{
    const res = await api('/auth/status')
    if(res.ok){
      // store CSRF token for subsequent POST requests
      if(res.csrf) window.csrfToken = res.csrf
      if(res.username){
        userInfo.textContent = 'Signed in as ' + res.username
        loginUser.style.display = 'none'
        loginPass.style.display = 'none'
        loginBtn.style.display = 'none'
        registerBtn.style.display = 'none'
        logoutBtn.style.display = 'inline-block'
      } else {
        userInfo.textContent = 'Not signed in'
        loginUser.style.display = 'inline-block'
        loginPass.style.display = 'inline-block'
        loginBtn.style.display = 'inline-block'
        registerBtn.style.display = 'inline-block'
        logoutBtn.style.display = 'none'
      }
    }
  }catch(e){console.warn('auth', e)}
}

loginBtn.onclick = async () => {
  const u = loginUser.value.trim(), p = loginPass.value
  if(!u || !p) return alert('username & password required')
  const res = await api('/auth/login', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({username:u,password:p})})
  if(res.ok){ authStatus(); alert('Logged in') } else alert('Login failed: '+(res.error||'unknown'))
}

registerBtn.onclick = async () => {
  const u = loginUser.value.trim(), p = loginPass.value, e = loginEmail.value.trim()
  if(!u || !p) return alert('username & password required')
  const res = await api('/auth/register', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({username:u,password:p,email:e})})
  if(res.ok){ authStatus(); alert('Registered. You may now log in.') } else alert('Register failed: '+(res.error||'unknown'))
}

forgotBtn.onclick = async () => {
  // open the in-app reset page
  window.location = '/static/reset.html'
}

logoutBtn.onclick = async () => {
  const res = await api('/auth/logout', {method:'POST'})
  if(res.ok){ authStatus(); alert('Logged out') } else alert('Logout failed')
}

// init
window.addEventListener('load', ()=>{ loadKB(); updateStatus(); authStatus(); setInterval(updateStatus, 15000) })
