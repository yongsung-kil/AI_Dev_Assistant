"""파라미터 최적화기 (표준 라이브러리만).

사용: python optimizer.py config.json [--budget N] [--workers K]
config.json의 params(공간), evaluate(명령과 지표 정규식), search(예산, 병렬 수, seed, 국소 비율)를 읽어
무작위 표본과 최량점 주변 국소 변이를 섞어 평가한다. 결과는 log.jsonl(누적)과 best.json.
"""
import io
import json
import locale
import os
import random
import re
import signal
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def load_config(path):
    with io.open(path, encoding="utf-8") as f:
        return json.load(f)


def validate(config):
    """설정 오류 문장 목록. 비어 있으면 정상."""
    errors = []
    params = config.get("params") or []
    if not params:
        errors.append("params: 파라미터가 하나도 없음")
    for p in params:
        name = p.get("name") or "(이름 없음)"
        kind = p.get("type")
        if not p.get("name"):
            errors.append("params: name 없음")
        if kind == "float":
            if any(k not in p for k in ("min", "max", "step")) or not p.get("step"):
                errors.append(f"params[{name}]: float은 min, max, step(0보다 큼)이 필요")
        elif kind == "int":
            if any(k not in p for k in ("min", "max")):
                errors.append(f"params[{name}]: int는 min, max가 필요")
        elif kind == "choice":
            if not p.get("values"):
                errors.append(f"params[{name}]: choice는 values가 필요")
        else:
            errors.append(f"params[{name}]: type은 float, int, choice 중 하나")
    ev = config.get("evaluate") or {}
    if not ev.get("command"):
        errors.append("evaluate.command 없음")
    if not ev.get("metric_regex"):
        errors.append("evaluate.metric_regex 없음")
    else:
        try:
            if re.compile(ev["metric_regex"]).groups < 1:
                errors.append("evaluate.metric_regex: 값을 잡는 괄호가 필요")
        except re.error as e:
            errors.append(f"evaluate.metric_regex: {e}")
    return errors


def _decimals(step):
    text = repr(float(step))
    return len(text.split(".")[1]) if "." in text and "e" not in text else 6


def _grid(p, value):
    lo, hi, step = float(p["min"]), float(p["max"]), float(p["step"])
    value = min(max(value, lo), hi)
    return round(lo + round((value - lo) / step) * step, _decimals(step))


def sample(params, rng):
    point = {}
    for p in params:
        if p["type"] == "float":
            point[p["name"]] = _grid(p, rng.uniform(float(p["min"]), float(p["max"])))
        elif p["type"] == "int":
            point[p["name"]] = rng.randint(int(p["min"]), int(p["max"]))
        else:
            point[p["name"]] = rng.choice(p["values"])
    return point


def mutate(point, params, rng):
    """최량점에서 파라미터 하나를 조금 바꾼 후보."""
    new = dict(point)
    p = rng.choice(params)
    name = p["name"]
    if p["type"] == "float":
        new[name] = _grid(p, point[name] + float(p["step"]) * rng.choice([-3, -2, -1, 1, 2, 3]))
    elif p["type"] == "int":
        new[name] = min(max(point[name] + rng.choice([-2, -1, 1, 2]), int(p["min"])), int(p["max"]))
    else:
        others = [v for v in p["values"] if v != point[name]]
        new[name] = rng.choice(others) if others else point[name]
    return new


def _decode(data):
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode(locale.getpreferredencoding(False), errors="replace")


def _kill_tree(proc):
    """시간 초과 때 셸과 그 아래 프로세스를 함께 끝낸다 (Windows는 taskkill, 그 밖은 프로세스 그룹)."""
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
    else:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except Exception:
            proc.kill()


def evaluate(config, point):
    """명령을 돌려 지표를 읽는다. 실패(종료 코드, 시간 초과, 지표 없음)는 None."""
    ev = config["evaluate"]
    command = ev["command"].format(**point)
    kwargs = {"shell": True, "stdout": subprocess.PIPE, "stderr": subprocess.PIPE}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    try:
        proc = subprocess.Popen(command, **kwargs)
    except OSError:
        return None
    try:
        stdout, stderr = proc.communicate(timeout=ev.get("timeout_seconds", 600))
    except subprocess.TimeoutExpired:
        _kill_tree(proc)
        try:
            proc.communicate(timeout=5)
        except Exception:
            pass
        return None
    if proc.returncode != 0:
        return None
    m = re.search(ev["metric_regex"], _decode(stdout) + "\n" + _decode(stderr))
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


def point_key(point):
    return json.dumps(point, sort_keys=True, ensure_ascii=False)


def run(config_path, budget=None, workers=None):
    config = load_config(config_path)
    errors = validate(config)
    if errors:
        raise ValueError("\n".join(errors))
    base = os.path.dirname(os.path.abspath(config_path))
    log_path, best_path = os.path.join(base, "log.jsonl"), os.path.join(base, "best.json")
    search = config.get("search", {})
    budget = budget or search.get("budget", 20)
    workers = max(1, workers or search.get("workers", 1))
    local_ratio = search.get("local_ratio", 0.5)
    minimize = config["evaluate"].get("minimize", True)
    params = config["params"]
    rng = random.Random(search.get("seed", 0))

    entries = []
    if os.path.isfile(log_path):
        with io.open(log_path, encoding="utf-8") as f:
            entries = [json.loads(line) for line in f if line.strip()]
    seen = {point_key(e["point"]) for e in entries}
    resumed = len(entries)

    def better(a, b):
        return a < b if minimize else a > b

    best = None
    for e in entries:
        if e["value"] is not None and (best is None or better(e["value"], best["value"])):
            best = e

    def propose():
        for _ in range(100):
            if best is None or rng.random() >= local_ratio:
                candidate = sample(params, rng)
            else:
                candidate = mutate(best["point"], params, rng)
            key = point_key(candidate)
            if key not in seen:
                seen.add(key)
                return candidate
        return None

    evaluated = len(entries)
    failed = sum(1 for e in entries if e["value"] is None)
    with io.open(log_path, "a", encoding="utf-8", newline="\n") as logf:
        while evaluated < budget:
            batch = []
            for _ in range(min(workers, budget - evaluated)):
                candidate = propose()
                if candidate is None:
                    break
                batch.append(candidate)
            if not batch:
                break
            with ThreadPoolExecutor(max_workers=len(batch)) as pool:
                values = list(pool.map(lambda pt: evaluate(config, pt), batch))
            for pt, val in zip(batch, values):
                entry = {"point": pt, "value": val}
                logf.write(json.dumps(entry, ensure_ascii=False) + "\n")
                logf.flush()
                evaluated += 1
                if val is None:
                    failed += 1
                elif best is None or better(val, best["value"]):
                    best = entry
    if best is not None:
        with io.open(best_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(best, f, ensure_ascii=False, indent=1)
    return {"best": best, "evaluated": evaluated, "failed": failed, "resumed": resumed}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print("사용법: optimizer.py config.json [--budget N] [--workers K]")
        return 2
    budget = int(argv[argv.index("--budget") + 1]) if "--budget" in argv else None
    workers = int(argv[argv.index("--workers") + 1]) if "--workers" in argv else None
    result = run(argv[0], budget=budget, workers=workers)
    base = os.path.dirname(os.path.abspath(argv[0]))
    with io.open(os.path.join(base, "log.jsonl"), encoding="utf-8") as f:
        entries = [json.loads(line) for line in f if line.strip()]
    minimize = load_config(argv[0])["evaluate"].get("minimize", True)
    ranked = sorted((e for e in entries if e["value"] is not None), key=lambda e: e["value"], reverse=not minimize)
    print(f"평가 {result['evaluated']}점 (실패 {result['failed']}, 이어서 {result['resumed']})")
    print("| 순위 | 값 | 점 |\n|---|---|---|")
    for i, e in enumerate(ranked[:10], 1):
        print(f"| {i} | {e['value']} | {point_key(e['point'])} |")
    return 0 if result["best"] else 1


if __name__ == "__main__":
    sys.exit(main())
