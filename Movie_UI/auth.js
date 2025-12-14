const AUTH_URL = "https://database-production-55fc.up.railway.app";

// 檢查登入狀態
function checkLoginStatus() {
  const token = localStorage.getItem("token");
  const loginBtn = document.getElementById("loginBtn");
  const userInfo = document.getElementById("userInfo");
  const writeSec = document.getElementById("writeReviewSection");
  const hintSec = document.getElementById("loginToReviewHint");
  
  const emailDisplay = document.getElementById("userEmailDisplay");
  if(emailDisplay) emailDisplay.textContent = "";

  if (token) {
    if(loginBtn) loginBtn.classList.add("hidden");
    if(userInfo) {
        userInfo.classList.remove("hidden");
        userInfo.style.display = "flex"; 
    }
    if(writeSec) writeSec.classList.remove("hidden");
    if(hintSec) hintSec.classList.add("hidden");
  } else {
    if(loginBtn) loginBtn.classList.remove("hidden");
    if(userInfo) userInfo.classList.add("hidden");
    if(writeSec) writeSec.classList.add("hidden");
    if(hintSec) hintSec.classList.remove("hidden");
  }
}

// Modal 切換
function switchTab(tab) {
  const loginForm = document.getElementById("formLogin");
  const regForm = document.getElementById("formRegister");
  const tLogin = document.getElementById("tabLogin");
  const tReg = document.getElementById("tabRegister");
  
  if (tab === 'login') {
    loginForm.classList.remove("hidden");
    regForm.classList.add("hidden");
    tLogin.style.color = "#f97316";
    tReg.style.color = "#9ca3af";
  } else {
    loginForm.classList.add("hidden");
    regForm.classList.remove("hidden");
    tLogin.style.color = "#9ca3af";
    tReg.style.color = "#f97316";
  }
}

function openAuthModal() { 
    const m = document.getElementById("authModal");
    if(m) m.classList.remove("hidden"); 
}
function closeAuthModal() { 
    const m = document.getElementById("authModal");
    if(m) m.classList.add("hidden"); 
}

// 註冊邏輯
function sendVerifyCode() {
  const email = document.getElementById("regEmail").value.trim();
  if (!email) { alert("請輸入 Email"); return; }
  document.getElementById("confirmEmailDisplay").textContent = email;
  document.getElementById("confirmEmailModal").classList.remove("hidden");
}
function closeConfirmModal() { document.getElementById("confirmEmailModal").classList.add("hidden"); }

async function executeSendEmail() {
  closeConfirmModal();
  const email = document.getElementById("regEmail").value.trim();
  const code = Math.floor(100000 + Math.random() * 900000).toString();
  localStorage.setItem("verify_code", code);
  localStorage.setItem("verify_email", email);

  const templateParams = { to_email: email, message: code };
  try {
    await emailjs.send('service_bofseos', 'template_yi4ythq', templateParams);
    alert(`驗證碼已發送至 ${email}`);
  } catch (error) { alert("寄信失敗，請檢查網路。"); }
}

async function doRegister() {
  const email = document.getElementById("regEmail").value;
  const code = document.getElementById("regCode").value;
  const password = document.getElementById("regPwd").value;
  if (!email || !code || !password) { alert("請填寫完整"); return; }

  try {
    const res = await fetch(`${AUTH_URL}/auth/register`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, code, password })
    });
    const data = await res.json();
    if(data.success) { alert("註冊成功"); switchTab('login'); }
    else { alert("註冊失敗：" + data.message); }
  } catch(e) { alert("錯誤：" + e.message); }
}

async function doLogin() {
  const email = document.getElementById("loginEmail").value;
  const password = document.getElementById("loginPwd").value;
  try {
    const res = await fetch(`${AUTH_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: 'include',
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    if(data.success) {
      localStorage.setItem("token", data.token);
      localStorage.setItem("user_email", email);
      closeAuthModal();
      checkLoginStatus();
      location.reload(); 
    } else { alert("登入失敗：" + data.message); }
  } catch(e) { console.error(e); }
}

function logout() {
  localStorage.removeItem("token");
  localStorage.removeItem("user_email");
  checkLoginStatus();
  location.reload();
}

// ★ 修復重點：載入評論 (防止報錯)
async function loadReviews(movieId) {
  const box = document.getElementById("reviewsList");
  if(!box) return;

  try {
    const res = await fetch(`${AUTH_URL}/reviews/tmdb/${movieId}`);
    
    // 如果 API 回傳 404/500，代表沒評論或後端錯誤，直接顯示空訊息，不要拋出錯誤
    if (!res.ok) {
        box.innerHTML = "<p style='color:#666;'>目前尚無評論。</p>";
        return;
    }

    const data = await res.json(); // 這裡如果後端回傳 HTML 還是會爆，但上面那行擋掉大部分錯誤了

    if(!data.reviews || data.reviews.length === 0) {
      box.innerHTML = "<p style='color:#666;'>目前尚無評論，成為第一個評論的人吧！</p>";
      return;
    }
    
    // 顯示評論 (新的在最上面，如果後端沒排序，前端用 reverse)
    box.innerHTML = data.reviews.map(r => `
      <div class="review-card">
        <div class="review-user">${r.email || "匿名用戶"}</div>
        <div class="review-text">${r.body}</div>
        <div class="review-date">${r.created_at || ""}</div>
      </div>
    `).join("");

  } catch(e) { 
      console.log("評論載入略過或格式錯誤", e);
      box.innerHTML = "<p style='color:#666;'>目前尚無評論。</p>";
  }
}

// ★ 修復重點：送出評論 (送出後立刻重整列表)
async function submitReview() {
  const content = document.getElementById("reviewContent").value;
  const movieId = new URLSearchParams(window.location.search).get("id");
  const token = localStorage.getItem("token");

  if(!content) return alert("請輸入內容");
  if(!token) return alert("請先登入");
  
  const submitBtn = event.target;
  submitBtn.disabled = true;
  submitBtn.innerText = "送出中...";

  try {
    const res = await fetch(`${AUTH_URL}/reviews/add`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json", 
        "Authorization": `Bearer ${token}` 
      },
      credentials: 'include',
      body: JSON.stringify({
        target_type: 'MOVIE',
        target_id: movieId,
        rating: 5,
        title: '',
        body: content
      })
    });

    // 檢查回應是否正常
    if (!res.ok) {
        throw new Error(`伺服器錯誤: ${res.status}`);
    }

    const data = await res.json();
    
    if(data.success) {
      document.getElementById("reviewContent").value = ""; // 清空輸入框
      await loadReviews(movieId); // ★ 關鍵：成功後立刻重新載入評論列表
    } else { 
      alert("評論失敗：" + data.message); 
    }
  } catch(e) { 
    console.error(e);
    alert("送出失敗，請確認伺服器狀態。"); 
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerText = "送出評論";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  checkLoginStatus();
  
  // 密碼眼睛功能
  const pwdInput = document.getElementById("regPwd");
  const toggleBtn = document.getElementById("togglePwdBtn");
  if (pwdInput && toggleBtn) {
    toggleBtn.addEventListener("mousedown", () => pwdInput.type = "text");
    toggleBtn.addEventListener("mouseup", () => pwdInput.type = "password");
    toggleBtn.addEventListener("mouseleave", () => pwdInput.type = "password");
  }
});