from __future__ import annotations

import base64

from langchain_core.messages import HumanMessage


def png_data_url(png: bytes) -> str:
    return f"data:image/png;base64,{base64.b64encode(png).decode('ascii')}"


def build_message(prompt: str, images: list[bytes]) -> HumanMessage:
    content: list[dict[str, object]] = [{"type": "text", "text": prompt}]
    content.extend(
        {"type": "image_url", "image_url": {"url": png_data_url(image)}} for image in images
    )
    return HumanMessage(content=content)
