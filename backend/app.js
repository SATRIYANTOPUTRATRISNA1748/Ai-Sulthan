export function initChat() {
    const form = document.getElementById('chat-form');
    const input = document.getElementById('message-input');
    const chatBox = document.getElementById('chat-box');

    if (!form || !input || !chatBox) {
        console.warn("⚠️ Elemen chat tidak ditemukan di halaman!");
        return;
    }

    //form auto refresh (save if listener error)
    form.setAttribute("novalidate", "true");

    form.addEventListener('submit', async function (e) {
        e.preventDefault();       
        e.stopPropagation();      
        const message = input.value.trim();

        if (!message) return;

        addMessage(message, 'user');
        input.value = '';

        // Answer Animation
        const typingEl = addMessage('Sultan Sedang Meneliti...', 'bot', true);

        try {
            const res = await fetch('http://10.86.103.159:5000/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message }),
                cache: "no-store"
            });

            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();

            typingEl.remove();
            typeWriter(data.reply || "⚠️ Tidak ada respons dari server.", 'bot');
        } catch (err) {
            console.error("Chat error:", err);
            typingEl.remove();
            addMessage('❌ Error: ' + err.message, 'bot');
        }
    });
}

function addMessage(text, sender, isTyping = false) {
    const chatBox = document.getElementById('chat-box');
    const msg = document.createElement('div');
    msg.classList.add('message', sender);
    if (isTyping) msg.classList.add('typing');
    msg.textContent = text;
    chatBox.appendChild(msg);
    chatBox.scrollTop = chatBox.scrollHeight;
    return msg;
}

function typeWriter(text, sender) {
    let i = 0;
    const chatBox = document.getElementById('chat-box');
    const msg = document.createElement('div');
    msg.classList.add('message', sender);
    chatBox.appendChild(msg);

    function typing() {
        if (i < text.length) {
            msg.textContent += text.charAt(i);
            i++;
            chatBox.scrollTop = chatBox.scrollHeight;
            setTimeout(typing, 25);
        }
    }
    typing();
}

// Chat actived ware by page already
document.addEventListener('DOMContentLoaded', () => {
    try {
        initChat();
    } catch (e) {
        console.error("Gagal inisialisasi chat:", e);
    }

});
