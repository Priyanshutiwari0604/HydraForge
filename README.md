# HYDRA-FORAGE 2.5

**Advanced Multi-Protocol Network Login Cracker**


<img width="613" height="296" alt="image" src="https://github.com/user-attachments/assets/9d04b14a-2780-4ffd-9f49-a1b004c8dea7" />



A modern, Hydra-compatible Python implementation for ethical security testing and automation.

# Overview

HYDRA-FORAGE is a modular, multi-protocol brute-force framework implemented in Python.
It aims to provide a Hydra-like CLI and output style, while being easy to read, extend, and run on systems with Python 3. It supports common protocols used in penetration testing workflows and provides a multi-threaded engine, real-time progress display, and result logging.

# Supported protocols

* ssh (requires `paramiko`)
* ftp (uses Python's `ftplib`)
* http-basic / https-basic (requires `requests`)
* http form-based (requires `requests`)
* telnet (uses Python's `telnetlib`)
* mysql (requires `pymysql`)
* postgres (requires `psycopg2` / `psycopg2-binary`)

# Features

* Hydra-style CLI and attack behavior
* Multi-threaded worker pool for concurrent attempts
* Real-time progress display (compact bar or verbose)
* Automatic result saving to file
* Modular handlers per protocol for easy extension
* Dependency checks with clear install hints
* Clean, color-coded terminal UI (can be run in quiet mode)

# Requirements

* Python 3.8 or newer
* Optional Python packages (install only what you need for a given protocol):

  * `paramiko` (SSH)
  * `requests` (HTTP/HTTPS)
  * `pymysql` (MySQL)
  * `psycopg2-binary` (PostgreSQL)

Install optional packages as needed:

```bash
pip install paramiko requests pymysql psycopg2-binary
```

# Quickstart

1. Place `hydraforage.py` in your working directory and make it executable:

```bash
chmod +x hydraforage.py
```

2. Basic usage examples:

```bash
# Single username, password file, SSH
./hydraforage.py -l root -P passwords.txt ssh://192.168.1.100

# User file, single password, custom SSH port
./hydraforage.py -L users.txt -p 'Password123' -s 2222 ssh://target.com

# FTP with threads and output file
./hydraforage.py -l admin -P rockyou.txt -t 32 -o results.txt ftp://10.0.0.1
```

# Command-line options

Run `./hydraforage.py -h` to show the full help. Key options are summarized below:

* `target` — positional: `service://host[:port]` (e.g. `ssh://10.0.0.1:2222`)
* `-l, --login` — single username
* `-L, --login-file` — file with usernames (one per line)
* `-p, --pass` — single password
* `-P, --pass-file` — file with passwords
* `-x, --generate` — password generator placeholder (not implemented in v2.5)
* `-s, --port` — override default port
* `-m, --path` — HTTP path (default `/`)
* `-t, --tasks` — number of parallel tasks/threads (default: 16)
* `-w, --timeout` — timeout in seconds per attempt (default: 10)
* `-W, --wait` — wait time between attempts in milliseconds (default: 0)
* `-o, --output` — output file to save valid credentials (default: `hydra_forage.txt`)
* `-v, --verbose` — verbose mode
* `-q, --quiet` — quiet mode (less output)
* `-f, --exit-on-first` — exit after first valid login found
* `--list-services` — list all available services and their dependency status

# Example session

```bash
./hydraforage.py -l admin -P passwords.txt -t 24 ssh://192.168.0.50
```

Typical output behavior:

* Banner and attack configuration box (unless `--quiet`)
* Connection test to the target
* Progress bar or verbose stats while running
* Successful credentials printed and saved to the output file
* Final attack summary with total attempts, successes, rate and elapsed time

# Files

* `hydraforage.py` — main script (this repository)
* `hydra_forage.txt` — default output file where successful logins are appended (created on first success)

# Extending / Development

`hydraforage.py` is designed to be modular:

* Add new protocol handlers as functions similar to `ssh_login`, `ftp_login`, `http_form_login`, etc.
* Add entries to the `SERVICES` dictionary mapping a service name to its handler and default port.
* The `BruteForceEngine` handles queueing, threading, and stats collection—modify or replace it to change concurrency strategy (for example, use `concurrent.futures` or async approaches).

# Security and legal notice

This tool can be used to test authentication across network services. Use it only against systems you own or explicitely have permission to test. Unauthorized access, scanning, or brute forcing is illegal and unethical. The author/project is not responsible for misuse.

# Contribution

Contributions, bug reports, and pull requests are welcome. When submitting changes:

* Keep protocol handlers isolated and well-documented.
* Add new dependencies to the README with clear install instructions.
* Include usage examples and tests where applicable.

# Contact

For questions or contributions, open an issue or submit a pull request on this repository.



