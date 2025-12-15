const IMG_BASE = "https://image.tmdb.org/t/p/w500";
const BACKEND_URL = "https://database-production-55fc.up.railway.app";

// ======= 1. 搜尋功能 =======
async function smartSearch() {
  const input = document.getElementById("searchInput").value.trim();
  const message = document.getElementById("searchMessage");
  const movieSection = document.getElementById("searchMovieSection");
  const peopleSection = document.getElementById("searchPeopleSection");
  const searchResultsSection = document.getElementById("searchResultsSection");

  if (!input) {
    message.textContent = "請輸入電影/人物名稱。";
    return;
  }

  message.textContent = "搜尋中…";
  searchResultsSection.classList.remove("hidden");

  try {
    const res = await fetch(`${BACKEND_URL}/api/search/all?query=${encodeURIComponent(input)}`);
    const data = await res.json();
    
    const movieResults = (data.movie || []).slice(0, 12);
    const peopleResults = (data.person || []).slice(0, 12);

    if (movieResults.length === 0 && peopleResults.length === 0) {
      message.textContent = "查無相關電影或人物。";
      movieSection.classList.add("hidden");
      peopleSection.classList.add("hidden");
      return;
    }

    message.textContent = "";

    // 電影結果
    if (movieResults.length > 0) {
      movieSection.classList.remove("hidden");
      showMovieListFromAPI(movieResults, "movieResults");
    } else {
      movieSection.classList.add("hidden");
    }

    // 人物結果
    if (peopleResults.length > 0) {
      peopleSection.classList.remove("hidden");
      showPeopleListFromAPI(peopleResults, "peopleResults");
    } else {
      peopleSection.classList.add("hidden");
    }
  } catch (err) {
    console.error(err);
    message.textContent = "搜尋時發生錯誤。";
  }
}

function showMovieListFromAPI(list, targetId) {
  const box = document.getElementById(targetId);
  const filteredList = list.filter(m => m.release_year);
  box.innerHTML = filteredList
    .map(m => {
      const poster = m.poster_url || "No_image_available.png";
      const year = m.release_year || "未知年份";
      const rating = m.rating || "N/A";
      return `
        <div class="movie-card" onclick="goMovieDetail(${m.movie_id})">
          <img src="${poster}" class="movie-poster" alt="${m.title}">
          <div class="movie-title">${m.title}</div>
          <div class="movie-meta">${year}</div>
          <div class="movie-rating">⭐ ${rating}</div>
        </div>
      `;
    })
    .join("");
}

function showPeopleListFromAPI(list, targetId) {
  const box = document.getElementById(targetId);
  const filteredList = list.filter(m => m.profile_url);
  box.innerHTML = filteredList
    .map(p => {
      const photo = p.profile_url || "No_image_available.png";
      return `
        <div class="person-card" onclick="openPersonModal(${p.actor_id})">
          <img src="${photo}" class="person-photo" alt="${p.name}">
          <div class="person-name">${p.name}</div>
        </div>
      `;
    })
    .join("");
}

// ======= 2. 排行榜 =======
async function loadTrending() {
  try {
    const res = await fetch(`${BACKEND_URL}/api/trending/all`);
    const data = await res.json();
    
    showRankRow(data.day || [], "rankTodayRow");
    showRankRow(data.week || [], "rankWeekRow");
    showRankRow(data.now_playing || [], "rankNowRow");
    showRankRow(data.upcoming || [], "rankUpcomingRow");
  } catch (err) {
    console.error("載入排行榜失敗", err);
  }
}

function showRankRow(results, targetId) {
  const box = document.getElementById(targetId);
  const list = (results || []).slice(0, 15);
  box.innerHTML = list
    .map(m => {
      const poster = m.poster_url || "No_image_available.png";
      const year = m.release_date ? m.release_date.slice(0, 4) : "未知";
      const rating = m.vote_average ? m.vote_average.toFixed(1) : "N/A";
      return `
        <div class="rank-card" onclick="goMovieDetail(${m.movie_id})">
          <img src="${poster}" class="rank-poster" alt="${m.title}">
          <div class="rank-title">${m.title}</div>
          <div class="rank-meta">${year}</div>
          <div class="rank-rating">⭐ ${rating}</div>
        </div>
      `;
    })
    .join("");
}

// ======= 3. 人物 Modal (正式串接後端 API) =======
async function openPersonModal(personId) {
  const modal = document.getElementById("personModal");
  if (!modal) return;

  // 先清空舊資料
  document.getElementById("personName").textContent = "載入中...";
  document.getElementById("personPhoto").src = "No_image_available.png";
  document.getElementById("personBirth").textContent = "";
  document.getElementById("personPlace").textContent = "";
  document.getElementById("personBio").textContent = "";
  document.getElementById("personKnownFor").innerHTML = "";
  document.getElementById("personMovies").innerHTML = "";

  modal.classList.remove("hidden");

  try {
    // ★ 呼叫後端取得演員詳細資料
    const res = await fetch(`${BACKEND_URL}/actors/${personId}`);
    if (!res.ok) throw new Error("API Error");
    const data = await res.json();

    // 填入資料
    document.getElementById("personName").textContent = data.name;
    document.getElementById("personPhoto").src = data.profile_url || "No_image_available.png";
    document.getElementById("personBirth").textContent = "生日：" + (data.birthdate || "未知");
    document.getElementById("personPlace").textContent = "出生地：" + (data.country || "未知");
    document.getElementById("personBio").textContent = data.biography || "尚無簡介。";

    // 如果後端有回傳 known_for 或 movies (視後端實作而定)
    // 這裡保留擴充空間，如果 data.known_for 存在則顯示
    if (data.known_for && data.known_for.length > 0) {
       // 渲染代表作品邏輯...
    }

  } catch (e) {
    console.error("載入演員失敗", e);
    document.getElementById("personName").textContent = "無法載入資料";
  }
}

function closePersonModal() {
  document.getElementById("personModal").classList.add("hidden");
}

function goMovieDetail(id) {
  window.location.href = `movie.html?id=${id}`;
}

// ======= 4. 指令輸入功能 (CMD) =======
const cmdInput = document.getElementById("cmdInput");
if (cmdInput) {
  cmdInput.addEventListener("keypress", async (e) => {
    if (e.key === "Enter") {
      const command = cmdInput.value.trim();
      if (!command) return;
      
      cmdInput.value = ""; // 清空

      try {
        // ★ 發送 POST 請求給後端 (假設路徑為 /api/cmd)
        const res = await fetch(`${BACKEND_URL}/api/cmd`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ command: command }) // 送出 { "command": "指令內容" }
        });
        
        const data = await res.json();
        
        // ★ 顯示後端回傳的計算結果
        alert(`💻 指令回傳結果：\n\n${JSON.stringify(data, null, 2)}`);

      } catch (err) {
        alert("指令發送失敗：" + err.message);
      }
    }
  });
}

// 初始化
loadTrending();