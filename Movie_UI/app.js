// ======= TMDB 基本設定 =======
const API_KEY = "b2028d2c10f5244b89b1f5e0bb482db3";
const BASE_URL = "https://api.themoviedb.org/3";
const IMG_BASE = "https://image.tmdb.org/t/p/w500";

function imgUrl(path) {
  if (!path) return "No_image_available.png";
  return `${IMG_BASE}${path}`;
}

// ======= 搜尋電影&人物 =======
async function smartSearch() {
  const input = document.getElementById("searchInput").value.trim();
  const message = document.getElementById("searchMessage");
  const movieSection = document.getElementById("searchMovieSection");
  const peopleSection = document.getElementById("searchPeopleSection");
  const searchResultsSection = document.getElementById("searchResultsSection");

  if (!input) {
    message.textContent = "請輸入電影名稱。";
    movieSection.classList.add("hidden");
    peopleSection.classList.add("hidden");
    return;
  }

  message.textContent = "搜尋中…";
  searchResultsSection.classList.remove("hidden");

  // 電影搜尋（TMDB）
  try {
    url = `${BASE_URL}/search/movie?api_key=${API_KEY}&language=zh-TW&query=${encodeURIComponent(input)}`;
    res = await fetch(url);
    data = await res.json();
    const movieResults = (data.results || []).slice(0, 12);

    // 人物搜尋（TMDB）
    url = `${BASE_URL}/search/person?api_key=${API_KEY}&language=zh-TW&query=${encodeURIComponent(input)}`;
    res = await fetch(url);
    data = await res.json();
    const peopleResults = (data.results || []).slice(0, 12);

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

// 顯示電影（API 回傳）
function showMovieListFromAPI(list, targetId) {
  const box = document.getElementById(targetId);
  const filteredList = list.filter(m => m.release_date);
  box.innerHTML = filteredList
    .map(m => {
      const poster = imgUrl(m.poster_path);
      const year = m.release_date ? m.release_date.slice(0, 4) : "未知年份";
      const rating = m.vote_average ? m.vote_average.toFixed(1) : "N/A";
      return `
        <div class="movie-card" onclick="goMovieDetail(${m.id})">
          <img src="${poster}" class="movie-poster" alt="${m.title}">
          <div class="movie-title">${m.title}</div>
          <div class="movie-meta">${year}</div>
          <div class="movie-rating">⭐ ${rating}</div>
        </div>
      `;
    })
    .join("");
}

// 顯示人物（API 回傳）
function showPeopleListFromAPI(list, targetId) {
  const box = document.getElementById(targetId);
  const filteredList = list.filter(m => m.profile_path);
  box.innerHTML = filteredList
    .map(p => {
      const photo = imgUrl(p.profile_path);
      return `
        <div class="person-card" onclick="openPersonModal(${p.id})">
          <img src="${photo}" class="person-photo" alt="${p.name}">
          <div class="person-name">${p.name}</div>
          <div class="person-name">${p.original_name}</div>
        </div>
      `;
    })
    .join("");
}

// ======= 排行榜：今日、本週、熱映中、即將上映 =======
async function loadTrending() {
  try {
    // 今日熱門
    const dayRes = await fetch(
      `${BASE_URL}/trending/movie/day?api_key=${API_KEY}&language=zh-TW`
    );
    const dayData = await dayRes.json();
    showRankRow(dayData.results || [], "rankTodayRow");

    // 本週熱門
    const weekRes = await fetch(
      `${BASE_URL}/trending/movie/week?api_key=${API_KEY}&language=zh-TW`
    );
    const weekData = await weekRes.json();
    showRankRow(weekData.results || [], "rankWeekRow");

    // 熱映中 Now Playing
    const nowRes = await fetch(
      `${BASE_URL}/movie/now_playing?api_key=${API_KEY}&language=zh-TW&region=TW`
    );
    const nowData = await nowRes.json();
    showRankRow(nowData.results || [], "rankNowRow");

    // 即將上映 Upcoming
    const upRes = await fetch(
      `${BASE_URL}/movie/upcoming?api_key=${API_KEY}&language=zh-TW&region=TW`
    );
    const upData = await upRes.json();
    showRankRow(upData.results || [], "rankUpcomingRow");
  } catch (err) {
    console.error("載入排行榜失敗", err);
  }
}

function showRankRow(results, targetId) {
  const box = document.getElementById(targetId);
  const list = (results || []).slice(0, 15);
  box.innerHTML = list
    .map(m => {
      const poster = imgUrl(m.poster_path);
      const year = m.release_date ? m.release_date.slice(0, 4) : "未知";
      const rating = m.vote_average ? m.vote_average.toFixed(1) : "N/A";
      return `
        <div class="rank-card" onclick="goMovieDetail(${m.id})">
          <img src="${poster}" class="rank-poster" alt="${m.title}">
          <div class="rank-title">${m.title}</div>
          <div class="rank-meta">${year}</div>
          <div class="rank-rating">⭐ ${rating}</div>
        </div>
      `;
    })
    .join("");
}

// ======= 人物 Modal（假資料） =======
function openPersonModal(personId) {
  const data = personMap[personId];
  if (!data) return;

  document.getElementById("personName").textContent = data.name;
  document.getElementById("personPhoto").src = data.photo;
  document.getElementById("personBirth").textContent =
    "生日：" + (data.birth || "未知");
  document.getElementById("personPlace").textContent =
    "出生地：" + (data.place || "未知");
  document.getElementById("personBio").textContent =
    data.bio || "尚無簡介。";

  document.getElementById("personKnownFor").innerHTML = (data.known_for || [])
    .map(
      m => `
    <div class="movie-card">
      <img src="${m.poster}" class="movie-poster">
      <div class="movie-title">${m.title}</div>
      <div class="movie-meta">${m.year}</div>
      <div class="movie-rating">⭐ ${m.rating}</div>
    </div>
  `
    )
    .join("");

  document.getElementById("personMovies").innerHTML = (data.movies || [])
    .map(
      m => `
    <div class="movie-card">
      <img src="${m.poster}" class="movie-poster">
      <div class="movie-title">${m.title}</div>
      <div class="movie-meta">${m.year}</div>
      <div class="movie-rating">⭐ ${m.rating}</div>
    </div>
  `
    )
    .join("");

  document.getElementById("personModal").classList.remove("hidden");
}

function closePersonModal() {
  document.getElementById("personModal").classList.add("hidden");
}

// ======= 跳轉到電影詳細頁 =======
function goMovieDetail(id) {
  window.location.href = `movie.html?id=${id}`;
}

// ======= 初始化 =======
loadTrending();