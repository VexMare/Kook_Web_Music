import os
import sys
import json
from typing import Dict


COOKIE_DIR = os.path.join(os.path.dirname(__file__), "Cookie")
COOKIE_JSON_PATH = os.path.join(COOKIE_DIR, "cookies.json")
COOKIE_TXT_PATH = os.path.join(COOKIE_DIR, "cookie.txt")


def ensure_dir():
    if not os.path.exists(COOKIE_DIR):
        os.makedirs(COOKIE_DIR, exist_ok=True)


def parse_cookie_str(cookie_str: str) -> Dict[str, str]:
    result: Dict[str, str] = {}
    parts = [p.strip() for p in cookie_str.split(";") if p.strip()]
    for p in parts:
        if "=" in p:
            k, v = p.split("=", 1)
            result[k.strip()] = v.strip()
    return result


def save(cookie_str: str):
    ensure_dir()
    cookies = parse_cookie_str(cookie_str)
    with open(COOKIE_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(cookies, f, ensure_ascii=False, indent=2)
    with open(COOKIE_TXT_PATH, "w", encoding="utf-8") as f:
        f.write(cookie_str.strip())
    print(f"已写入: {COOKIE_JSON_PATH} 和 {COOKIE_TXT_PATH}")


def main():
    if len(sys.argv) > 1:
        cookie_str = " ".join(sys.argv[1:])
    else:
        print("请粘贴完整 Cookie 后回车并按 Ctrl+Z 回车(Windows) 或 Ctrl+D(Linux/Mac) 结束输入:")
        cookie_str = sys.stdin.read()
    if not cookie_str.strip():
        print("未检测到 Cookie 内容")
        sys.exit(1)
    save(cookie_str)


if __name__ == "__main__":
    main()







