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
    
    // ★★★ 修正 1: 從 localStorage 取得 Token ★★★
    const token = localStorage.getItem("token");
    
    // 準備 Header
    const headers = {
      "Content-Type": "application/json"
    };
    
    // 如果有 Token，就放入 Header (這樣後端才知道您已登入)
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    // ★★★ 修正 2: 發送請求時帶上 headers ★★★
    const res = await fetch(url, {
      method: "GET",
      headers: headers
    });

    // ★★★ 修正 3: 針對 401 (未登入) 做優雅的處理 ★★★
    if (res.status === 401) {
      // 顯示需要登入的提示，而不是報錯
      const titleEl = document.getElementById("movieTitle");
      if(titleEl) titleEl.textContent = "🔒 此內容需登入觀看";
      
      const errBox = document.getElementById("movieOverview");
      if(errBox) {
        errBox.innerHTML = `
          <div style="padding: 20px; background: #1e293b; border-radius: 8px; text-align: center;">
            <p style="color: #f97316; font-weight: bold; font-size: 18px; margin-bottom: 10px;">
              您的登入已過期或尚未登入
            </p>
            <p style="color: #ccc; margin-bottom: 20px;">
              為了提供完整的電影資訊，請先登入會員。
            </p>
            <button onclick="openAuthModal()" class="auth-submit" style="width: auto; padding: 8px 24px;">
              立即登入
            </button>
          </div>
        `;
      }
      return; 
    }

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
    const errBox = document.getElementById("movieOverview");
    if(errBox && !errBox.textContent) {
        errBox.textContent = "載入失敗，請稍後再試。";
    }
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

async function openCastModal(id, name, photo, role) {
  const modal = document.getElementById("personModal");
  if (!modal) return;
  
  document.getElementById("modalPersonName").textContent = name;
  document.getElementById("modalPersonPhoto").src = photo;
  
  const elRole = document.getElementById("modalPersonRole");
  if(elRole) elRole.textContent = role ? `飾演：${role}` : "";
  
  document.getElementById("modalPersonBirth").textContent = "";
  document.getElementById("modalPersonPlace").textContent = "";
  document.getElementById("modalPersonBio").textContent = "";
  
  const actorContainer = document.getElementById("modalActorMovies");
  const directorContainer = document.getElementById("modalDirectorMovies");
  
  actorContainer.innerHTML = "";
  directorContainer.innerHTML = "";
  
  if(actorContainer.previousElementSibling) actorContainer.previousElementSibling.style.display = "none";
  if(directorContainer.previousElementSibling) directorContainer.previousElementSibling.style.display = "none";

  modal.classList.remove("hidden");

  const details = await fetchPersonDetail(id);
  
  if (details) {
    let infoHtml = "";
    if (details.birthdate) {
        const birthDate = new Date(details.birthdate);
        const age = new Date().getFullYear() - birthDate.getFullYear();
        const dateStr = details.birthdate.toString().split("T")[0]; 
        infoHtml += `🎂 生日：${dateStr} (現年 ${age} 歲)<br>`;
    }
    if (details.country) {
        infoHtml += `🌍 出生地：${details.country}<br>`;
    }

    document.getElementById("modalPersonBirth").innerHTML = infoHtml;

    if (details.movies_as_actor && details.movies_as_actor.length > 0) {
        if(actorContainer.previousElementSibling) actorContainer.previousElementSibling.style.display = "block";
        actorContainer.innerHTML = details.movies_as_actor.map(m => createMiniMovieCard(m)).join("");
    } 

    if (details.movies_as_director && details.movies_as_director.length > 0) {
        if(directorContainer.previousElementSibling) directorContainer.previousElementSibling.style.display = "block";
        directorContainer.innerHTML = details.movies_as_director.map(m => createMiniMovieCard(m)).join("");
    }

  } else {
    document.getElementById("modalPersonBirth").textContent = "無法載入詳細資料。";
  }
}

function closePersonModal() {
  const modal = document.getElementById("personModal");
  if(modal) modal.classList.add("hidden");
}

function performSearch() {
  const input = document.getElementById("searchInput");
  if (!input) return;
  const query = input.value.trim();
  if (query) {
    alert(`請至首頁使用搜尋功能，您輸入了：${query}`);
  }
}
document.getElementById("searchInput")?.addEventListener("keypress", (e) => {
  if (e.key === "Enter") performSearch();
});

const cmdInput = document.getElementById("cmdInput");
if (cmdInput) {
  cmdInput.addEventListener("keypress", async (e) => {
    if (e.key === "Enter") {
      const command = cmdInput.value.trim();
      if (!command) return;
      cmdInput.value = "";

      try {
        const res = await fetch(`${BASE_URL}/api/cmd`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ command: command })
        });
        
        const data = await res.json();
        alert(`💻 指令執行結果：\n\n${JSON.stringify(data, null, 2)}`);

      } catch (err) {
        alert("指令執行失敗：" + err.message);
      }
    }
  });
}

function createMiniMovieCard(m) {
    const targetId = m.movie_id || m.id;
    const poster = m.poster_url ? m.poster_url : "No_image_available.png";
    const title = m.title || "未知片名";
    const year = m.release_year || (m.release_date ? m.release_date.slice(0,4) : "");

    return `
      <div style="flex: 0 0 90px; margin-right: 12px; cursor: pointer;" onclick="window.location.href='movie.html?id=${targetId}'">
        <img src="${poster}" style="width: 90px; height: 135px; object-fit: cover; border-radius: 4px; border: 1px solid #333;">
        <div style="font-size: 12px; margin-top: 4px; color: #fff; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; width: 90px;">
          ${title}
        </div>
        <div style="font-size: 10px; color: #999;">${year}</div>
      </div>
    `;
}

loadMovieDetail();