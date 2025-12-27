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
      const year = m.release_year || "未知年份";
      const rating = m.rating ? `${m.rating}` : "N/A";
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

async function openPersonModal(personId) {
  const modal = document.getElementById("personModal");
  if (!modal) return;

  // 1. 先清空舊資料 (包含文字與列表)
  document.getElementById("personName").textContent = "載入中...";
  document.getElementById("personPhoto").src = "No_image_available.png";
  document.getElementById("personBirth").textContent = "";
  document.getElementById("personPlace").textContent = "";
  document.getElementById("personBio").textContent = "";
  
  // ★ 清空電影列表容器
  const knownForBox = document.getElementById("personKnownFor");
  const moviesBox = document.getElementById("personMovies");
  if (knownForBox) knownForBox.innerHTML = "";
  if (moviesBox) moviesBox.innerHTML = "";

  modal.classList.remove("hidden");

  try {
    // 2. 呼叫後端
    const res = await fetch(`${BACKEND_URL}/actors/${personId}`);
    if (!res.ok) throw new Error("API Error");
    const data = await res.json();

    // 3. 填入基本資料
    document.getElementById("personName").textContent = data.name;
    document.getElementById("personPhoto").src = data.profile_url || "No_image_available.png";
   // --- 日期格式統一修改開始 ---
    if (data.birthdate) {
      const birthDate = new Date(data.birthdate);
      const yyyy = birthDate.getFullYear();
      const mm = String(birthDate.getMonth() + 1).padStart(2, '0');
      const dd = String(birthDate.getDate()).padStart(2, '0');
      const dateStr = `${yyyy}-${mm}-${dd}`;

      // 計算年齡
      const age = new Date().getFullYear() - yyyy;

      // 格式：🎂 生日：1992-10-12 (現年 33 歲)
      document.getElementById("personBirth").textContent = `🎂 生日：${dateStr} (現年 ${age} 歲)`;
    } else {
      document.getElementById("personBirth").textContent = "生日：未知";
    }
    // --- 日期格式統一修改結束 ---
    document.getElementById("personPlace").textContent = "出生地：" + (data.country || "未知");
    document.getElementById("personBio").textContent = data.biography || "尚無簡介。";

    // ★★★ 4. 渲染「代表作品」 (Known For) ★★★
    if (data.known_for && data.known_for.length > 0) {
        knownForBox.innerHTML = data.known_for.map(m => createModalMovieCard(m)).join("");
    } else {
        knownForBox.innerHTML = "<p style='color:#666; font-size: 14px;'>無代表作資料</p>";
    }

    // ★★★ 5. 渲染「參與電影」 (Movies as Actor) ★★★
    // 通常 API 回傳的是 movies_as_actor
    const allMovies = data.movies_as_actor || [];
    if (allMovies.length > 0) {
        // 依照年份排序 (新的在前)
        allMovies.sort((a, b) => (b.release_year || 0) - (a.release_year || 0));
        moviesBox.innerHTML = allMovies.map(m => createModalMovieCard(m)).join("");
    } else {
        moviesBox.innerHTML = "<p style='color:#666; font-size: 14px;'>無出演紀錄</p>";
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

function closeCmdModal() {
  const m = document.getElementById("cmdModal");
  if(m) m.classList.add("hidden");
}

// 2. 修改 Enter 鍵的監聽邏輯
if (cmdInput) {
  cmdInput.addEventListener("keypress", async (e) => {
    if (e.key === "Enter") {
      const command = cmdInput.value.trim();
      if (!command) return;
      
      // 暫存指令方便查看，不立即清空，或者發送後清空看你習慣
      cmdInput.value = ""; 

      try {
        const res = await fetch(`${BACKEND_URL}/api/cmd`, { // 或 movie.js 裡的 BASE_URL
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ command: command })
        });
        
        const data = await res.json();
        
        // ★★★ 修改重點：原本是 alert，現在改成開啟自訂視窗 ★★★
        const outputBox = document.getElementById("cmdOutput");
        const modal = document.getElementById("cmdModal");
        
        if (outputBox && modal) {
            // 將 JSON 轉成漂亮的字串 (縮排 2 格)
            outputBox.textContent = JSON.stringify(data, null, 2);
            modal.classList.remove("hidden");
        } else {
            // 如果忘記加 HTML，就還是彈出 alert 當備案
            alert(JSON.stringify(data, null, 2));
        }
        // ★★★ 修改結束 ★★★

      } catch (err) {
        alert("指令發送失敗：" + err.message);
      }
    }
  });
}
// ★★★ 產生 Modal 內的電影小卡片 HTML ★★★
function createModalMovieCard(m) {
  const poster = m.poster_url || "No_image_available.png";
  const title = m.title || "未知片名";
  const year = m.release_year || "----";
  const rating = m.rating ? `⭐ ${m.rating}` : "";

  // 這裡使用與首頁一致的樣式 (.movie-card)
  // 注意：onclick 指向 goMovieDetail
  return `
    <div class="movie-card" onclick="goMovieDetail(${m.movie_id})">
      <img src="${poster}" class="movie-poster" alt="${title}">
      <div class="movie-title">${title}</div>
      <div class="movie-meta">${year}</div>
      <div class="movie-rating">${rating}</div>
    </div>
  `;
}
// 初始化
loadTrending();