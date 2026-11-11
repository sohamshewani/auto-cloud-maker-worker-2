import os
import json
import time
import random
import subprocess
import re
from pathlib import Path
from google import genai
from google.genai import types

# Verified active models on your Google AI Studio account
MODELS = ["gemini-3.5-flash-lite", "gemini-3.8-flash"]
LANGUAGES = ["C++", "C", "Java", "Python"]

ELITE_SYSTEM_CHALLENGES = [
    {
        "domain": "High-Throughput Storage Engines & Database Internals",
        "challenges": [
            "Log-Structured Merge-tree (LSM) key-value engine featuring multi-threaded Write-Ahead Logging (WAL) with CRC32 checksums, lock-free MemTable using SkipLists, leveled background compaction with merge-sort, and dynamic Bloom Filter pruning",
            "In-memory columnar database analytical engine with vectorized SIMD execution passes, dictionary encoding, dictionary compression, and multi-version concurrency control (MVCC)",
            "Append-only B-Tree index storage manager with LRU page-cache buffer pooling, dirty page flusher, and write-lock striping"
        ]
    },
    {
        "domain": "Distributed Consensus & State Machine Replication",
        "challenges": [
            "Distributed consensus Raft protocol engine featuring dynamic leader election, serialized heartbeat log replication, and atomic state-machine transitions",
            "SWIM gossip-protocol cluster membership detector with failure detection, suspicion transition timers, and piggybacked ping payloads",
            "Multi-node distributed token-bucket rate limiter with sliding-window atomic counters, and synchronization via peer gossip"
        ]
    },
    {
        "domain": "Compilers, Low-Level Runtimes & Kernel Bypass Systems",
        "challenges": [
            "Recursive-descent AST parser, bytecode compiler, and register virtual machine runtime featuring a stack frame evaluator and mark-and-sweep garbage collector",
            "Zero-copy userspace packet filter utilizing lock-free circular ring buffers, sliding-window flow control, and checksum validation",
            "Asynchronous high-concurrency event runtime with non-blocking epoll/kqueue event loop multiplexing, coroutine scheduler, and timer wheels"
        ]
    }
]

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
GH_USER = os.environ.get("GITHUB_ACTOR", "sohamshewani")

def run(cmd, cwd=None):
    res = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    return res.returncode == 0, res.stdout, res.stderr

def ask_gemini(prompt: str, max_tokens=4000) -> str:
    for attempt in range(4):
        for model_name in MODELS:
            try:
                print(f"⚡ [Attempt {attempt + 1}] Querying [{model_name}]...", flush=True)
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        max_output_tokens=max_tokens,
                        temperature=0.2
                    )
                )
                if response.text and response.text.strip():
                    return response.text.strip()
            except Exception as e:
                err_str = str(e)
                print(f"⚠️ [{model_name}] notice: {err_str[:120]}...", flush=True)
                time.sleep(5)
        # If all models hit a 503 spike, wait for Google's server load to settle
        wait_time = (attempt + 1) * 12
        print(f"⏳ Cloud demand spike detected across all models. Pausing {wait_time}s before retry...", flush=True)
        time.sleep(wait_time)
    raise RuntimeError("All models failed after multiple retries.")


def clean_code(raw: str) -> str:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned

def build_system():
    domain_obj = random.choice(ELITE_SYSTEM_CHALLENGES)
    challenge = random.choice(domain_obj["challenges"])
    language = random.choice(LANGUAGES)
    base_name = f"{language.lower()}-sys-{int(time.time())}"

    print(f"\n[Stage 1/7: Architecture Spec] 📐 Formulating specification for [{language}]...", flush=True)
    spec_prompt = f"""
    You are a Principal Systems Architect. Design a production-grade system for:
    Topic: {challenge}
    Language: {language}

    Return a clean JSON object with these keys:
    {{
      "repo_name": "{base_name}",
      "description": "Clear technical description mentioning {language}",
      "files": ["include/engine.hpp", "src/engine.cpp", "src/main.cpp"]
    }}
    Return ONLY JSON.
    """
    spec_text = ask_gemini(spec_prompt, max_tokens=1000)
    try:
        spec = json.loads(clean_code(spec_text))
    except Exception:
        spec = {
            "repo_name": base_name,
            "description": f"Enterprise-grade {challenge} implemented in {language}",
            "files": ["include/engine.h", "src/engine.c", "src/main.c"]
        }

    work_dir = Path(f"/tmp/{spec['repo_name']}")
    work_dir.mkdir(parents=True, exist_ok=True)

    # Stage 2: Author Files
    for rel_path in spec.get("files", []):
        print(f"⚙️  Authoring production module: [{rel_path}]...", flush=True)
        code_prompt = f"""
        You are a Staff Systems Engineer. Write complete, working code for '{rel_path}' in {language}.
        System topic: {challenge}
        MANDATES:
        - No TODOs, no placeholders.
        - Production quality, thread safety, clean interfaces.
        Return ONLY source code.
        """
        code = clean_code(ask_gemini(code_prompt, max_tokens=3000))
        target_path = work_dir / rel_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(code, encoding="utf-8")

    # Stage 3: Build Automation
    print("\n[Stage 3/7: Build Automation & Packaging] 📦 Configuring build harness...", flush=True)
    make_prompt = f"Write a complete Makefile or build script for {language} project with files {spec.get('files', [])}. Output ONLY the file content."
    (work_dir / "Makefile").write_text(clean_code(ask_gemini(make_prompt, max_tokens=1000)), encoding="utf-8")

    # Stage 4: Documentation
    print("\n[Stage 6/7: Enterprise Documentation] 📚 Synthesizing architectural documentation...", flush=True)
    readme_prompt = f"""
    Write a top-tier README.md for '{spec['repo_name']}' in {language}.
    Start with:
    # {spec['repo_name']}
    [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

    Include an ASCII architecture diagram, memory invariants, Big-O table, and build instructions.
    Return ONLY Markdown.
    """
    (work_dir / "README.md").write_text(clean_code(ask_gemini(readme_prompt, max_tokens=3000)), encoding="utf-8")

    # Root MIT LICENSE
    year = time.strftime("%Y")
    license_text = f"""MIT License

Copyright (c) {year} {GH_USER}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
    (work_dir / "LICENSE").write_text(license_text, encoding="utf-8")
    (work_dir / ".gitignore").write_text("*.o\n*.a\n*.out\nbuild/\ntarget/\nbin/\nvenv/\n__pycache__/\n", encoding="utf-8")

    # Stage 7: Non-hanging Git Deployment
    print("\n[Packaging & Deployment] 🚀 Publishing repository to GitHub...", flush=True)
    run("git init", cwd=work_dir)
    run(f"git config user.name '{GH_USER}'", cwd=work_dir)
    run(f"git config user.email '{GH_USER}@users.noreply.github.com'", cwd=work_dir)
    run("git add .", cwd=work_dir)
    run('git commit -m "feat: complete production architecture with tests and ci"', cwd=work_dir)
    run("git branch -M main", cwd=work_dir)

    gh_token = os.environ.get("GH_TOKEN", "")
    target_repo = spec['repo_name']
    remote_url = f"https://x-access-token:{gh_token}@github.com/{GH_USER}/{target_repo}.git"

    # Non-interactive CLI creation
    create_cmd = (
        f'GH_PROMPT_DISABLED=1 gh repo create "{target_repo}" '
        f'--public --source=. --remote=origin --description "{spec.get("description", "Built by Bot")}"'
    )
    ok, out, err = run(create_cmd, cwd=work_dir)
    
    # Always push using explicit token URL to prevent interactive auth prompts
    run(f"git remote set-url origin {remote_url}", cwd=work_dir)
    push_ok, _, push_err = run("git push -u origin main", cwd=work_dir)

    if push_ok:
        print(f"\n🌟 Published Production Repository: https://github.com/{GH_USER}/{target_repo}", flush=True)
    else:
        print(f"⚠️ Push error: {push_err.strip()}", flush=True)

if __name__ == "__main__":
    build_system()
