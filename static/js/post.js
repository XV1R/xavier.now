let ws = null;
let config = {};
let postContent = null;
let cursorEl = null;

function initPost(options) {
    config = options;
    postContent = document.getElementById("post-content");

    if (config.isLive) {
        connectWebSocket();
    }

    if (config.isAdmin && config.isLive) {
        setupAdminEditor();
    } else if (config.isLive) {
        createCursorElement();
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
        case "cursor":
            if (!config.isAdmin) {
                updateCursorPosition(data.position);
            }
            break;
        case "viewer_count":
            updateViewerCount(data.count);
            break;
    }
}

function setupAdminEditor() {
    let contentTimeout = null;
    let cursorTimeout = null;

    postContent.addEventListener("input", function() {
        clearTimeout(contentTimeout);
        contentTimeout = setTimeout(function() {
            sendUpdate(postContent.textContent);
        }, 100);
    });

    document.addEventListener("selectionchange", function() {
        clearTimeout(cursorTimeout);
        cursorTimeout = setTimeout(function() {
            const position = getCursorPosition();
            if (position !== null) {
                sendCursorPosition(position);
            }
        }, 50);
    });
}

function getCursorPosition() {
    const selection = window.getSelection();
    if (!selection.rangeCount) return null;

    const range = selection.getRangeAt(0);
    if (!postContent.contains(range.startContainer)) return null;

    const preRange = document.createRange();
    preRange.selectNodeContents(postContent);
    preRange.setEnd(range.startContainer, range.startOffset);

    return preRange.toString().length;
}

function sendUpdate(content) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            type: "update",
            content: content
        }));
    }
}

function sendCursorPosition(position) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            type: "cursor",
            position: position
        }));
    }
}

function createCursorElement() {
    cursorEl = document.createElement("span");
    cursorEl.className = "admin-cursor";
    cursorEl.style.display = "none";
    document.body.appendChild(cursorEl);
}

function updateCursorPosition(position) {
    if (!cursorEl || position === null) {
        if (cursorEl) cursorEl.style.display = "none";
        return;
    }

    const text = postContent.textContent;
    if (position > text.length) position = text.length;

    const range = document.createRange();
    const textNode = postContent.firstChild;

    if (!textNode || textNode.nodeType !== Node.TEXT_NODE) {
        if (text.length === 0) {
            const rect = postContent.getBoundingClientRect();
            cursorEl.style.left = rect.left + postContent.clientLeft + "px";
            cursorEl.style.top = rect.top + postContent.clientTop + "px";
            cursorEl.style.height = "1.2em";
            cursorEl.style.display = "block";
        }
        return;
    }

    try {
        range.setStart(textNode, position);
        range.setEnd(textNode, position);

        const rect = range.getBoundingClientRect();
        if (rect.width === 0 && rect.height === 0 && position > 0) {
            range.setStart(textNode, position - 1);
            range.setEnd(textNode, position);
            const prevRect = range.getBoundingClientRect();
            cursorEl.style.left = prevRect.right + "px";
            cursorEl.style.top = prevRect.top + "px";
            cursorEl.style.height = prevRect.height + "px";
        } else {
            cursorEl.style.left = rect.left + "px";
            cursorEl.style.top = rect.top + "px";
            cursorEl.style.height = rect.height || "1.2em";
        }
        cursorEl.style.display = "block";
    } catch (e) {
        cursorEl.style.display = "none";
    }
}

function updateViewerCount(count) {
    const el = document.getElementById("viewer-count");
    if (el) {
        el.textContent = count > 0 ? `${count} watching` : "";
    }
}
