// ======= 會員系統邏輯 =======
const AUTH_URL = "http://127.0.0.1:5000"; // 指向您的 Python 後端

// 檢查登入狀態 (初始化)
function checkLoginStatus() {
  const token = localStorage.getItem("token");
  const email = localStorage.getItem("user_email");
  
  const loginBtn = document.getElementById("loginBtn");
  const userInfo = document.getElementById("userInfo");
  const writeSec = document.getElementById("writeReviewSection");
  const hintSec = document.getElementById("loginToReviewHint");

  if (token && email) {
    // 已登入
    if(loginBtn) loginBtn.classList.add("hidden");
    if(userInfo) {
        userInfo.classList.remove("hidden");
        userInfo.style.display = "flex"; // 確保 flex 樣式生效
    }
    document.getElementById("userEmailDisplay").textContent = email;
    
    // 如果在電影頁，顯示寫評論框
    if(writeSec) writeSec.classList.remove("hidden");
    if(hintSec) hintSec.classList.add("hidden");
  } else {
    // 未登入
    if(loginBtn) loginBtn.classList.remove("hidden");
    if(userInfo) userInfo.classList.add("hidden");
    
    if(writeSec) writeSec.classList.add("hidden");
    if(hintSec) hintSec.classList.remove("hidden");
  }
}

// Modal 切換 Tab
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

function openAuthModal() { document.getElementById("authModal").classList.remove("hidden"); }
function closeAuthModal() { document.getElementById("authModal").classList.add("hidden"); }

// ======= 修改後的驗證碼邏輯 =======

// 1. 按下「傳送驗證碼」按鈕時觸發：只負責檢查並打開確認視窗
function sendVerifyCode() {
  const email = document.getElementById("regEmail").value.trim();
  
  if (!email) {
    alert("請輸入 Email");
    return;
  }
  
  // 把 Email 填入確認視窗，並顯示視窗
  document.getElementById("confirmEmailDisplay").textContent = email;
  document.getElementById("confirmEmailModal").classList.remove("hidden");
}

// 2. 關閉確認視窗
function closeConfirmModal() {
  document.getElementById("confirmEmailModal").classList.add("hidden");
}

// 3. 使用者按下「沒錯，發送」後觸發：真正執行 EmailJS 寄信
async function executeSendEmail() {
  // 關閉確認視窗
  closeConfirmModal();
  
  // 再次取得 Email (從確認視窗或輸入框拿都可以)
  const email = document.getElementById("regEmail").value.trim();
  const messageBox = document.getElementById("authMsg"); // 用來顯示狀態

  // 產生隨機驗證碼
  const code = Math.floor(100000 + Math.random() * 900000).toString();
  
  // 存入 localStorage 供註冊比對
  localStorage.setItem("verify_code", code);
  localStorage.setItem("verify_email", email);

  // EmailJS 參數
  const templateParams = {
    to_email: email, // 確保這裡對應 EmailJS 後台設定的 {{to_email}}
    message: code,   // 確保這裡對應 EmailJS 後台設定的 {{message}}
  };

  try {
    if(messageBox) messageBox.textContent = "正在發送驗證碼...";
    
    // ★ 請確認這裡已填入您的 Service ID 和 Template ID
    await emailjs.send('service_bofseos', 'template_yi4ythq', templateParams);
    
    alert(`驗證碼已發送至 ${email}，請查收！`);
    if(messageBox) messageBox.textContent = "驗證碼已發送，請檢查信箱。";
    
  } catch (error) {
    console.error('寄信失敗:', error);
    alert("寄信失敗，請檢查網路或 Email 設定。");
    if(messageBox) messageBox.textContent = "發送失敗，請稍後再試。";
  }
}

// 2. 註冊
async function doRegister() {
  const email = document.getElementById("regEmail").value;
  const code = document.getElementById("regCode").value;
  const password = document.getElementById("regPwd").value;
  
  if (!email || !code || !password) {
    alert("請確認所有欄位都已填寫！");
    return;
  }

  // 顯示 loading 或提示
  const btn = event.target; // 取得按下的按鈕
  const originalText = btn.textContent;
  btn.textContent = "註冊中...";
  btn.disabled = true;

  try {
    const res = await fetch(`${AUTH_URL}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, code, password })
    });
    
    // 如果伺服器回應不是 200-299，手動拋出錯誤
    if (!res.ok) {
        throw new Error(`伺服器回應錯誤: ${res.status}`);
    }

    const data = await res.json();
    if(data.success) {
      alert("註冊成功！請登入。");
      switchTab('login');
    } else {
      document.getElementById("authMsg").textContent = data.message;
      alert("註冊失敗：" + data.message); // 多加一個 alert 比較明顯
    }
  } catch(e) { 
    console.error(e); 
    // ★ 這裡最重要：把連線錯誤顯示出來
    alert("連線失敗！請確認後端 Python 伺服器是否已啟動。\n詳細錯誤：" + e.message);
  } finally {
    // 恢復按鈕
    btn.textContent = originalText;
    btn.disabled = false;
  }
}

// 3. 登入
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
      // 儲存 Token (JWT)
      localStorage.setItem("token", data.token);
      localStorage.setItem("user_email", email);
      closeAuthModal();
      checkLoginStatus();
      location.reload(); // 重新整理以更新狀態
    } else {
      document.getElementById("authMsg").textContent = "登入失敗：" + data.message;
    }
  } catch(e) { console.error(e); }
}

// 4. 登出
function logout() {
  localStorage.removeItem("token");
  localStorage.removeItem("user_email");
  checkLoginStatus();
  location.reload();
}

// 5. 載入評論 (放在 loadMovieDetail 裡呼叫)
async function loadReviews(movieId) {
  try {
    const res = await fetch(`${AUTH_URL}/reviews/${movieId}`);
    const data = await res.json();
    const box = document.getElementById("reviewsList");
    
    if(!data.reviews || data.reviews.length === 0) {
      box.innerHTML = "<p>目前尚無評論，成為第一個評論的人吧！</p>";
      return;
    }
    
    box.innerHTML = data.reviews.map(r => `
      <div class="review-card">
        <div class="review-user">${r.user_email}</div>
        <div class="review-text">${r.content}</div>
        <div class="review-date">${r.created_at}</div>
      </div>
    `).join("");
  } catch(e) { console.error(e); }
}

// 6. 送出評論
async function submitReview() {
  const content = document.getElementById("reviewContent").value;
  const movieId = new URLSearchParams(window.location.search).get("id");
  const token = localStorage.getItem("token");
  
  if(!content) return alert("請輸入內容");
  
  try {
    const res = await fetch(`${AUTH_URL}/reviews/add`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}` // 把 Token 帶給後端驗證
      },
      body: JSON.stringify({ movie_id: movieId, content })
    });
    const data = await res.json();
    if(data.success) {
      document.getElementById("reviewContent").value = "";
      loadReviews(movieId); // 重新載入列表
    } else {
      alert("評論失敗：" + data.message);
    }
  } catch(e) { console.error(e); }
}

// 頁面載入時執行
document.addEventListener("DOMContentLoaded", () => {
  checkLoginStatus();
  // 如果是電影詳細頁，還要載入評論
  const params = new URLSearchParams(window.location.search);
  const id = params.get("id");
  if(id) loadReviews(id);
});// ======= 密碼眼睛功能 =======
document.addEventListener("DOMContentLoaded", () => {
  const pwdInput = document.getElementById("regPwd");
  const toggleBtn = document.getElementById("togglePwdBtn");

  if (pwdInput && toggleBtn) {
    // 1. 滑鼠按下 (MouseDown) -> 顯示密碼
    toggleBtn.addEventListener("mousedown", () => {
      pwdInput.type = "text";
    });

    // 2. 滑鼠放開 (MouseUp) -> 隱藏密碼
    toggleBtn.addEventListener("mouseup", () => {
      pwdInput.type = "password";
    });

    // 3. 滑鼠移開圖示 (MouseLeave) -> 也要隱藏，避免使用者按著移開後密碼一直顯示
    toggleBtn.addEventListener("mouseleave", () => {
      pwdInput.type = "password";
    });
    
    // (選用) 支援手機觸控
    toggleBtn.addEventListener("touchstart", (e) => {
      e.preventDefault(); // 防止觸發 click
      pwdInput.type = "text";
    });
    toggleBtn.addEventListener("touchend", () => {
      pwdInput.type = "password";
    });
  }
});