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
    
    // 呼叫 auth.js 裡的載入評論功能
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
      const id = c.actor_id;

      // 處理特殊字元
      const safeName = name.replace(/'/g, "\\'");
      const safePhoto = photo.replace(/'/g, "\\'");
      const safeChar = character.replace(/'/g, "\\'");

      return `
      <div class="person-card" onclick="openCastModal(${id}, '${safeName}', '${safePhoto}', '${safeChar}')">
        <img src="${photo}" class="person-photo" alt="${name}">
        <div class="person-name">${name}</div>
        <div class="person-role">${character}</div>
      </div>
    `;
  }).join("");
}

// 根據 ID 去後端抓取演員詳細資料
async function fetchPersonDetail(personId) {
  if (!personId) return null;
  try {
    const res = await fetch(`${BASE_URL}/actors/${personId}`);
    if (!res.ok) return null;
    return await res.json();
  } catch (e) {
    console.warn("無法取得演員詳細資料", e);
    return null;
  }
}

// 開啟 Modal 並載入資料
async function openCastModal(id, name, photo, role) {
  const modal = document.getElementById("personModal");
  if (!modal) return;
  
  // 1. 先填入基本資料
  const elName = document.getElementById("modalPersonName");
  if(elName) elName.textContent = name;
  
  const elPhoto = document.getElementById("modalPersonPhoto");
  if(elPhoto) elPhoto.src = photo;
  
  const elRole = document.getElementById("modalPersonRole");
  if(elRole) elRole.textContent = role ? `飾演：${role}` : "";

  // 簡介區塊
  const bioBox = document.createElement("p");
  bioBox.id = "modalPersonBio";
  bioBox.style.marginTop = "10px";
  bioBox.style.color = "#ccc";
  bioBox.textContent = "正在載入詳細資料...";
  
  const oldBio = document.getElementById("modalPersonBio");
  if(oldBio) oldBio.remove();
  
  if(elRole) elRole.parentNode.appendChild(bioBox);

  modal.classList.remove("hidden");

  // 2. 呼叫後端 API
  const details = await fetchPersonDetail(id);
  
  if (details) {
    if (details.biography) bioBox.textContent = details.biography;
    else if (details.country) bioBox.textContent = `出生地：${details.country}`;
    else bioBox.textContent = "目前暫無詳細個人簡介。";
  } else {
    bioBox.textContent = "無法載入詳細資料。";
  }
}

function closePersonModal() {
  const modal = document.getElementById("personModal");
  if(modal) modal.classList.add("hidden");
}

// ======= 搜尋功能 (跳轉) =======
function performSearch() {
  const input = document.getElementById("searchInput");
  if (!input) return;
  const query = input.value.trim();
  if (query) {
    alert(`請至首頁使用搜尋功能，您輸入了：${query}`);
    // window.location.href = `index.html`; // 視需求決定是否跳轉
  }
}
document.getElementById("searchInput")?.addEventListener("keypress", (e) => {
  if (e.key === "Enter") performSearch();
});

// ======= CMD 指令功能 (正式 fetch 版) =======
const cmdInput = document.getElementById("cmdInput");
if (cmdInput) {
  cmdInput.addEventListener("keypress", async (e) => {
    if (e.key === "Enter") {
      const command = cmdInput.value.trim();
      if (!command) return;
      cmdInput.value = "";

      try {
        // ★ 發送 POST 請求
        const res = await fetch(`${BASE_URL}/api/cmd`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ command: command })
        });
        
        const data = await res.json();
        
        // ★ 顯示結果
        alert(`💻 指令執行結果：\n\n${JSON.stringify(data, null, 2)}`);

      } catch (err) {
        alert("指令執行失敗：" + err.message);
      }
    }
  });
}

// 啟動
loadMovieDetail();