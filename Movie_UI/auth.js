const AUTH_URL = "https://database-production-55fc.up.railway.app";

// 檢查登入狀態
function checkLoginStatus() {
  const token = localStorage.getItem("token");
  const loginBtn = document.getElementById("loginBtn");
  const userInfo = document.getElementById("userInfo");
  const writeSec = document.getElementById("writeReviewSection");
  const hintSec = document.getElementById("loginToReviewHint");
  
  const emailDisplay = document.getElementById("userEmailDisplay");
  if(emailDisplay) emailDisplay.textContent = ""; // 先清空

  if (token) {
    if(loginBtn) loginBtn.classList.add("hidden");
    if(userInfo) {
        userInfo.classList.remove("hidden");
        userInfo.style.display = "flex"; 
        // 顯示使用者 Email
        const savedEmail = localStorage.getItem("user_email");
        if(savedEmail && emailDisplay) emailDisplay.textContent = savedEmail;
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
      // credentials: 'include', // ★ 移除這行，避免某些環境下的權限衝突
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

async function loadReviews(movieId) {
  const box = document.getElementById("reviewsList");
  const siteRatingBox = document.getElementById("siteRating");
  
  if(!box) return;

  try {
    const res = await fetch(`${AUTH_URL}/reviews/tmdb/${movieId}`);
    
    if (!res.ok) {
        box.innerHTML = "<p style='color:#666;'>目前尚無評論。</p>";
        if(siteRatingBox) siteRatingBox.textContent = "本站評分：暫無";
        return;
    }

    const data = await res.json(); 

    if(!data.reviews || data.reviews.length === 0) {
      box.innerHTML = "<p style='color:#666;'>目前尚無評論，成為第一個評論的人吧！</p>";
      if(siteRatingBox) siteRatingBox.textContent = "本站評分：暫無";
      return;
    }
    
    let totalScore = 0;
    let validCount = 0;
    
    data.reviews.forEach(r => {
        if (r.rating !== undefined && r.rating !== null) {
            totalScore += parseInt(r.rating);
            validCount++;
        }
    });
    
    if (siteRatingBox) {
        if (validCount > 0) {
            const avg = (totalScore / validCount).toFixed(1);
            siteRatingBox.innerHTML = `本站評分：<span style="color:#facc15; font-size:1.2em;">★ ${avg}</span> <span style="font-size:0.8em; color:#999;">(${validCount} 人評分)</span>`;
        } else {
            siteRatingBox.textContent = "本站評分：暫無";
        }
    }

    box.innerHTML = data.reviews.map(r => {
      const scoreHtml = (r.rating !== undefined && r.rating !== null) 
        ? `<span style="color: #facc15; font-weight:bold; margin-left: 10px; border: 1px solid #facc15; padding: 1px 6px; border-radius: 4px; font-size: 12px;">★ ${r.rating}</span>` 
        : "";
      
      const dateStr = r.created_at ? r.created_at.slice(0, 10) : "";

      return `
      <div class="review-card" style="margin-bottom: 12px;">
        <div style="display:flex; justify-content: space-between; align-items: center;">
            <div class="review-user" style="display:flex; align-items:center;">
                ${r.email || "匿名用戶"} 
                ${scoreHtml}
            </div>
            <div class="review-date">${dateStr}</div>
        </div>
        <div class="review-text" style="margin-top: 6px; color: #ddd;">${r.body}</div>
      </div>
    `}).join("");

  } catch(e) { 
      console.log("評論載入錯誤", e);
      box.innerHTML = "<p style='color:#666;'>讀取評論時發生錯誤。</p>";
  }
}

// ★★★ 修正後的送出評論 (解決 401 錯誤) ★★★
async function submitReview(event) {
  if (event) {
    event.preventDefault();
  }

  const contentEl = document.getElementById("reviewContent");
  const scoreEl = document.getElementById("reviewScore"); 

  if (!contentEl) return;
  
  const content = contentEl.value;
  if (!content || !content.trim()) {
      alert("請輸入評論內容");
      return;
  }

  let ratingVal = 5;
  if (scoreEl) {
      ratingVal = parseInt(scoreEl.value);
  }

  const movieId = new URLSearchParams(window.location.search).get("id");
  const token = localStorage.getItem("token");

  if (!token) {
      alert("請先登入才能評論！");
      return;
  }

  // 鎖定按鈕
  const submitBtn = event ? event.target : null;
  if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerText = "送出中...";
  }

  try {
    const payload = {
        target_type: 'MOVIE',
        target_id: movieId,
        rating: ratingVal, 
        title: '',
        body: content
    };
    
    // ★ 修正：移除 credentials: 'include'，這常常是導致 401 的原因
    // 因為我們已經在 Header 帶了 Token，後端不需要 Cookie
    const res = await fetch(`${AUTH_URL}/reviews/add`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json", 
        "Authorization": `Bearer ${token}` 
      },
      body: JSON.stringify(payload)
    });

    if (res.status === 401) {
        alert("授權失敗：您的登入已過期，請重新登入。");
        logout(); // 自動登出
        return;
    }

    if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`伺服器錯誤: ${errorText}`);
    }

    const data = await res.json();
    
    if(data.success) {
      document.getElementById("reviewContent").value = ""; 
      await loadReviews(movieId); // 重新載入列表
    } else { 
      alert("評論失敗：" + data.message); 
    }

  } catch(e) { 
    console.error(e);
    alert("送出失敗：" + e.message); 
  } finally {
    if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerText = "送出評論";
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  checkLoginStatus();
  
  const pwdInput = document.getElementById("regPwd");
  const toggleBtn = document.getElementById("togglePwdBtn");
  if (pwdInput && toggleBtn) {
    toggleBtn.addEventListener("mousedown", () => pwdInput.type = "text");
    toggleBtn.addEventListener("mouseup", () => pwdInput.type = "password");
    toggleBtn.addEventListener("mouseleave", () => pwdInput.type = "password");
  }
});