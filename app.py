import json
import os
import secrets
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.websockets import WebSocket, WebSocketDisconnect
from itsdangerous import URLSafeSerializer, BadSignature

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(32))

app = FastAPI()
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

serializer = URLSafeSerializer(SECRET_KEY)
current_content = ""

SESSION_COOKIE = "session"


class ConnectionManager:
    def __init__(self):
        self.viewers: list[WebSocket] = []
        self.admin: WebSocket | None = None

    async def connect_viewer(self, websocket: WebSocket):
        await websocket.accept()
        self.viewers.append(websocket)
        await self.broadcast_viewer_count()

    async def connect_admin(self, websocket: WebSocket):
        await websocket.accept()
        self.admin = websocket
        await self.broadcast_viewer_count()

    def disconnect_viewer(self, websocket: WebSocket):
        if websocket in self.viewers:
            self.viewers.remove(websocket)

    def disconnect_admin(self):
        self.admin = None

    @property
    def viewer_count(self) -> int:
        return len(self.viewers)

    async def broadcast_viewer_count(self):
        message = json.dumps({"type": "viewer_count", "count": self.viewer_count})
        if self.admin:
            try:
                await self.admin.send_text(message)
            except Exception:
                pass
        for viewer in self.viewers:
            try:
                await viewer.send_text(message)
            except Exception:
                pass

    async def broadcast_content(self, content: str):
        message = json.dumps({"type": "update", "content": content})
        for viewer in self.viewers:
            try:
                await viewer.send_text(message)
            except Exception:
                pass

    async def broadcast_cursor(self, position: int):
        message = json.dumps({"type": "cursor", "position": position})
        for viewer in self.viewers:
            try:
                await viewer.send_text(message)
            except Exception:
                pass

    async def send_content(self, websocket: WebSocket, content: str):
        message = json.dumps({"type": "content", "content": content})
        await websocket.send_text(message)


manager = ConnectionManager()


def get_current_user(request: Request) -> str | None:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    try:
        data = serializer.loads(token)
        return data.get("username")
    except BadSignature:
        return None


def is_admin(request: Request) -> bool:
    return get_current_user(request) == ADMIN_USERNAME


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    admin = is_admin(request)
    ws_token = request.cookies.get(SESSION_COOKIE) if admin else ""
    return templates.TemplateResponse(
        "post.html",
        {
            "request": request,
            "title": "xavier.now",
            "date": date.today().strftime("%B %d, %Y"),
            "content": current_content,
            "is_admin": admin,
            "is_live": True,
            "ws_token": ws_token,
            "active_tab": "today",
        },
    )


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if is_admin(request):
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": None},
    )


@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        token = serializer.dumps({"username": username})
        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie(
            key=SESSION_COOKIE,
            value=token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=86400,
        )
        return response

    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": "Invalid credentials"},
        status_code=401,
    )


@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie(SESSION_COOKIE)
    return response


@app.get("/posts", response_class=HTMLResponse)
async def posts_list(request: Request):
    return templates.TemplateResponse(
        "posts.html",
        {
            "request": request,
            "title": "Archive - xavier.now",
            "posts": [],
            "active_tab": "posts",
        },
    )


@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse(
        "about.html",
        {
            "request": request,
            "title": "About - xavier.now",
            "active_tab": "about",
        },
    )


def get_user_from_token(token: str | None) -> str | None:
    if not token:
        return None
    try:
        data = serializer.loads(token)
        return data.get("username")
    except BadSignature:
        return None


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str | None = Query(default=None)):
    global current_content
    user = get_user_from_token(token)
    is_admin_user = user == ADMIN_USERNAME

    if is_admin_user:
        await manager.connect_admin(websocket)
    else:
        await manager.connect_viewer(websocket)

    try:
        await manager.send_content(websocket, current_content)

        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            msg_type = message.get("type")
            if msg_type == "update" and is_admin_user:
                current_content = message.get("content", "")
                await manager.broadcast_content(current_content)
            elif msg_type == "cursor" and is_admin_user:
                position = message.get("position", 0)
                await manager.broadcast_cursor(position)
    except WebSocketDisconnect:
        pass
    finally:
        if is_admin_user:
            manager.disconnect_admin()
        else:
            manager.disconnect_viewer(websocket)
        await manager.broadcast_viewer_count()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
