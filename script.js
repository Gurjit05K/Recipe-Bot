const chatInput = document.querySelector(".chat-input textarea");
const micBtn = document.querySelector(".chat-input .mic");
const sendChatBtn = document.querySelector(".chat-input .send");
const chatbox = document.querySelector(".chatbox");
const chatbotToggler = document.querySelector(".chatbot-toggler");
const chatbotCloseBtn = document.querySelector(".chatbot header .close-btn");

let userMessage, sessionId = generateSessionId(); // Unique session for each user
let isListening = false; // Flag to avoid mic double-clicks

// Helper function to generate a unique session ID
function generateSessionId() {
    return "session_" + Math.random().toString(36).substr(2, 9);
}

// Speech Recognition Setup
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition && micBtn) {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.lang = "en-US";

        micBtn.addEventListener("click", () => {
            if (isListening) return; // avoid double activation

            try {
                recognition.start();
                isListening = true;
                micBtn.classList.add("active"); // show mic is live
                console.log("🎙️ Mic started...");
            } catch (error) {
                console.error("❌ Mic start failed:", error);
            }
        });

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            chatInput.value = transcript;
            console.log("✅ Transcript:", transcript);
        };

        recognition.onerror = (event) => {
            console.error("❌ Mic error:", event.error);
        };

        recognition.onend = () => {
            isListening = false;
            micBtn.classList.remove("active");
            console.log("🛑 Mic stopped.");
        };
    } else if (micBtn) {
        micBtn.style.display = "none"; // Hide mic if not supported
        console.warn("⚠️ SpeechRecognition not supported.");
    }

// Helper function to create chat elements
const createChatLi = (message, className) => {
    const chatLi = document.createElement("li");
    chatLi.classList.add("chat", className);

    let chatContent = className === "outgoing"
        ? `<p></p>`
        : `<span class="material-icons">smart_toy</span><p></p>`;

    chatLi.innerHTML = chatContent;
    chatLi.querySelector("p").innerHTML = message;
    return chatLi;
};

// Function to send user message and get bot response
const generateResponse = async (incomingChatLi) => {
    const API_URL = "http://127.0.0.1:5000/get_recipe";
    const messageElement = incomingChatLi.querySelector("p");

    try {
        console.log("Sending request:", { message: userMessage, session_id: sessionId });

        const response = await fetch(API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: userMessage, session_id: sessionId })
        });

        const data = await response.json();
        console.log("API Response:", data);

        if (data.message) {
            messageElement.innerHTML = data.message
                .replace(/<(?!\/?(b|br)\b)[^>]*>/gi, ""); // Allow only <b> and <br>
        } else {
            throw new Error("Unexpected response format.");
        }
    } catch (error) {
        console.error("Error:", error);
        messageElement.classList.add("error");
        messageElement.textContent = "Oops! Something went wrong. Please try again.";
    } finally {
        chatbox.scrollTo(0, chatbox.scrollHeight);
    }
};

// Function to handle message sending
const handleChat = () => {
    userMessage = chatInput.value.trim();
    if (!userMessage) return;

    chatInput.value = "";
    chatbox.appendChild(createChatLi(userMessage, "outgoing"));
    chatbox.scrollTo(0, chatbox.scrollHeight);

    setTimeout(() => {
        const incomingChatLi = createChatLi("Thinking...", "incoming");
        chatbox.appendChild(incomingChatLi);
        generateResponse(incomingChatLi);
    }, 600);
};

// Event listeners for Enter key and send button
chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleChat();
    }
});

sendChatBtn.addEventListener("click", handleChat);
chatbotCloseBtn.addEventListener("click", () => document.body.classList.remove("show-chatbot"));
chatbotToggler.addEventListener("click", () => document.body.classList.toggle("show-chatbot"));
