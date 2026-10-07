"""تولید مختصات SVG برای نمودارها (بدون وابستگی به CDN — آفلاین‌سازگار)."""
from __future__ import annotations

from decimal import Decimal

from .utils import fa, num


def sparkline(values, width: int = 120, height: int = 30, padding: int = 4) -> str:
    values = [float(v or 0) for v in values]
    if len(values) < 2:
        return ""
    top, bottom = max(values), min(values)
    span = (top - bottom) or 1
    step = (width - 2 * padding) / (len(values) - 1)
    points = []
    for index, value in enumerate(values):
        x = padding + index * step
        y = height - padding - ((value - bottom) / span) * (height - 2 * padding)
        points.append(f"{x:.1f},{y:.1f}")
    return " ".join(points)


def area_chart(values, labels, *, width=820, height=250, ticks=5, force_max=None,
               value_suffix="") -> dict:
    values = [float(v or 0) for v in values]
    labels = list(labels)
    if not values:
        return {"empty": True}
    pad_top, pad_bottom, pad_left, pad_right = 18, 34, 54, 14
    top = force_max or (max(values) * 1.12 if max(values) else 1)
    inner_w = width - pad_left - pad_right
    inner_h = height - pad_top - pad_bottom

    def x_at(index):
        if len(values) == 1:
            return pad_left
        return pad_left + index * inner_w / (len(values) - 1)

    def y_at(value):
        return pad_top + inner_h * (1 - value / top)

    points = [f"{x_at(i):.1f} {y_at(v):.1f}" for i, v in enumerate(values)]
    line = "M " + " L ".join(points)
    area = line + f" L {x_at(len(values) - 1):.1f} {pad_top + inner_h:.1f} L {x_at(0):.1f} {pad_top + inner_h:.1f} Z"

    grid = []
    for index in range(ticks + 1):
        value = top * index / ticks
        grid.append({"y": round(y_at(value), 1), "label": num(value, 0)})

    step = max(1, len(labels) // 7)
    x_labels = [
        {"x": round(x_at(i), 1), "label": labels[i]}
        for i in range(0, len(labels), step)
    ]

    last_value = values[-1]
    return {
        "empty": False,
        "width": width,
        "height": height,
        "line": line,
        "area": area,
        "grid": grid,
        "x_labels": x_labels,
        "last": {"x": round(x_at(len(values) - 1), 1), "y": round(y_at(last_value), 1),
                 "label": num(last_value, 0) + (" " + value_suffix if value_suffix else "")},
        "baseline": round(pad_top + inner_h, 1),
    }


def donut(segments: list[dict], *, size=170, thickness=20, center_title="", center_sub="") -> dict:
    total = sum(float(s.get("value") or 0) for s in segments) or 1
    radius = (size / 2) - thickness
    circumference = 2 * 3.141592653589793 * radius
    offset = 0.0
    slices = []
    for segment in segments:
        value = float(segment.get("value") or 0)
        length = circumference * value / total
        slices.append({
            "dasharray": f"{length:.2f} {circumference - length:.2f}",
            "offset": f"{-offset:.2f}",
            "color": segment.get("color", "#0e7490"),
        })
        offset += length
    return {
        "size": size,
        "radius": radius,
        "circumference": circumference,
        "slices": slices,
        "center_title": center_title,
        "center_sub": center_sub,
        "legend": [
            {
                "label": segment.get("label", ""),
                "color": segment.get("color", "#0e7490"),
                "pct": round(float(segment.get("value") or 0) * 100 / total),
                "value": segment.get("value", 0),
            }
            for segment in segments
        ],
    }


def hbars(items: list[dict], *, max_value=None) -> list[dict]:
    top = max_value or max([float(i.get("value") or 0) for i in items] or [1]) or 1
    result = []
    for item in items:
        value = float(item.get("value") or 0)
        result.append({
            **item,
            "pct": round(value * 100 / top, 1),
            "value_label": item.get("label_value") or num(value, 0),
        })
    return result


def bars(items: list[dict], *, width=820, height=250) -> dict:
    values = [float(i.get("value") or 0) for i in items]
    top = (max(values) if values else 1) * 1.2 or 1
    pad_top, pad_bottom, pad_left, pad_right = 20, 34, 16, 16
    inner_h = height - pad_top - pad_bottom
    slot = (width - pad_left - pad_right) / max(len(items), 1)
    bar_w = max(slot - 18, 10)
    rects = []
    for index, item in enumerate(items):
        value = float(item.get("value") or 0)
        bar_h = inner_h * value / top
        x = pad_left + index * slot + (slot - bar_w) / 2
        y = pad_top + inner_h - bar_h
        rects.append({
            "x": round(x, 1), "y": round(y, 1), "w": round(bar_w, 1), "h": round(bar_h, 1),
            "label": item.get("label", ""),
            "value_label": item.get("label_value") or num(value, 0),
            "cx": round(x + bar_w / 2, 1),
        })
    return {"width": width, "height": height, "rects": rects,
            "baseline": pad_top + inner_h, "pad_left": pad_left}


def funnel(steps: list[dict]) -> list[dict]:
    first = float(steps[0]["value"]) if steps else 1
    result = []
    for index, step in enumerate(steps):
        value = float(step["value"])
        previous = float(steps[index - 1]["value"]) if index else value
        result.append({
            **step,
            "width_pct": round(58 + (value / first) * 42, 1) if first else 60,
            "rate": round(value / previous * 100) if previous else 100,
            "value_label": fa(step.get("value", "")),
        })
    return result
