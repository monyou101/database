const API_KEY = "b2028d2c10f5244b89b1f5e0bb482db3";
const BASE_URL = "https://api.themoviedb.org/3";
const IMG_BASE = "https://image.tmdb.org/t/p/w500";

function imgUrl(path) {
  if (!path) return "https://via.placeholder.com/300x450?text=No+Image";
  return `${IMG_BASE}${path}`;
}

function getQueryId() {
  const params = new URLSearchParams(window.location.search);
  return params.get("id");
}

async function loadMovieDetail() {
  const id = getQueryId();
  if (!id) return;

  try {
    const url = `${BASE_URL}/movie/${id}?api_key=${API_KEY}&language=zh-TW&append_to_response=credits,recommendations`;
    const res = await fetch(url);
    const data = await res.json();

    renderMovieDetail(data);
    renderCast((data.credits && data.credits.cast) || []);
    renderSimilar((data.recommendations && data.recommendations.results) || []);
  } catch (err) {
    console.error("載入電影詳細資料失敗", err);
  }
}

function renderMovieDetail(m) {
  const poster = imgUrl(m.poster_path);
  const title = m.title || m.original_title || "未命名電影";
  const year = m.release_date ? m.release_date.slice(0, 4) : "未知年份";
  const rating = m.vote_average ? m.vote_average.toFixed(1) : "N/A";
  const runtime = m.runtime ? `${m.runtime} 分鐘` : "片長未知";
  const genres = (m.genres || []).map(g => g.name).join(" / ") || "未分類";
  const overview = m.overview || "尚無簡介。";

  // 導演（在 crew 裡找 job = Director）
  let directors = "";
  if (m.credits && m.credits.crew) {
    const ds = m.credits.crew.filter(c => c.job === "Director");
    if (ds.length > 0) {
      directors = "導演：" + ds.map(d => d.name).join("、");
    }
  }

  document.getElementById("moviePoster").src = poster;
  document.getElementById("movieTitle").textContent = title;
  document.getElementById(
    "movieMeta"
  ).textContent = `${year} · TMDB 評分 ${rating}`;
  document.getElementById("movieGenres").textContent = `類型：${genres}`;
  document.getElementById("movieOverview").textContent = overview;
  document.getElementById("movieRuntime").textContent = runtime;
  document.getElementById("movieRating").textContent = `TMDB 評分：${rating}`;
  document.getElementById("movieDirectors").textContent = directors || "";
}

function renderCast(castList) {
  const box = document.getElementById("movieCast");
  const top5 = castList.slice(0, 10);
  box.innerHTML = top5
    .map(c => {
      const photo = imgUrl(c.profile_path);
      const name = c.name || "Unknown";
      const character = c.character || "";
      return `
      <div class="person-card">
        <img src="${photo}" class="person-photo" alt="${name}">
        <div class="person-name">${name}</div>
        <div class="person-role">${character}</div>
      </div>
    `;
    })
    .join("");
}

function renderSimilar(list) {
  const box = document.getElementById("similarMovies");
  const top = list.slice(0, 15);
  if (top.length === 0) {
    box.innerHTML = `<p class="hint">沒有找到相似電影。</p>`;
    return;
  }

  box.innerHTML = top
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

// 從詳細頁再跳轉到另一部電影
function goMovieDetail(id) {
  window.location.href = `movie.html?id=${id}`;
}

loadMovieDetail();
