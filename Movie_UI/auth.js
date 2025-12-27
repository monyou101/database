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
        const savedNickname = localStorage.getItem("user_nickname");
        const savedEmail = localStorage.getItem("user_email");
       if(emailDisplay) {
            emailDisplay.textContent = savedNickname || savedEmail || "會員";
        }
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

// 註冊邏輯：移除信箱驗證，直接送出資料
async function doRegister() {
  const username = document.getElementById("regUsername").value.trim();
  const email = document.getElementById("regEmail").value.trim();
  const password = document.getElementById("regPwd").value.trim();

  if (!username || !email || !password) {
    alert("請填寫完整資訊（暱稱、帳號、密碼）");
    return;
  }

  try {
    const res = await fetch(`${AUTH_URL}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      // 注意：此處 payload 配合後端調整，通常包含 email, password, username
      body: JSON.stringify({ email, password, username })
    });
    
    const data = await res.json();
    if(data.success) { 
      alert("註冊成功！請使用剛才的帳號登入。"); 
      switchTab('login'); 
    } else { 
      alert("註冊失敗：" + data.message); 
    }
  } catch(e) { 
    alert("註冊發生錯誤：" + e.message); 
  }
}

async function doLogin() {
  const email = document.getElementById("loginEmail").value;
  const password = document.getElementById("loginPwd").value;
  try {
    const res = await fetch(`${AUTH_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    
    if(data.success) {
      // 1. 存入 Token
      localStorage.setItem("token", data.token);
      // 2. 存入 Email
      localStorage.setItem("user_email", data.user_email);
      // 3. 存入 暱稱 (重要：解決右上角顯示問題)
      // 嘗試抓取 username 或 nickname，都沒有就用 email 替代
      const displayName = data.username || data.user_email || "會員";
    localStorage.setItem("user_nickname", displayName);
      
      // 4. 重新整理頁面
      location.reload(); 
    } else { 
      alert("登入失敗：" + data.message);
    }
  } catch(e) { 
    console.error(e);
  }
}

function logout() {
  localStorage.removeItem("token");
  localStorage.removeItem("user_email");
  localStorage.removeItem("user_nickname");
  checkLoginStatus();
  location.reload();
}

async function loadReviews(movieId) {
  const box = document.getElementById("reviewsList");
  const siteRatingBox = document.getElementById("siteRating");
  
  if(!box) return;

  try {
    const res = await fetch(`${AUTH_URL}/reviews/${movieId}`);
    
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
                ${r.username || r.nickname || r.email || "匿名用戶"}
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
  
  // 1. 處理「註冊」頁面的眼睛 (regPwd)
  const regPwdInput = document.getElementById("regPwd");
  const toggleRegBtn = document.getElementById("togglePwdBtn");
  
  if (regPwdInput && toggleRegBtn) {
    // 按下顯示
    toggleRegBtn.addEventListener("mousedown", () => regPwdInput.type = "text");
    toggleRegBtn.addEventListener("touchstart", (e) => { // 支援手機觸控
        e.preventDefault(); 
        regPwdInput.type = "text";
    });

    // 放開隱藏
    toggleRegBtn.addEventListener("mouseup", () => regPwdInput.type = "password");
    toggleRegBtn.addEventListener("mouseleave", () => regPwdInput.type = "password");
    toggleRegBtn.addEventListener("touchend", () => regPwdInput.type = "password");
  }

  // 2. ★★★ 新增：處理「登入」頁面的眼睛 (loginPwd) ★★★
  const loginPwdInput = document.getElementById("loginPwd");
  const toggleLoginBtn = document.getElementById("toggleLoginPwdBtn");

  if (loginPwdInput && toggleLoginBtn) {
    // 按下顯示
    toggleLoginBtn.addEventListener("mousedown", () => loginPwdInput.type = "text");
    toggleLoginBtn.addEventListener("touchstart", (e) => {
        e.preventDefault();
        loginPwdInput.type = "text";
    });

    // 放開隱藏
    toggleLoginBtn.addEventListener("mouseup", () => loginPwdInput.type = "password");
    toggleLoginBtn.addEventListener("mouseleave", () => loginPwdInput.type = "password");
    toggleLoginBtn.addEventListener("touchend", () => loginPwdInput.type = "password");
  }
});
// 1. 監聽 Enter 鍵 (解決首頁按 Enter 沒反應)
const searchInput = document.getElementById("searchInput");
if (searchInput) {
  searchInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      smartSearch();
    }
  });
}

// 2. 自動執行搜尋 (如果網址帶有 ?q=... 代表是從內頁跳轉過來的)
window.addEventListener("DOMContentLoaded", () => {
  const params = new URLSearchParams(window.location.search);
  const query = params.get("q");
  if (query && searchInput) {
    searchInput.value = decodeURIComponent(query);
    smartSearch(); // 自動執行搜尋
  }
});