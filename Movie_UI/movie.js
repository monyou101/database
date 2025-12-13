const BASE_URL = "https://database-production-55fc.up.railway.app";

function getQueryId() {
  const params = new URLSearchParams(window.location.search);
  return params.get("id");
}

async function loadMovieDetail() {
  const id = getQueryId();
  if (!id) return;

  try {
    const url = `${BASE_URL}/movies/tmdb/${id}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    
    const data = await res.json();

    if (data.error) {
      const errBox = document.getElementById("movieOverview");
      if(errBox) errBox.textContent = `錯誤：${data.error}`;
      return;
    }

    renderMovieDetail(data);
    renderCast(data.actors || []);
    
    // 呼叫 auth.js 裡的載入評論功能 (確保評論功能存在才呼叫)
    if (typeof loadReviews === "function") {
      loadReviews(id);
    }

  } catch (err) {
    console.error("載入電影失敗", err);
  }
}

function renderMovieDetail(m) {
  const poster = m.poster_url || "No_image_available.png";
  const title = m.title || "未命名電影";
  const year = m.release_year || "未知年份";
  const rating = m.rating ? `${m.rating}` : "N/A";
  const runtime = m.runtime ? `${m.runtime} 分鐘` : "片長未知";
  const genres = m.genres || "未分類";
  const overview = m.overview || "尚無簡介。";

  const setText = (id, text) => {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
  };

  const elPoster = document.getElementById("moviePoster");
  if (elPoster) {
    elPoster.src = poster;
    elPoster.style.background = "none";
  }

  setText("movieTitle", title);
  setText("movieMeta", `${year} · TMDB 評分 ${rating}`);
  setText("movieGenres", `類型：${genres}`);
  setText("movieOverview", overview);
  setText("movieRuntime", runtime);
  setText("movieRating", `TMDB 評分：${rating}`);

  const directorNames = (m.directors || []).map(d => d.name).join("、");
  setText("movieDirectors", directorNames ? `導演：${directorNames}` : "");
}

function renderCast(castList) {
  const box = document.getElementById("movieCast");
  if (!box) return;

  const top5 = castList.slice(0, 5);
  box.innerHTML = top5.map(c => {
      const photo = c.profile_url || "No_image_available.png";
      const name = c.name || "Unknown";
      const character = c.character_name || "";
      const id = c.actor_id; // ★ 重點：取得演員 ID

      // 處理特殊字元，避免 onclick 報錯
      const safeName = name.replace(/'/g, "\\'");
      const safePhoto = photo.replace(/'/g, "\\'");
      const safeChar = character.replace(/'/g, "\\'");

      // ★ 將 ID 傳入 openCastModal
      return `
      <div class="person-card" onclick="openCastModal(${id}, '${safeName}', '${safePhoto}', '${safeChar}')">
        <img src="${photo}" class="person-photo" alt="${name}">
        <div class="person-name">${name}</div>
        <div class="person-role">${character}</div>
      </div>
    `;
  }).join("");
}

// ★ 新增：根據 ID 去後端抓取演員詳細資料
async function fetchPersonDetail(personId) {
  if (!personId) return null;
  try {
    // 假設後端有這個路徑，如果沒有會跳到 catch
    const res = await fetch(`${BASE_URL}/actors/${personId}`);
    if (!res.ok) return null;
    return await res.json();
  } catch (e) {
    console.warn("無法取得演員詳細資料", e);
    return null;
  }
}

// ★ 修改：開啟 Modal 並載入資料
async function openCastModal(id, name, photo, role) {
  const modal = document.getElementById("personModal");
  if (!modal) return;
  
  // 1. 先填入基本資料 (讓使用者不用等)
  const elName = document.getElementById("modalPersonName");
  if(elName) elName.textContent = name;
  
  const elPhoto = document.getElementById("modalPersonPhoto");
  if(elPhoto) elPhoto.src = photo;
  
  const elRole = document.getElementById("modalPersonRole");
  if(elRole) elRole.textContent = role ? `飾演：${role}` : "";

  // 清空舊的簡介，顯示載入中
  const bioBox = document.createElement("p");
  bioBox.id = "modalPersonBio";
  bioBox.style.marginTop = "10px";
  bioBox.style.color = "#ccc";
  bioBox.textContent = "正在載入詳細資料...";
  
  // 清除舊的 Bio 區域 (如果有的話)
  const oldBio = document.getElementById("modalPersonBio");
  if(oldBio) oldBio.remove();
  
  // 插入新 Bio 區塊
  if(elRole) elRole.parentNode.appendChild(bioBox);

  modal.classList.remove("hidden");

  // 2. 呼叫後端 API 取得詳細資料
  const details = await fetchPersonDetail(id);
  
  if (details && details.biography) {
    bioBox.textContent = details.biography;
  } else if (details && details.country) {
    bioBox.textContent = `出生地：${details.country}`;
  } else {
    bioBox.textContent = "目前暫無詳細個人簡介。";
  }
}

function closePersonModal() {
  const modal = document.getElementById("personModal");
  if(modal) modal.classList.add("hidden");
}
// movie.js 最下方

// ======= 1. 搜尋功能 (保持不變) =======
function performSearch() {
  const input = document.getElementById("searchInput");
  if (!input) return;
  const query = input.value.trim();
  if (query) {
    alert(`搜尋功能請至首頁使用，您想搜尋：${query}`);
  }
}
document.getElementById("searchInput")?.addEventListener("keypress", (e) => {
  if (e.key === "Enter") performSearch();
});

// ======= 2. 簡易指令功能 (新版) =======
const cmdInput = document.getElementById("cmdInput");
const BASE_CMD_URL = "https://database-production-55fc.up.railway.app"; 

if (cmdInput) {
  cmdInput.addEventListener("keypress", async (e) => {
    if (e.key === "Enter") {
      const command = cmdInput.value.trim();
      if (!command) return;

      // 為了使用者體驗，可以先清空輸入框
      cmdInput.value = "";
      
      // 顯示「處理中」的提示 (可選)
      // alert("指令傳送中..."); 

      try {
        // ★★★ 這裡之後改成真正的 fetch ★★★
        /*
        const res = await fetch(`${BASE_CMD_URL}/api/cmd`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ command: command })
        });
        const data = await res.json();
        alert("後端回應：\n" + data.message);
        */

        // ★★★ 目前的模擬回應 ★★★
        console.log(`指令 [${command}] 已發送`);
        
        // 模擬延遲回傳
        setTimeout(() => {
          let result = "";
          if (command.startsWith("calc ")) {
             try {
                const expr = command.replace("calc ", "");
                result = `計算結果: ${eval(expr)}`;
             } catch { result = "計算錯誤"; }
          } else if (command === "date") {
             result = "伺服器時間: " + new Date().toLocaleString();
          } else {
             result = `收到指令: "${command}"\n(後端尚未連接，僅做格式測試)`;
          }

          // 用 Alert 彈出結果 (簡單明瞭)
          alert(`💻 指令執行結果：\n------------------\n${result}`);
          
        }, 200);

      } catch (err) {
        alert("指令錯誤：" + err.message);
      }
    }
  });
}
// 啟動
loadMovieDetail();