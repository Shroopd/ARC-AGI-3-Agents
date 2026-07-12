"""
Helpers for working with game frames.
"""

import base64
import json
from io import BytesIO
from typing import Any

import numpy as np
from arcengine import FrameData, GameAction
from PIL import Image, ImageDraw, ImageFont

COLOR_PALETTE = {
    0: (0, 0, 0),  # Black
    2: (255, 0, 0),  # Red
    4: (0, 255, 0),  # Green
    5: (128, 128, 128),  # Gray
    6: (0, 0, 255),  # Blue
    7: (255, 255, 0),  # Yellow
    8: (255, 165, 0),  # Orange
    9: (128, 0, 128),  # Purple
    10: (255, 255, 255),  # White
    11: (128, 128, 128),  # Gray
    # Top of player - 12
}
SCALE_FACTOR = 15


def extract_rect_from_render(
    b64image: str,
    x: int,
    y: int,
    width: int,
    height: int,
) -> str:
    """
    Extract rectangle from base64-encoded PNG and return as base64.

    Useful for extracting the door and key for comparison.
    """
    # Decode base64 to PIL Image
    img_data = base64.b64decode(b64image)
    img = Image.open(BytesIO(img_data))

    # Crop the rectangle
    cropped = img.crop(
        (
            x * SCALE_FACTOR,
            y * SCALE_FACTOR,
            (x + width) * SCALE_FACTOR,
            (y + height) * SCALE_FACTOR,
        )
    )

    # Convert back to base64
    buffered = BytesIO()
    cropped.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def render_frame(
    array_3d: list[list[list[int]]], description: str, with_highlights: bool = True
) -> str:
    """
    Renders a game frame to a PNG image.
    """

    # Default color (white) if number not in palette
    default_color = (255, 255, 255)

    # Convert the 3D array to a NumPy array
    np_array = np.array(array_3d[0], dtype=np.uint8)

    # Original dimensions
    orig_height, orig_width = np_array.shape

    # Create an empty RGB image with scaled dimensions
    scaled_width = (orig_width + 1) * SCALE_FACTOR
    scaled_height = (orig_height + 1) * SCALE_FACTOR

    # Add extra height for description
    description_height = 40
    img = Image.new("RGB", (scaled_width, scaled_height + description_height))
    pixels = img.load()

    with open("frame.json", "w") as f:
        f.write(json.dumps(np_array.tolist()))

    # Fill the image with colors from the palette, scaled
    for y in range(orig_height):
        for x in range(orig_width):
            color_num = np_array[y, x]
            color = COLOR_PALETTE.get(color_num, default_color)
            for i in range(SCALE_FACTOR):
                for j in range(SCALE_FACTOR):
                    pixels[
                        (x * SCALE_FACTOR + j) + SCALE_FACTOR,
                        (y * SCALE_FACTOR + i) + SCALE_FACTOR,
                    ] = color

    draw = ImageDraw.Draw(img)
    line_color = (128, 128, 128)  # Gray

    # Horizontal lines
    for k_h in range(orig_height + 1):
        y = k_h * SCALE_FACTOR
        draw.line([(0, y), (scaled_width - 1, y)], fill=line_color, width=1)
    draw.line(
        [(0, scaled_height - 1), (scaled_width - 1, scaled_height - 1)],
        fill=line_color,
        width=1,
    )

    # Vertical lines
    for k_v in range(orig_width + 1):
        x = k_v * SCALE_FACTOR
        draw.line([(x, 0), (x, scaled_height - 1)], fill=line_color, width=1)
    draw.line(
        [(scaled_width - 1, 0), (scaled_width - 1, scaled_height - 1)],
        fill=line_color,
        width=1,
    )

    font = ImageFont.load_default()
    text_color = (255, 255, 255)

    # Draw column numbers
    y_center_col_labels = SCALE_FACTOR / 2.0
    for col_idx in range(orig_width):
        x_center_col_labels = (
            col_idx * SCALE_FACTOR + (SCALE_FACTOR / 2.0)
        ) + SCALE_FACTOR
        draw.text(
            (x_center_col_labels, y_center_col_labels),
            str(col_idx),
            font=font,
            fill=text_color,
            anchor="mm",
        )

    # Draw row numbers
    x_center_row_labels = SCALE_FACTOR / 2.0
    for row_idx in range(orig_height):
        y_center_row_labels = (
            row_idx * SCALE_FACTOR + (SCALE_FACTOR / 2.0)
        ) + SCALE_FACTOR
        draw.text(
            (x_center_row_labels, y_center_row_labels),
            str(row_idx),
            font=font,
            fill=text_color,
            anchor="mm",
        )

    # Draw highlights
    if with_highlights:
        add_highlight(
            draw,
            ((2, 2), (47, 5)),
            "Health",
        )
        add_highlight(
            draw,
            ((52, 1), (64, 5)),
            "Lives",
        )

        found_player = False
        found_door = False
        found_rotator = False
        for y in range(orig_height):
            if found_player and found_door and found_rotator:
                break
            for x in range(orig_width):
                if np_array[y, x] == 12 and not found_player:
                    found_player = True
                    add_highlight(
                        draw,
                        ((x + 1, y + 1), (x + 9, y + 9)),
                        "Player",
                    )
                    break
                if np_array[y, x] == 5 and not found_door:
                    found_door = True
                    add_highlight(
                        draw,
                        ((x + 1, y + 1), (x + 9, y + 9)),
                        "Door",
                    )
                    break
                if (
                    np_array[y, x] == 9
                    and np_array[y - 1, x] == 3
                    and not found_rotator
                ):
                    found_rotator = True
                    add_highlight(
                        draw,
                        ((x + 1, y + 1), (x + 9, y + 9)),
                        "Rotator",
                    )
                    break

        add_highlight(draw, ((2, 55), (11, 64)), "Key")

    # Add description text at the bottom
    description_y = scaled_height + (description_height / 2)
    draw.text(
        (scaled_width / 2, description_y),
        description,
        font=font,
        fill=text_color,
        anchor="mm",
    )

    # Convert image to base64
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

    return img_str


def add_highlight(
    draw: ImageDraw.ImageDraw,
    coords: ImageDraw.Coords,
    label: str,
) -> None:
    (x1, y1), (x2, y2) = coords

    draw.rectangle(
        (
            (x1 * SCALE_FACTOR + 1, y1 * SCALE_FACTOR + 1),
            (x2 * SCALE_FACTOR - 1, y2 * SCALE_FACTOR - 1),
        ),
        fill=None,
        outline=(255, 0, 0),
        width=4,
    )

    # Text label
    draw.rectangle(
        (
            (((x1 + x2) / 2 - 2) * SCALE_FACTOR, (y2 + 0.25) * SCALE_FACTOR),
            (((x1 + x2) / 2 + 2) * SCALE_FACTOR, (y2 + 2) * SCALE_FACTOR),
        ),
        fill=(0, 0, 0),
        outline=None,
    )
    draw.text(
        ((x1 + x2) / 2 * SCALE_FACTOR, (y2 + 1) * SCALE_FACTOR),
        label,
        font=ImageFont.load_default(size=16),
        fill=(255, 255, 255),
        anchor="mm",
    )


def g2im(g: list[list[list[int]]]) -> bytes:
    C = [
        (0, 0, 0),
        (0, 0, 170),
        (0, 170, 0),
        (0, 170, 170),
        (170, 0, 0),
        (170, 0, 170),
        (170, 85, 0),
        (170, 170, 170),
        (85, 85, 85),
        (85, 85, 255),
        (85, 255, 85),
        (85, 255, 255),
        (255, 85, 85),
        (255, 85, 255),
        (255, 255, 85),
        (255, 255, 255),
    ]

    h, w = len(g[0]), len(g[0][0])
    good = [block for block in g if len(block) == h and len(block[0]) == w]
    n = len(good)
    s = 5 * (n > 1)
    W = w * n + s * (n - 1)

    im = Image.new("RGB", (W, h), "white")
    px = im.load()
    for i, block in enumerate(good):
        ox = i * (w + s)
        for y, row in enumerate(block):
            for x, val in enumerate(row):
                px[ox + x, y] = C[val & 15]

    buf = BytesIO()
    im.save(buf, "PNG")
    return buf.getvalue()


def format_frame(latest_frame: FrameData, as_image: bool) -> list[dict[str, Any]]:
    img = g2im(latest_frame.frame) if latest_frame.frame else None
    if as_image and img:
        frame_block = {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{base64.b64encode(img).decode('ascii')}",
            },
        }
    else:
        lines = []
        for i, block in enumerate(latest_frame.frame):
            lines.append(f"Grid {i}:")
            for row in block:
                lines.append(f"  {row}")
            lines.append("")
        frame_block = {"type": "text", "text": "\n".join(lines)}
    return [
        {
            "type": "text",
            "text": f"""# State:
{latest_frame.state.name}

# Score:
{latest_frame.score}

# Frame:
""",
        },
        frame_block,
        {
            "type": "text",
            "text": """
# TURN:
Reply with a few sentences of plain-text strategy observation about the frame to inform your next action.""",
        },
    ]


# ---------------------------------------------------------------------------
# Preserved independent utilities from the removed LLM-agent files
# ---------------------------------------------------------------------------

_RGBA_PALETTE: list[tuple[int, int, int, int]] = [
    (0xFF, 0xFF, 0xFF, 0xFF),  # 0 White
    (0xCC, 0xCC, 0xCC, 0xFF),  # 1 Off-white
    (0x99, 0x99, 0x99, 0xFF),  # 2 Neutral light
    (0x66, 0x66, 0x66, 0xFF),  # 3 Neutral
    (0x33, 0x33, 0x33, 0xFF),  # 4 Off-black
    (0x00, 0x00, 0x00, 0xFF),  # 5 Black
    (0xE5, 0x3A, 0xA3, 0xFF),  # 6 Magenta
    (0xFF, 0x7B, 0xCC, 0xFF),  # 7 Magenta light
    (0xF9, 0x3C, 0x31, 0xFF),  # 8 Red
    (0x1E, 0x93, 0xFF, 0xFF),  # 9 Blue
    (0x88, 0xD8, 0xF1, 0xFF),  # 10 Blue light
    (0xFF, 0xDC, 0x00, 0xFF),  # 11 Yellow
    (0xFF, 0x85, 0x1B, 0xFF),  # 12 Orange
    (0x92, 0x12, 0x31, 0xFF),  # 13 Maroon
    (0x4F, 0xCC, 0x30, 0xFF),  # 14 Green
    (0xA3, 0x56, 0xD6, 0xFF),  # 15 Purple
]


def _validate_grid_64(grid: list[list[int]]) -> None:
    if len(grid) != 64 or any(len(row) != 64 for row in grid):
        raise ValueError("Grid must be 64×64.")
    if any(cell not in range(16) for row in grid for cell in row):
        raise ValueError("Grid values must be integers 0–15.")


def grid_2d_to_pil(grid: list[list[int]]) -> Image.Image:
    _validate_grid_64(grid)
    raw = bytearray()
    for row in grid:
        for idx in row:
            raw.extend(_RGBA_PALETTE[idx])
    img = Image.frombytes("RGBA", (64, 64), bytes(raw))
    img = img.resize((128, 128), Image.NEAREST)
    return img


def pil_to_base64(img: Image.Image) -> str:
    buffer = BytesIO()
    img.save(buffer, format="PNG", optimize=True)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def image_diff(
    img_a: Image.Image,
    img_b: Image.Image,
    highlight_rgb: tuple[int, int, int] = (255, 0, 0),
) -> Image.Image:
    a = np.asarray(img_a.convert("RGB"))
    b = np.asarray(img_b.convert("RGB"))
    if a.shape != b.shape:
        raise ValueError(
            f"Images must have the same dimensions; got {a.shape} vs {b.shape}"
        )
    diff_mask = np.any(a != b, axis=-1)
    if not diff_mask.any():
        return Image.new("RGB", (a.shape[1], a.shape[0]), (0, 0, 0))
    diff_img = np.zeros_like(a)
    diff_img[diff_mask] = highlight_rgb
    return Image.fromarray(diff_img)


human_actions: dict[GameAction, str] = {
    GameAction.ACTION1: "Move Up",
    GameAction.ACTION2: "Move Down",
    GameAction.ACTION3: "Move Left",
    GameAction.ACTION4: "Move Right",
    GameAction.ACTION5: "Perform Action",
    GameAction.ACTION6: "Click object on screen, make sure to describe object and its relative, not absolute, position",
    GameAction.ACTION7: "Undo",
}


def get_human_inputs_from(available_actions: list[GameAction]) -> str:
    s = ""
    for action in available_actions:
        if action in human_actions:
            s += "\n" + human_actions[action]
    return s


def grids_to_pil(grid: list[list[list[int]]]) -> Image.Image:
    color_map = [
        (0, 0, 0),
        (0, 0, 170),
        (0, 170, 0),
        (0, 170, 170),
        (170, 0, 0),
        (170, 0, 170),
        (170, 85, 0),
        (170, 170, 170),
        (85, 85, 85),
        (85, 85, 255),
        (85, 255, 85),
        (85, 255, 255),
        (255, 85, 85),
        (255, 85, 255),
        (255, 255, 85),
        (255, 255, 255),
    ]
    height = len(grid[0])
    width = len(grid[0][0])
    num_layers = len(grid)
    separator_width = 5 if num_layers > 1 else 0
    total_width = (width * num_layers) + (separator_width * (num_layers - 1))
    image = Image.new("RGB", (total_width, height), "white")
    pixels = image.load()
    for i, grid_layer in enumerate(grid):
        if len(grid_layer) != height or len(grid_layer[0]) != width:
            continue
        offset_x = i * (width + separator_width)
        for y in range(height):
            for x in range(width):
                color_index = grid_layer[y][x] % 16
                pixels[x + offset_x, y] = color_map[color_index]
    return image


def render_grid_with_zones(
    grid: list[list[int]], cell_size: int = 40, zone_size: int = 16
) -> bytes:
    if not grid or not grid[0]:
        img = Image.new("RGB", (200, 200), color="black")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()
    height = len(grid)
    width = len(grid[0])
    img = Image.new("RGB", (width * cell_size, height * cell_size), color="white")
    draw = ImageDraw.Draw(img)
    key_colors = {
        0: "#FFFFFF",
        1: "#CCCCCC",
        2: "#999999",
        3: "#666666",
        4: "#333333",
        5: "#000000",
        6: "#E53AA3",
        7: "#FF7BCC",
        8: "#F93C31",
        9: "#1E93FF",
        10: "#88D8F1",
        11: "#FFDC00",
        12: "#FF851B",
        13: "#921231",
        14: "#4FCC30",
        15: "#A356D6",
    }
    for y in range(height):
        for x in range(width):
            color = key_colors.get(grid[y][x], "#888888")
            draw.rectangle(
                [
                    x * cell_size,
                    y * cell_size,
                    (x + 1) * cell_size,
                    (y + 1) * cell_size,
                ],
                fill=color,
                outline="#000000",
                width=1,
            )
    for y in range(0, height, zone_size):
        for x in range(0, width, zone_size):
            font = ImageFont.load_default()
            draw.text(
                (x * cell_size + 2, y * cell_size + 2),
                f"({x},{y})",
                fill="#FFFFFF",
                font=font,
            )
            zone_w = min(zone_size, width - x) * cell_size
            zone_h = min(zone_size, height - y) * cell_size
            draw.rectangle(
                [
                    x * cell_size,
                    y * cell_size,
                    x * cell_size + zone_w,
                    y * cell_size + zone_h,
                ],
                fill=None,
                outline="#FFD700",
                width=2,
            )
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()
