// ======= TMDB 基本設定 =======
const API_KEY = "b2028d2c10f5244b89b1f5e0bb482db3";
const BASE_URL = "https://api.themoviedb.org/3";
const IMG_BASE = "https://image.tmdb.org/t/p/w500";

function imgUrl(path) {
  if (!path) return "https://via.placeholder.com/300x450?text=No+Image";
  return `${IMG_BASE}${path}`;
}

// ======= 人物假資料（演員 / 導演 for Modal） =======
const mockPeople = [
  {
    id: "p1",
    name: "Leonardo DiCaprio",
    roleType: "Actor",
    photo: "https://image.tmdb.org/t/p/w500/wo2hJpn04vbtmh0B9utCFdsQhxM.jpg",
    birth: "1974-11-11",
    place: "Los Angeles, California, USA",
    bio: "Leonardo DiCaprio is an American actor and film producer, known for working with directors such as Martin Scorsese and Christopher Nolan.",
    known_for: [
      {
        title: "Inception",
        year: 2010,
        rating: 8.8,
        poster: "https://image.tmdb.org/t/p/w500/qmDpIHrmpJINaRKAfWQfftjCdyi.jpg"
      },
      {
        title: "Titanic",
        year: 1997,
        rating: 7.9,
        poster: "https://image.tmdb.org/t/p/w500/9xjZS2rlVxm8SFx8kPC3aIGCOYQ.jpg"
      }
    ],
    movies: [
      {
        title: "The Revenant",
        year: 2015,
        rating: 8.0,
        poster: "https://image.tmdb.org/t/p/w500/oXUWEc5i3wYyFnL1Ycu8ppxxPvs.jpg"
      }
    ]
  },
  {
    id: "p2",
    name: "Tom Cruise",
    roleType: "Actor",
    photo: "https://image.tmdb.org/t/p/w500/8qBylBsQf4llkGrWR3qAsOtOU8O.jpg",
    birth: "1962-07-03",
    place: "Syracuse, New York, USA",
    bio: "Tom Cruise is an American actor and producer, known for his roles in the Mission: Impossible franchise and many acclaimed films.",
    known_for: [
      {
        title: "Top Gun: Maverick",
        year: 2022,
        rating: 8.3,
        poster: "https://image.tmdb.org/t/p/w500/62HCnUTziyWcpDaBO2i1DX17ljH.jpg"
      }
    ],
    movies: [
      {
        title: "Mission: Impossible - Fallout",
        year: 2018,
        rating: 7.9,
        poster: "https://image.tmdb.org/t/p/w500/AkJQpZp9WoNdj7pLYSj1L0RcMMN.jpg"
      }
    ]
  },
  {
    id: "p3",
    name: "Scarlett Johansson",
    roleType: "Actor",
    photo: "https://image.tmdb.org/t/p/w500/6NsMbJXRlDZuDzatN2akFdGuTvx.jpg",
    birth: "1984-11-22",
    place: "New York City, New York, USA",
    bio: "Scarlett Johansson is an American actress and singer. She is known for her work in both independent films and blockbusters.",
    known_for: [
      {
        title: "Avengers: Endgame",
        year: 2019,
        rating: 8.4,
        poster: "https://image.tmdb.org/t/p/w500/ulzhLuWrPK07P1YkdWQLZnQh1JL.jpg"
      }
    ],
    movies: [
      {
        title: "Lucy",
        year: 2014,
        rating: 6.4,
        poster: "https://image.tmdb.org/t/p/w500/rwn876MeqienhOVSSjtUPnwxn0Z.jpg"
      }
    ]
  },
  {
    id: "p4",
    name: "Christopher Nolan",
    roleType: "Director",
    photo: "https://image.tmdb.org/t/p/w500/k4Z0a0tSIzkn0x1pZgdKzac8Esl.jpg",
    birth: "1970-07-30",
    place: "London, England, UK",
    bio: "Christopher Nolan is a British-American film director, producer, and screenwriter, known for his complex, mind-bending narratives.",
    known_for: [
      {
        title: "Inception",
        year: 2010,
        rating: 8.8,
        poster: "https://image.tmdb.org/t/p/w500/qmDpIHrmpJINaRKAfWQfftjCdyi.jpg"
      },
      {
        title: "The Dark Knight",
        year: 2008,
        rating: 9.0,
        poster: "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg"
      }
    ],
    movies: [
      {
        title: "Interstellar",
        year: 2014,
        rating: 8.6,
        poster: "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg"
      }
    ]
  },
  {
    id: "p5",
    name: "James Cameron",
    roleType: "Director",
    photo: "https://image.tmdb.org/t/p/w500/9NAZNGL0rZtfeR0vZoYlV8aem1r.jpg",
    birth: "1954-08-16",
    place: "Kapuskasing, Ontario, Canada",
    bio: "James Cameron is a Canadian filmmaker, known for epic films and pioneering the use of visual effects.",
    known_for: [
      {
        title: "Titanic",
        year: 1997,
        rating: 7.9,
        poster: "https://image.tmdb.org/t/p/w500/9xjZS2rlVxm8SFx8kPC3aIGCOYQ.jpg"
      }
    ],
    movies: [
      {
        title: "Avatar: The Way of Water",
        year: 2022,
        rating: 7.7,
        poster: "https://image.tmdb.org/t/p/w500/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg"
      }
    ]
  },
  {
    id: "p6",
    name: "Denis Villeneuve",
    roleType: "Director",
    photo: "https://image.tmdb.org/t/p/w500/4jhqse9jQRCQXwEWgicG3v4nqCC.jpg",
    birth: "1967-10-03",
    place: "Bécancour, Québec, Canada",
    bio: "Denis Villeneuve is a Canadian filmmaker, known for his visually striking and thoughtful science fiction films.",
    known_for: [
      {
        title: "Dune: Part Two",
        year: 2024,
        rating: 8.7,
        poster: "https://image.tmdb.org/t/p/w500/8b8gkM9EJJdQjvYpJneCErYzv3v.jpg"
      }
    ],
    movies: [
      {
        title: "Blade Runner 2049",
        year: 2017,
        rating: 8.0,
        poster: "https://image.tmdb.org/t/p/w500/gajva2L0rPYkEWjzgFlBXCAVBE5.jpg"
      }
    ]
  }
];

const popularActors = [mockPeople[0], mockPeople[1], mockPeople[2]];
const popularDirectors = [mockPeople[3], mockPeople[4], mockPeople[5]];

// 建立人物 map 給 Modal 用
const personMap = {};
mockPeople.forEach(p => { personMap[p.id] = p; });

// ======= 搜尋電影（TMDB search/movie）＋ 人物假資料搜尋 =======
async function smartSearch() {
  const input = document.getElementById("searchInput").value.trim();
  const message = document.getElementById("searchMessage");
  const movieSection = document.getElementById("searchMovieSection");
  const peopleSection = document.getElementById("searchPeopleSection");

  if (!input) {
    message.textContent = "請輸入電影名稱。";
    movieSection.classList.add("hidden");
    peopleSection.classList.add("hidden");
    return;
  }

  message.textContent = "搜尋中…";

  try {
    // 電影搜尋（TMDB）
    const url = `${BASE_URL}/search/movie?api_key=${API_KEY}&language=zh-TW&query=${encodeURIComponent(
      input
    )}`;
    const res = await fetch(url);
    const data = await res.json();
    const movieResults = (data.results || []).slice(0, 12);

    // 人名搜尋（暫時用假資料：名字包含關鍵字）
    const keyword = input.toLowerCase();
    const peopleResults = mockPeople.filter(p =>
      p.name.toLowerCase().includes(keyword)
    );

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

    // 人物結果（假資料）
    if (peopleResults.length > 0) {
      peopleSection.classList.remove("hidden");
      showPeopleList(peopleResults, "peopleResults");
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
  box.innerHTML = list
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

// ======= 人物卡片（假資料） =======
function showPeopleList(list, targetId) {
  const box = document.getElementById(targetId);
  box.innerHTML = list
    .map(
      p => `
    <div class="person-card" onclick="openPersonModal('${p.id}')">
      <img src="${p.photo}" class="person-photo" alt="${p.name}">
      <div class="person-name">${p.name}</div>
      <div class="person-role">${p.roleType}</div>
    </div>
  `
    )
    .join("");
}

// ======= 受歡迎演員 / 導演（假資料） =======
function renderPopularSections() {
  showPeopleList(popularActors, "popularActors");
  showPeopleList(popularDirectors, "popularDirectors");
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
renderPopularSections();
loadTrending();
