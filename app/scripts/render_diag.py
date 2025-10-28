# app/scripts/render_diag.py
import os, json
import certifi
from pymongo import MongoClient
from dns import resolver

URI = os.getenv("MONGO_URI", "")
print("[diag] MONGO_URI repr:", repr(URI))
print("[diag] certifi CA:", certifi.where())

# 1) SRV/DNS 확인
try:
    host = URI.split("@")[1].split("/")[0]  # cluster0.xxx.mongodb.net
    print("[diag] host:", host)
    for t in ["_mongodb._tcp."+host, host]:
        try:
            ans = resolver.resolve(t, "SRV" if t.startswith("_mongodb") else "CNAME")
            print(f"[diag] DNS {t} ->", [str(a) for a in ans])
        except Exception as e:
            print(f"[diag] DNS {t} error:", e)
except Exception as e:
    print("[diag] host parse error:", e)

# 2) Atlas 핑 테스트
try:
    cli = MongoClient(URI, tls=True, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=6000)
    info = cli.server_info()
    print("[diag] server_info ok:", json.dumps(info, indent=2)[:600], "...")
except Exception as e:
    print("[diag] server_info error:", e)
