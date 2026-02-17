import asyncio
import base64
import io
import json
import logging
import mimetypes
from typing import Optional

import requests
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile

from open_webui.config import CACHE_DIR
from open_webui.constants import ERROR_MESSAGES
from open_webui.env import ENABLE_FORWARD_USER_INFO_HEADERS

from open_webui.models.chats import Chats
from open_webui.routers.files import upload_file_handler
from open_webui.utils.auth import get_admin_user, get_verified_user
from open_webui.utils.access_control import has_permission
from open_webui.utils.headers import include_user_info_headers
from pydantic import BaseModel

log = logging.getLogger(__name__)

VIDEO_CACHE_DIR = CACHE_DIR / "video" / "generations"
VIDEO_CACHE_DIR.mkdir(parents=True, exist_ok=True)

MAX_POLL_ATTEMPTS = 120
POLL_INTERVAL_SECONDS = 5

router = APIRouter()


class VideosConfig(BaseModel):
    ENABLE_VIDEO_GENERATION: bool
    VIDEO_GENERATION_ENGINE: str
    VIDEO_GENERATION_MODEL: str

    VIDEOS_OPENAI_API_BASE_URL: str
    VIDEOS_OPENAI_API_KEY: str

    VIDEOS_GEMINI_API_BASE_URL: str
    VIDEOS_GEMINI_API_KEY: str


@router.get("/config", response_model=VideosConfig)
async def get_config(request: Request, user=Depends(get_admin_user)):
    return {
        "ENABLE_VIDEO_GENERATION": request.app.state.config.ENABLE_VIDEO_GENERATION,
        "VIDEO_GENERATION_ENGINE": request.app.state.config.VIDEO_GENERATION_ENGINE,
        "VIDEO_GENERATION_MODEL": request.app.state.config.VIDEO_GENERATION_MODEL,
        "VIDEOS_OPENAI_API_BASE_URL": request.app.state.config.VIDEOS_OPENAI_API_BASE_URL,
        "VIDEOS_OPENAI_API_KEY": request.app.state.config.VIDEOS_OPENAI_API_KEY,
        "VIDEOS_GEMINI_API_BASE_URL": request.app.state.config.VIDEOS_GEMINI_API_BASE_URL,
        "VIDEOS_GEMINI_API_KEY": request.app.state.config.VIDEOS_GEMINI_API_KEY,
    }


@router.post("/config/update")
async def update_config(
    request: Request, form_data: VideosConfig, user=Depends(get_admin_user)
):
    request.app.state.config.ENABLE_VIDEO_GENERATION = form_data.ENABLE_VIDEO_GENERATION
    request.app.state.config.VIDEO_GENERATION_ENGINE = form_data.VIDEO_GENERATION_ENGINE
    request.app.state.config.VIDEO_GENERATION_MODEL = form_data.VIDEO_GENERATION_MODEL

    request.app.state.config.VIDEOS_OPENAI_API_BASE_URL = (
        form_data.VIDEOS_OPENAI_API_BASE_URL
    )
    request.app.state.config.VIDEOS_OPENAI_API_KEY = form_data.VIDEOS_OPENAI_API_KEY

    request.app.state.config.VIDEOS_GEMINI_API_BASE_URL = (
        form_data.VIDEOS_GEMINI_API_BASE_URL
    )
    request.app.state.config.VIDEOS_GEMINI_API_KEY = form_data.VIDEOS_GEMINI_API_KEY

    return {
        "ENABLE_VIDEO_GENERATION": request.app.state.config.ENABLE_VIDEO_GENERATION,
        "VIDEO_GENERATION_ENGINE": request.app.state.config.VIDEO_GENERATION_ENGINE,
        "VIDEO_GENERATION_MODEL": request.app.state.config.VIDEO_GENERATION_MODEL,
        "VIDEOS_OPENAI_API_BASE_URL": request.app.state.config.VIDEOS_OPENAI_API_BASE_URL,
        "VIDEOS_OPENAI_API_KEY": request.app.state.config.VIDEOS_OPENAI_API_KEY,
        "VIDEOS_GEMINI_API_BASE_URL": request.app.state.config.VIDEOS_GEMINI_API_BASE_URL,
        "VIDEOS_GEMINI_API_KEY": request.app.state.config.VIDEOS_GEMINI_API_KEY,
    }


@router.get("/models")
def get_models(request: Request, user=Depends(get_verified_user)):
    try:
        if request.app.state.config.VIDEO_GENERATION_ENGINE == "openai":
            return [
                {"id": "sora", "name": "Sora"},
            ]
        elif request.app.state.config.VIDEO_GENERATION_ENGINE == "gemini":
            return [
                {"id": "veo-2.0-generate-001", "name": "Veo 2.0"},
            ]
        return []
    except Exception as e:
        raise HTTPException(status_code=400, detail=ERROR_MESSAGES.DEFAULT(e))


class CreateVideoForm(BaseModel):
    model: Optional[str] = None
    prompt: str
    n: int = 1


def get_video_model(request):
    if request.app.state.config.VIDEO_GENERATION_ENGINE == "openai":
        return (
            request.app.state.config.VIDEO_GENERATION_MODEL
            if request.app.state.config.VIDEO_GENERATION_MODEL
            else "sora"
        )
    elif request.app.state.config.VIDEO_GENERATION_ENGINE == "gemini":
        return (
            request.app.state.config.VIDEO_GENERATION_MODEL
            if request.app.state.config.VIDEO_GENERATION_MODEL
            else "veo-2.0-generate-001"
        )
    return request.app.state.config.VIDEO_GENERATION_MODEL or ""


def upload_video(request, video_data, content_type, metadata, user):
    ext = mimetypes.guess_extension(content_type) or ".mp4"
    file = UploadFile(
        file=io.BytesIO(video_data),
        filename=f"generated-video{ext}",
        headers={
            "content-type": content_type,
        },
    )
    file_item = upload_file_handler(
        request,
        file=file,
        metadata=metadata,
        process=False,
        user=user,
    )

    chat_id = metadata.get("chat_id")
    message_id = metadata.get("message_id")

    if file_item and file_item.id and chat_id and message_id:
        Chats.insert_chat_files(
            chat_id=chat_id,
            message_id=message_id,
            file_ids=[file_item.id],
            user_id=user.id,
        )

    url = request.app.url_path_for("get_file_content_by_id", id=file_item.id)
    return file_item, url


@router.post("/generations")
async def generate_videos(
    request: Request, form_data: CreateVideoForm, user=Depends(get_verified_user)
):
    if not request.app.state.config.ENABLE_VIDEO_GENERATION:
        raise HTTPException(
            status_code=403,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )

    if user.role != "admin" and not has_permission(
        user.id,
        "features.video_generation",
        request.app.state.config.USER_PERMISSIONS,
    ):
        raise HTTPException(
            status_code=403,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )

    return await video_generations(request, form_data, user=user)


async def video_generations(
    request: Request,
    form_data: CreateVideoForm,
    metadata: Optional[dict] = None,
    user=None,
):
    metadata = metadata or {}
    model = form_data.model or get_video_model(request)

    r = None
    try:
        if request.app.state.config.VIDEO_GENERATION_ENGINE == "openai":
            headers = {
                "Authorization": f"Bearer {request.app.state.config.VIDEOS_OPENAI_API_KEY}",
                "Content-Type": "application/json",
            }

            if ENABLE_FORWARD_USER_INFO_HEADERS:
                headers = include_user_info_headers(headers, user)

            data = {
                "model": model,
                "prompt": form_data.prompt,
                "n": form_data.n,
            }

            # POST to create the video generation job
            r = await asyncio.to_thread(
                requests.post,
                url=f"{request.app.state.config.VIDEOS_OPENAI_API_BASE_URL}/videos/generations",
                json=data,
                headers=headers,
            )

            r.raise_for_status()
            res = r.json()

            videos = []

            # OpenAI video API may return results directly or require polling
            if "data" in res:
                # Direct response with video data
                for video in res["data"]:
                    if video_url := video.get("url", None):
                        video_resp = await asyncio.to_thread(
                            requests.get, video_url, headers=headers
                        )
                        video_resp.raise_for_status()
                        video_data = video_resp.content
                        content_type = video_resp.headers.get(
                            "content-type", "video/mp4"
                        )
                    elif b64_data := video.get("b64_json", None):
                        video_data = base64.b64decode(b64_data)
                        content_type = "video/mp4"
                    else:
                        continue

                    _, url = upload_video(
                        request,
                        video_data,
                        content_type,
                        {**data, **metadata},
                        user,
                    )
                    videos.append({"url": url})

            elif "id" in res:
                # Async job - poll for completion
                job_id = res["id"]
                poll_url = f"{request.app.state.config.VIDEOS_OPENAI_API_BASE_URL}/videos/generations/{job_id}"

                for _ in range(MAX_POLL_ATTEMPTS):
                    await asyncio.sleep(POLL_INTERVAL_SECONDS)
                    poll_r = await asyncio.to_thread(
                        requests.get,
                        url=poll_url,
                        headers=headers,
                    )
                    poll_r.raise_for_status()
                    poll_res = poll_r.json()

                    status = poll_res.get("status", "")
                    if status == "completed":
                        for video in poll_res.get("data", poll_res.get("output", [])):
                            if video_url := video.get("url", None):
                                video_resp = await asyncio.to_thread(
                                    requests.get, video_url, headers=headers
                                )
                                video_resp.raise_for_status()
                                video_data = video_resp.content
                                content_type = video_resp.headers.get(
                                    "content-type", "video/mp4"
                                )
                            elif b64_data := video.get("b64_json", None):
                                video_data = base64.b64decode(b64_data)
                                content_type = "video/mp4"
                            else:
                                continue

                            _, url = upload_video(
                                request,
                                video_data,
                                content_type,
                                {**data, **metadata},
                                user,
                            )
                            videos.append({"url": url})
                        break
                    elif status == "failed":
                        error_msg = poll_res.get("error", "Video generation failed")
                        raise Exception(error_msg)
                else:
                    raise Exception("Video generation timed out")

            return videos

        elif request.app.state.config.VIDEO_GENERATION_ENGINE == "gemini":
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": request.app.state.config.VIDEOS_GEMINI_API_KEY,
            }

            # Use Gemini's video generation via the predict endpoint
            predict_model = f"{model}:predict"
            data = {
                "instances": [{"prompt": form_data.prompt}],
                "parameters": {
                    "sampleCount": form_data.n,
                },
            }

            r = await asyncio.to_thread(
                requests.post,
                url=f"{request.app.state.config.VIDEOS_GEMINI_API_BASE_URL}/models/{predict_model}",
                json=data,
                headers=headers,
            )

            r.raise_for_status()
            res = r.json()

            videos = []

            # Handle long-running operation response
            if "name" in res:
                # Async operation - poll for completion
                operation_name = res["name"]
                poll_url = f"{request.app.state.config.VIDEOS_GEMINI_API_BASE_URL}/operations/{operation_name}"

                for _ in range(MAX_POLL_ATTEMPTS):
                    await asyncio.sleep(POLL_INTERVAL_SECONDS)
                    poll_r = await asyncio.to_thread(
                        requests.get,
                        url=poll_url,
                        headers=headers,
                    )
                    poll_r.raise_for_status()
                    poll_res = poll_r.json()

                    if poll_res.get("done", False):
                        response = poll_res.get("response", {})
                        for video in response.get(
                            "generateVideoResponse", response.get("predictions", [])
                        ):
                            if b64_data := video.get("bytesBase64Encoded", None):
                                video_data = base64.b64decode(b64_data)
                                content_type = video.get("mimeType", "video/mp4")
                                _, url = upload_video(
                                    request,
                                    video_data,
                                    content_type,
                                    {**data, **metadata},
                                    user,
                                )
                                videos.append({"url": url})
                            elif video_url := video.get("uri", None):
                                video_resp = await asyncio.to_thread(
                                    requests.get, video_url, headers=headers
                                )
                                video_resp.raise_for_status()
                                video_data = video_resp.content
                                content_type = video_resp.headers.get(
                                    "content-type", "video/mp4"
                                )
                                _, url = upload_video(
                                    request,
                                    video_data,
                                    content_type,
                                    {**data, **metadata},
                                    user,
                                )
                                videos.append({"url": url})
                        break
                    elif poll_res.get("error"):
                        raise Exception(
                            poll_res["error"].get(
                                "message", "Video generation failed"
                            )
                        )
                else:
                    raise Exception("Video generation timed out")

            elif "predictions" in res:
                # Direct response
                for video in res["predictions"]:
                    if b64_data := video.get("bytesBase64Encoded", None):
                        video_data = base64.b64decode(b64_data)
                        content_type = video.get("mimeType", "video/mp4")
                        _, url = upload_video(
                            request,
                            video_data,
                            content_type,
                            {**data, **metadata},
                            user,
                        )
                        videos.append({"url": url})

            return videos

    except Exception as e:
        error = e
        if r is not None:
            try:
                data = r.json()
                if "error" in data:
                    error = data["error"].get("message", data["error"])
            except Exception:
                error = r.text
        raise HTTPException(status_code=400, detail=ERROR_MESSAGES.DEFAULT(error))
