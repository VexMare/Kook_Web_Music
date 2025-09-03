import os
import sys
import json
import time
from typing import Dict, Any

import requests


API_BASE = os.environ.get(
    "NETEASE_API_BASE",
    "https://1304404172-f3na0r58ws.ap-beijing.tencentscf.com"
)
COOKIE_DIR = os.path.join(os.path.dirname(__file__), "Cookie")
COOKIE_JSON_PATH = os.path.join(COOKIE_DIR, "cookies.json")
COOKIE_TXT_PATH = os.path.join(COOKIE_DIR, "cookie.txt")


def ensure_cookie_dir():
    if not os.path.exists(COOKIE_DIR):
        os.makedirs(COOKIE_DIR, exist_ok=True)


def save_cookies(cookies: Dict[str, Any]):
    ensure_cookie_dir()
    with open(COOKIE_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(cookies, f, ensure_ascii=False, indent=2)
    cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
    with open(COOKIE_TXT_PATH, "w", encoding="utf-8") as f:
        f.write(cookie_str)
    print(f"已保存 Cookie 到: {COOKIE_JSON_PATH} 和 {COOKIE_TXT_PATH}")


def extract_resp_cookies(resp: requests.Response) -> Dict[str, str]:
    return {k: v for k, v in resp.cookies.items()}


def captcha_send(phone: str, countrycode: str = "86") -> Dict[str, Any]:
    # NeteaseCloudMusicApi 规范参数名为 countrycode
    url = f"{API_BASE}/captcha/sent?phone={phone}&countrycode={countrycode}&timestamp={int(time.time()*1000)}"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.json()


def captcha_verify(phone: str, code: str, countrycode: str = "86") -> Dict[str, Any]:
    url = (
        f"{API_BASE}/captcha/verify?phone={phone}&captcha={code}"
        f"&countrycode={countrycode}&timestamp={int(time.time()*1000)}"
    )
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.json()


def login_cellphone_with_captcha(phone: str, code: str, countrycode: str = "86") -> Dict[str, Any]:
    # 使用 POST 并按官方参数名提交 countrycode，增加 rememberLogin 以便服务下发 Cookie
    ts = int(time.time() * 1000)
    url = f"{API_BASE}/login/cellphone?timestamp={ts}"
    payload = {
        "phone": phone,
        "captcha": code,
        "countrycode": countrycode,
        "rememberLogin": "true",
    }
    with requests.Session() as s:
        resp = s.post(url, data=payload, timeout=20, allow_redirects=True)
        data: Dict[str, Any] = {}
        try:
            data = resp.json()
        except Exception:
            data = {"status": resp.status_code, "text": resp.text[:500]}
        # 登录后从会话中收集 cookie
        cookies = {k: v for k, v in s.cookies.items()}
        # 兜底从本次响应收集 cookie
        if not cookies:
            cookies = extract_resp_cookies(resp)

        # 再尝试 /login/status，部分实现会在此下发 Set-Cookie
        try:
            st = s.get(f"{API_BASE}/login/status", timeout=10)
            st.raise_for_status()
            if s.cookies:
                cookies.update({k: v for k, v in s.cookies.items()})
        except Exception:
            pass

        # 将可能的错误信息带回，便于上层打印
        return {"data": data, "cookies": cookies, "http_status": resp.status_code}


def main():
    print(f"使用 API: {API_BASE}")
    phone = input("请输入手机号: ").strip()
    if not phone:
        print("手机号不能为空")
        sys.exit(1)
    ct = input("国家区号(默认86): ").strip() or "86"

    try:
        sent = captcha_send(phone, ct)
        code = sent.get("code")
        if code not in (200,):
            print(f"发送验证码失败: {sent}")
            sys.exit(2)
        print("验证码已发送，请查收短信...")
    except Exception as e:
        print(f"发送验证码异常: {e}")
        sys.exit(2)

    sms = input("请输入短信验证码: ").strip()
    if not sms:
        print("验证码不能为空")
        sys.exit(3)

    try:
        verify = captcha_verify(phone, sms, ct)
        vcode = verify.get("code")
        if vcode not in (200,):
            print(f"验证码校验失败: {verify}")
            # 仍尝试直接登录，以应对部分实现不返回 200
        else:
            print("验证码校验成功，正在登录...")
    except Exception as e:
        print(f"验证码校验异常: {e}，尝试继续登录...")

    try:
        result = login_cellphone_with_captcha(phone, sms, ct)
        data = result.get("data", {})
        cookies = result.get("cookies", {})
        status = result.get("http_status")
        if status and status >= 400:
            print(f"登录HTTP状态: {status}")
        if not cookies:
            print(f"登录返回但未获取到 Cookie，请检查服务端: {data}")
            sys.exit(4)
        save_cookies(cookies)
        code = data.get("code")
        if code in (200, 803):
            print("登录成功！")
        else:
            print(f"登录完成，返回码: {code}，详情: {json.dumps(data, ensure_ascii=False)[:800]}")
    except Exception as e:
        print(f"登录异常: {e}")
        sys.exit(5)


if __name__ == "__main__":
    main()


