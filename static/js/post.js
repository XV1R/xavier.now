let ws = null;
let config = {};
let postContent = null;

function initPost(options) {
    config = options;
    postContent = document.getElementById("post-content");

    if (config.isLive) {
        connectWebSocket();
    }

    if (config.isAdmin && config.isLive) {
        setupAdminEditor();
    }
}

function connectWebSocket() {
    ws = new WebSocket(config.wsUrl);

    ws.onopen = function() {
        ws.send(JSON.stringify({ type: "get_content" }));
    };

    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        handleMessage(data);
    };

    ws.onclose = function() {
        setTimeout(connectWebSocket, 3000);
    };

    ws.onerror = function(error) {
        console.error("WebSocket error:", error);
    };
}

function handleMessage(data) {
    switch (data.type) {
        case "content":
            if (!config.isAdmin) {
                postContent.textContent = data.content;
            }
            break;
        case "update":
            if (!config.isAdmin) {
                postContent.textContent = data.content;
            }
            break;
        case "viewer_count":
            updateViewerCount(data.count);
            break;
    }
}

function setupAdminEditor() {
    let timeout = null;

    postContent.addEventListener("input", function() {
        clearTimeout(timeout);
        timeout = setTimeout(function() {
            sendUpdate(postContent.textContent);
        }, 100);
    });
}

function sendUpdate(content) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            type: "update",
            content: content
        }));
    }
}

function updateViewerCount(count) {
    const el = document.getElementById("viewer-count");
    if (el) {
        el.textContent = count > 0 ? `${count} watching` : "";
    }
}
