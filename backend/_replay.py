import asyncio, json, pathlib, struct, sys, cv2, websockets
CLIPS=pathlib.Path("../experiments/day1/clips"); Q=[cv2.IMWRITE_JPEG_QUALITY,70]
URL="ws://localhost:8000/ws/recognize"; CAP=25.0
def enc(i): return cv2.imencode(".jpg", cv2.resize(i,(640,480)), Q)[1].tobytes()
def stamp(ms,j): return struct.pack("<I", int(ms)) + j
async def one(clip):
    cap=cv2.VideoCapture(str(clip)); src=cap.get(cv2.CAP_PROP_FPS) or 25.0
    raw=[]
    while True:
        ok,f=cap.read()
        if not ok: break
        raw.append(f)
    cap.release()
    if not raw: return None
    step=src/CAP; idx=[int(i*step) for i in range(int(len(raw)/step))]
    frames=[enc(raw[i]) for i in idx if i<len(raw)]; still=enc(raw[0])
    dt=1000.0/CAP; ms=0.0
    async with websockets.connect(URL,max_size=None) as ws:
        await ws.recv()
        async def push(b):
            nonlocal ms
            await ws.send(stamp(ms,b)); ms+=dt; await asyncio.sleep(1.0/CAP)
        for _ in range(8): await push(still)
        for b in frames:  await push(b)
        for _ in range(14): await push(still)
        try:
            while True:
                ev=json.loads(await asyncio.wait_for(ws.recv(),timeout=8))
                if ev["type"] in ("recognized","unknown_ambiguous","unknown_no_match","aborted","discarded"):
                    return ev
        except asyncio.TimeoutError: return None
async def main():
    rows=[]
    for clip in sorted(CLIPS.glob("*.mp4")):
        exp=clip.stem.rsplit("_ref_",1)[0]; ev=await one(clip)
        if ev is None: print(f"    [NONE ] {clip.stem:22}"); continue
        got=ev.get("best_sign_code"); d1=ev.get("d1"); d2=ev.get("d2_diff_label")
        ok = got==exp
        mg=f"{((d2-d1)/d1*100):+.0f}%" if (d1 and d2) else "-"
        rows.append((exp,got,d1,ok))
        print(f"    [{'OK  ' if ok else 'MISS'}] {clip.stem:22} nearest={str(got):14} d1={d1} margin={mg}")
    good=[r[2] for r in rows if r[3] and r[2]]
    bad=[r[2] for r in rows if not r[3] and r[2]]
    print(f"\n  nearest-reference correct: {sum(1 for r in rows if r[3])}/{len(rows)}")
    if good: print(f"  correct-match d1 range: {min(good):.3f} - {max(good):.3f}")
    if bad: print(f"  wrong-match d1 range:   {min(bad):.3f} - {max(bad):.3f}")
asyncio.run(main())
