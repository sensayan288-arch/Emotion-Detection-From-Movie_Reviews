const $ = (id) => document.getElementById(id);
let movies = [];
let selected = null;

const palette = {
  joy: "#e8b65d", sadness: "#83a9e8", anger: "#e47c69",
  fear: "#ad91dc", surprise: "#64c5b2", neutral: "#9aa0ad"
};
const label = (value = "neutral") => value.charAt(0).toUpperCase() + value.slice(1);

function toast(message) {
  $("toast").textContent = message;
  $("toast").classList.add("show");
  setTimeout(() => $("toast").classList.remove("show"), 3200);
}
function escapeHtml(value = "") {
  return String(value).replace(/[&<>"']/g, char => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[char]);
}
function openModal() {
  $("reviewModal").classList.add("open");
  $("reviewModal").setAttribute("aria-hidden", "false");
  $("reviewInput").focus();
}
function closeModal() {
  $("reviewModal").classList.remove("open");
  $("reviewModal").setAttribute("aria-hidden", "true");
}
function showLanding() {
  $("landingScreen").hidden = false;
  $("movieDashboard").hidden = true;
  selected = null;
  document.querySelectorAll(".movie-item").forEach(item => item.classList.remove("active"));
}

function showMovie(movie) {
  selected = movie;
  $("landingScreen").hidden = true;
  $("movieDashboard").hidden = false;
  $("filmEyebrow").textContent = "NOW EXPLORING · " + movie.year;
  $("filmTitle").textContent = movie.title;
  $("filmDescription").textContent = movie.description;
  $("filmGenre").textContent = movie.genre;

  const backdrop = $("filmBackdrop");
  if (movie.backdrop_path) {
    backdrop.style.backgroundImage = `linear-gradient(90deg, #111116 0%, #111116d9 45%, #11111655 100%), url("${movie.backdrop_path}")`;
    backdrop.classList.add("has-image");
  } else {
    backdrop.style.backgroundImage = "";
    backdrop.classList.remove("has-image");
  }

  $("predictionWord").textContent = movie.review_count ? label(movie.predicted_emotion) : "No reviews";
  $("predictionWord").style.color = palette[movie.predicted_emotion] || "#d5a64e";
  $("signalText").textContent = movie.review_count
    ? movie.leading_count + " of " + movie.review_count + " reviews"
    : "No TMDB reviews available for this title";
  $("ringValue").textContent = movie.review_count ? movie.leading_percent + "%" : "—";
  $("reviewCount").textContent = movie.review_count;
  $("reviewCountFoot").textContent = movie.review_count + " REVIEWS SCORED";

  $("distribution").innerHTML = Object.entries(movie.distribution).map(([emotion, pct]) =>
    '<div class="emotion-row"><span>' + label(emotion) +
    '</span><div class="track"><div class="fill" style="width:' + pct +
    '%;background:' + palette[emotion] + '"></div></div><b>' + pct + '%</b></div>'
  ).join("");

  $("reviewsList").innerHTML = movie.reviews.length
    ? movie.reviews.map(review =>
      '<article class="review-card"><div class="review-top"><b>@' +
      escapeHtml(review.user) + '</b><span style="color:' +
      (palette[review.emotion] || "#aaa") + '">' + escapeHtml(label(review.emotion)) +
      '</span></div><p>' + escapeHtml(review.text) + '</p></article>'
    ).join("")
    : '<p class="empty-reviews">TMDB has no English reviews available for this movie yet.</p>';

  document.querySelectorAll(".movie-item").forEach(item =>
    item.classList.toggle("active", item.dataset.id === movie.id)
  );
}

function renderList(query = "") {
  const filtered = movies.filter(movie =>
    movie.title.toLowerCase().includes(query.toLowerCase())
  );
  $("movieList").innerHTML = filtered.map(movie =>
    '<button class="movie-item" data-id="' + escapeHtml(movie.id) + '">' +
    (movie.poster_path
      ? '<img class="movie-cover" src="' + escapeHtml(movie.poster_path) + '" alt="" loading="lazy">'
      : '<span class="movie-cover movie-cover-fallback">✦</span>') +
    '<span><b>' + escapeHtml(movie.title) + '</b><small>' +
    escapeHtml(movie.year) + ' · ' + escapeHtml(movie.genre) +
    '</small></span></button>'
  ).join("") || '<div class="loading">No films found.</div>';

  document.querySelectorAll(".movie-item").forEach(item => {
    item.addEventListener("click", () => {
      const movie = movies.find(candidate => candidate.id === item.dataset.id);
      if (movie) showMovie(movie);
    });
  });
  $("movieCount").textContent = String(movies.length).padStart(2, "0");
}

async function loadMovies() {
  $("movieList").innerHTML = '<div class="loading">Loading movies from TMDB…</div>';
  try {
    const response = await fetch("/api/movies");
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Could not load movies.");
    movies = data;
    renderList($("movieSearch").value);
    if (!movies.length) $("movieList").innerHTML = '<div class="loading">TMDB returned no movies.</div>';
  } catch (error) {
    $("movieList").innerHTML =
      '<div class="loading">' + escapeHtml(error.message || "Movie library unavailable.") +
      '<br><br>Check your TMDB_API_KEY setting and try again.</div>';
    toast(error.message || "Could not load movies.");
  }
}

$("movieSearch").addEventListener("input", event => renderList(event.target.value));
["analyzeNav", "newReviewBtn", "landingAnalyzeBtn"].forEach(id =>
  $(id).addEventListener("click", openModal)
);
$("exploreMoviesBtn").addEventListener("click", () => {
  if (movies[0]) showMovie(movies[0]);
  else toast("Movie library is still loading.");
});
$("libraryNav").addEventListener("click", showLanding);
$("closeModal").addEventListener("click", closeModal);
$("reviewModal").addEventListener("click", event => {
  if (event.target === $("reviewModal")) closeModal();
});
$("reviewInput").addEventListener("input", event =>
  $("charCount").textContent = event.target.value.length + " / 5000"
);
$("analyzeButton").addEventListener("click", async () => {
  const review = $("reviewInput").value.trim();
  if (!review) return toast("Please enter a review first.");

  $("analyzeButton").disabled = true;
  $("analyzeButton").textContent = "Analysing…";
  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({review})
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Analysis failed.");
    $("quickResult").classList.add("visible");
    $("quickResult").innerHTML =
      '<div class="result-label">PREDICTED EMOTION</div><div class="result-emotion" style="color:' +
      (palette[data.predicted_emotion] || "#d5a64e") + '">' +
      escapeHtml(data.emotion_label) + '</div><div class="result-review">' +
      escapeHtml(data.review) + '</div>';
  } catch (error) {
    toast(error.message);
  } finally {
    $("analyzeButton").disabled = false;
    $("analyzeButton").textContent = "Analyze emotion ↗";
  }
});

loadMovies();
