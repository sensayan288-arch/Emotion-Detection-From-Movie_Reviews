const $ = (id) => document.getElementById(id);
let movies = [];
let selected = null;
const palette = {joy:"#e8b65d",sadness:"#83a9e8",anger:"#e47c69",fear:"#ad91dc",surprise:"#64c5b2",neutral:"#9aa0ad"};
const label = (s) => s.charAt(0).toUpperCase()+s.slice(1);
function toast(message){$("toast").textContent=message;$("toast").classList.add("show");setTimeout(()=>$("toast").classList.remove("show"),2400);}
function openModal(){$("reviewModal").classList.add("open");$("reviewModal").setAttribute("aria-hidden","false");$("reviewInput").focus();}
function closeModal(){$("reviewModal").classList.remove("open");$("reviewModal").setAttribute("aria-hidden","true");}
function showLanding(){$("landingScreen").hidden=false;$("movieDashboard").hidden=true;selected=null;document.querySelectorAll(".movie-item").forEach(x=>x.classList.remove("active"));}
function showMovie(movie){
 selected=movie;$("landingScreen").hidden=true;$("movieDashboard").hidden=false;
 $("filmEyebrow").textContent="NOW EXPLORING · "+movie.year;$("filmTitle").textContent=movie.title;
 $("filmDescription").textContent=movie.description;$("filmGenre").textContent=movie.genre;
 $("predictionWord").textContent=label(movie.predicted_emotion);$("predictionWord").style.color=palette[movie.predicted_emotion]||"#d5a64e";
 $("signalText").textContent=movie.leading_count+" of "+movie.review_count+" reviews";$("ringValue").textContent=movie.leading_percent+"%";
 $("reviewCount").textContent=movie.review_count;$("reviewCountFoot").textContent=movie.review_count+" REVIEWS SCORED";
 $("distribution").innerHTML=Object.entries(movie.distribution).map(([emotion,pct])=>'<div class="emotion-row"><span>'+label(emotion)+'</span><div class="track"><div class="fill" style="width:'+pct+'%;background:'+palette[emotion]+'"></div></div><b>'+pct+'%</b></div>').join("");
 $("reviewsList").innerHTML=movie.reviews.map(r=>'<article class="review-card"><div class="review-top"><b>@'+r.user+'</b><span style="color:'+(palette[r.emotion]||"#aaa")+'">'+label(r.emotion)+'</span></div><p>'+escapeHtml(r.text)+'</p></article>').join("");
 document.querySelectorAll(".movie-item").forEach(x=>x.classList.toggle("active",x.dataset.id===movie.id));
}
function escapeHtml(s){return s.replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
function renderList(query=""){
 const filtered=movies.filter(m=>m.title.toLowerCase().includes(query.toLowerCase()));
 $("movieList").innerHTML=filtered.map(m=>'<button class="movie-item" data-id="'+m.id+'"><span class="movie-cover">✦</span><span><b>'+m.title+'</b><small>'+m.year+' · '+m.genre+'</small></span></button>').join("")||'<div class="loading">No films found.</div>';
 document.querySelectorAll(".movie-item").forEach(el=>el.addEventListener("click",()=>showMovie(movies.find(m=>m.id===el.dataset.id))));
 $("movieCount").textContent=String(movies.length).padStart(2,"0");
}
async function loadMovies(){
 try{const res=await fetch("/api/movies");if(!res.ok)throw new Error("Could not load movies");movies=await res.json();renderList();}
 catch(err){$("movieList").textContent="Could not load the movie library. Check that the model files are installed.";toast(err.message);}
}
$("movieSearch").addEventListener("input",e=>renderList(e.target.value));
["analyzeNav","newReviewBtn","landingAnalyzeBtn"].forEach(id=>$(id).addEventListener("click",openModal));
$("exploreMoviesBtn").addEventListener("click",()=>{if(movies[0])showMovie(movies[0]);else toast("Movie library is still loading.");});
$("libraryNav").addEventListener("click",showLanding);
$("closeModal").addEventListener("click",closeModal);
$("reviewModal").addEventListener("click",e=>{if(e.target===$("reviewModal"))closeModal();});
$("reviewInput").addEventListener("input",e=>$("charCount").textContent=e.target.value.length+" / 5000");
$("analyzeButton").addEventListener("click",async()=>{
 const review=$("reviewInput").value.trim();if(!review){toast("Please enter a review first.");return;}
 $("analyzeButton").disabled=true;$("analyzeButton").textContent="Analysing…";
 try{const res=await fetch("/api/analyze",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({review})});const data=await res.json();if(!res.ok)throw new Error(data.error||"Analysis failed");
 $("quickResult").classList.add("visible");$("quickResult").innerHTML='<div class="result-label">PREDICTED EMOTION</div><div class="result-emotion" style="color:'+(palette[data.predicted_emotion]||"#d5a64e")+'">'+data.emotion_label+'</div><div class="result-review">'+escapeHtml(data.review)+'</div>';
 }catch(err){toast(err.message);}finally{$("analyzeButton").disabled=false;$("analyzeButton").textContent="Analyze emotion ↗";}
});
loadMovies();