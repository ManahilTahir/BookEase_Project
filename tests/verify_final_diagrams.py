import asyncio
import json
import os
import subprocess
import time
import urllib.request
import websockets

async def verify_html():
    html_path = os.path.abspath("BookEase_Database_and_DataFlow_Diagrams.html")
    url = f"file:///{html_path.replace(os.sep, '/')}"

    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    cmd = [
        chrome_path,
        "--headless=new",
        "--remote-debugging-port=9222",
        "--disable-gpu",
        "--no-sandbox",
        url
    ]
    proc = subprocess.Popen(cmd)
    time.sleep(2)

    try:
        resp = urllib.request.urlopen("http://127.0.0.1:9222/json")
        tabs = json.loads(resp.read().decode())
        target_tab = None
        for t in tabs:
            if "BookEase" in t.get("url", ""):
                target_tab = t
                break
        if not target_tab:
            target_tab = tabs[0]
        ws_url = target_tab["webSocketDebuggerUrl"]

        async with websockets.connect(ws_url) as ws:
            await ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
            # Wait for DOM and all diagrams to render
            await asyncio.sleep(4)

            # 1. Check all diagram SVGs on initial load
            check_script = """
            (() => {
                const results = [];
                const ids = ['erd', 'dfd0', 'dfd1', 'dfd2a', 'dfd2b', 'dfd2c', 'dfd2d'];
                ids.forEach(id => {
                    const render = document.getElementById('render-' + id);
                    const svg = render ? render.querySelector('svg') : null;
                    const err = render ? render.querySelector('.diagram-error, .error-text') : null;
                    const ind = document.querySelector('#viewport-' + id + ' .zoom-indicator');
                    results.push({
                        id: id,
                        hasSvg: !!svg,
                        svgId: svg ? svg.id : null,
                        viewBox: svg ? svg.getAttribute('viewBox') : null,
                        styleWidth: svg ? svg.style.width : null,
                        styleHeight: svg ? svg.style.height : null,
                        hasError: !!err,
                        zoomIndicator: ind ? ind.textContent : null,
                        scale: state[id] ? state[id].scale : null,
                        naturalWidth: state[id] ? state[id].naturalWidth : null,
                        naturalHeight: state[id] ? state[id].naturalHeight : null,
                    });
                });
                return results;
            })()
            """
            msg_id = 100
            await ws.send(json.dumps({
                "id": msg_id,
                "method": "Runtime.evaluate",
                "params": {"expression": check_script, "returnByValue": True}
            }))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get("id") == msg_id:
                    print("=== 1. DIAGRAM STATUS ON PAGE LOAD ===")
                    print(json.dumps(data.get("result", {}).get("result", {}).get("value", []), indent=2))
                    break

            # 2. Test tab navigation: click each tab and check visibility & fitting
            tab_test = """
            (() => {
                const results = [];
                const tabs = ['erd', 'dfd0', 'dfd1', 'dfd2'];
                tabs.forEach(t => {
                    const btn = document.querySelector(`.tab-btn[data-tab="${t}"]`);
                    if (btn) btn.click();
                    const section = document.getElementById('tab-' + t);
                    results.push({
                        tab: t,
                        isActive: section ? section.classList.contains('active') : false,
                        isVisible: section ? window.getComputedStyle(section).visibility : null
                    });
                });
                return results;
            })()
            """
            msg_id = 200
            await ws.send(json.dumps({
                "id": msg_id,
                "method": "Runtime.evaluate",
                "params": {"expression": tab_test, "returnByValue": True}
            }))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get("id") == msg_id:
                    print("\n=== 2. TAB SWITCHING TEST ===")
                    print(json.dumps(data.get("result", {}).get("result", {}).get("value", []), indent=2))
                    break

            # 3. Test Zoom Controls on dfd0
            zoom_test = """
            (() => {
                const initialScale = state['dfd0'].scale;
                zoom('dfd0', 1.2);
                const afterZoomIn = state['dfd0'].scale;
                zoom('dfd0', 0.8);
                const afterZoomOut = state['dfd0'].scale;
                resetDiagram('dfd0');
                const afterReset = state['dfd0'].scale;
                fitDiagram('dfd0');
                const afterFit = state['dfd0'].scale;
                return {
                    initialScale,
                    afterZoomIn,
                    afterZoomOut,
                    afterReset,
                    afterFit
                };
            })()
            """
            msg_id = 300
            await ws.send(json.dumps({
                "id": msg_id,
                "method": "Runtime.evaluate",
                "params": {"expression": zoom_test, "returnByValue": True}
            }))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get("id") == msg_id:
                    print("\n=== 3. ZOOM CONTROLS TEST (dfd0) ===")
                    print(json.dumps(data.get("result", {}).get("result", {}).get("value", []), indent=2))
                    break

            # 4. Check for any errors anywhere in the page DOM
            error_check = """
            (() => {
                const errors = [];
                document.querySelectorAll('.diagram-error, .error-text').forEach(el => {
                    errors.push(el.textContent.substring(0, 100));
                });
                return errors;
            })()
            """
            msg_id = 400
            await ws.send(json.dumps({
                "id": msg_id,
                "method": "Runtime.evaluate",
                "params": {"expression": error_check, "returnByValue": True}
            }))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get("id") == msg_id:
                    print("\n=== 4. DOM ERROR CHECK ===")
                    print("Errors found:", data.get("result", {}).get("result", {}).get("value", []))
                    break

    finally:
        proc.terminate()

if __name__ == "__main__":
    asyncio.run(verify_html())

