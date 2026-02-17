let voiceEnabled = true;
let lastSpeechText = "";
let speechPaused = false;
async function send(){

let input=document.getElementById("input");
let text=input.value.trim();

if(!text) return;

// show user message
addMessage(text,"user");
input.value="";

// show typing animation
showTyping();

// send to backend
let res=await fetch("/chat",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({message:text})
});

let data=await res.json();

// remove typing
removeTyping();

// show bot reply
addMessage(data.reply,"bot");
}


// ENTER KEY SUPPORT
function enter(e){
if(e.key==="Enter") send();
}


// ADD MESSAGE FUNCTION
function addMessage(text,type){

let div=document.createElement("div");
div.className="msg "+type;

if(type==="bot"){
div.innerHTML=text;
speak(text); // ✅ ADD THIS LINE
}
else{
div.innerText=text;
}

document.getElementById("messages").appendChild(div);
div.scrollIntoView({behavior:"smooth"});
}


// SHOW TYPING ANIMATION
function showTyping(){

let div=document.createElement("div");
div.className="msg bot";
div.id="typing";

div.innerHTML=`
<span class="dot"></span>
<span class="dot"></span>
<span class="dot"></span>
`;

document.getElementById("messages").appendChild(div);
div.scrollIntoView();
}



// REMOVE TYPING
function removeTyping(){
let t=document.getElementById("typing");
if(t) t.remove();
}


// Welcome message when page loads


// Welcome message when page loads
window.onload = function(){

let welcomeText = `
<b>Hello! Welcome to the Government Schemes Eligibility Assistant! 🏛️</b><br><br>

I'm here to help you discover government schemes and programs that you may be eligible for.<br><br>

<b>Here's how this works:</b><br>
• I'll ask you some questions about your personal details<br>
• Based on your answers, I'll find schemes you qualify for<br>
• I'll show how to apply and required documents<br><br>

<b>The questions will cover:</b><br>
• Age and personal info<br>
• Employment and income<br>
• Needs (healthcare, housing, education)<br>
• Benefit status<br><br>

Your information is only used to match you with schemes.<br><br>

<b>Are you ready to begin?</b><br>
Type <span style="color:#2563eb;font-weight:bold">ready</span> to start.
`;

setTimeout(()=>{
addMessage(welcomeText,"bot");
speak(welcomeText);
},600);


};
function startVoice(){

const SpeechRecognition =
window.SpeechRecognition || window.webkitSpeechRecognition;

if(!SpeechRecognition){
alert("Voice not supported in this browser");
return;
}

const recognition = new SpeechRecognition();
recognition.lang = "en-US";
recognition.start();

recognition.onresult = function(event){
document.getElementById("input").value =
event.results[0][0].transcript;
};

recognition.onerror = function(){
alert("Voice recognition error");
};

}
function resetChat(){

// STOP ANY CURRENT SPEECH
speechSynthesis.cancel();
speechPaused = true;
lastSpeechText = "";

// clear messages
document.getElementById("messages").innerHTML="";

// reset backend session
fetch("/reset",{ method:"POST" });

// show restart message
setTimeout(()=>{
addMessage("Chat restarted. Type ready to begin.","bot");
},300);

}

lucide.createIcons();
function speak(text){

if(!voiceEnabled){
lastSpeechText = text;
speechPaused = true;
return;
}

speechSynthesis.cancel();

lastSpeechText = text;
speechPaused = false;

// clean text
let clean = text.replace(/<[^>]*>?/gm,'');

// remove percentages like 25% 50% etc
clean = clean.replace(/\d+%/g,'');

// remove progress bar blocks
clean = clean.replace(/[█░]+/g,'');

// remove symbols
clean = clean.replace(/[•→]/g,'');

// remove extra spaces
clean = clean.replace(/\s+/g,' ').trim();

clean = clean.replace(/[\p{Emoji_Presentation}\p{Extended_Pictographic}]/gu,'')
.replace(/[•→█░]/g,'')
.replace(/\s+/g,' ')
.trim();

const speech = new SpeechSynthesisUtterance(clean);

// ---------- VOICE SELECTION ----------
let voices = speechSynthesis.getVoices();

// try to find female voice
let femaleVoice =
voices.find(v => v.name.toLowerCase().includes("female")) ||
voices.find(v => v.name.toLowerCase().includes("zira")) ||
voices.find(v => v.name.toLowerCase().includes("susan")) ||
voices.find(v => v.name.toLowerCase().includes("heera")) ||
voices.find(v => v.name.toLowerCase().includes("india")) ||
voices.find(v => v.lang === "en-IN");

if(femaleVoice){
speech.voice = femaleVoice;
}

// settings
speech.rate = 1.1;
speech.pitch = 1.2; // slightly higher pitch = more feminine
speech.volume = 1;

speechSynthesis.speak(speech);
}


function toggleVoice(){

voiceEnabled = !voiceEnabled;

let btn=document.getElementById("voiceBtn");

if(voiceEnabled){

btn.innerHTML='<i data-lucide="volume-2"></i>';
btn.style.background="#16a34a";

if(speechPaused && lastSpeechText){
speak(lastSpeechText);
}

}
else{

btn.innerHTML='<i data-lucide="volume-x"></i>';
btn.style.background="#ef4444";

speechSynthesis.cancel();
speechPaused = true;
}

lucide.createIcons();
}
speechSynthesis.onvoiceschanged = () => {
speechSynthesis.getVoices();
};
