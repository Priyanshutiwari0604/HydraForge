# HydraForge

HydraForge is a Python-based re-implementation of core THC-Hydra functionality.
It provides a familiar CLI, modular protocol design, and Hydra-style output — implemented in a single, easy-to-extend Python script.

---

## Legal disclaimer

HydraForge is intended for ethical penetration testing, red teaming, and educational research only.

You must have explicit written permission from the system owner before running any brute-force or authentication testing. Unauthorized access attempts against systems you do not own or have permission to test are illegal and punishable by law.

The author and contributors assume no liability for misuse of this tool.

---

## Features

* Hydra-style CLI and output format
* Modular protocol support (implemented):

  * `ssh` (password authentication)
  * `http-post-form` (HTTP form POST)
  * `ftp` (FTP login)
  * `smtp-auth` (SMTP AUTH)
* Concurrency control (`-t` / `--threads`)
* Optional HTTP form auto-detection (requires BeautifulSoup)
* Save discovered credentials to an output file (CSV)
* Verbose mode for logging failed attempts
* Single-file script for easy distribution and extension

---

## Requirements

* Python 3.8 or newer
* Recommended Python packages:

  * `aiohttp`
  * `paramiko`
  * `beautifulsoup4` (optional, only for `--auto-form`)

Install dependencies with pip:

```bash
pip install aiohttp paramiko beautifulsoup4
```

---

## Installation

1. Clone or download the repository.
2. Place the main script (`hydraforge.py`) in your working directory.
3. Ensure the script is executable:

```bash
chmod +x hydraforge.py
```

4. Install the dependencies listed above.

---

## Usage

Basic syntax:

```bash
python3 hydraforge.py -L <userlist> -P <passlist> -M <module> --target <target> [options]
```

Short flags overview:

* `-L, --userlist` : file with usernames (one per line)
* `-l, --user` : single username
* `-P, --passlist` : file with passwords (one per line) [required]
* `-M, --module` : module to use (`ssh`, `http-post-form`, `ftp`, `smtp-auth`)
* `--target` : target string (e.g. `ssh://10.0.0.5:22`, `http://example.com/login.php`)
* `-t, --threads` : concurrent threads/requests (default: 10)
* `-T, --timeout` : connection timeout in seconds (default: 15)
* `-o, --output` : append valid credentials to output file (CSV)
* `--auto-form` : auto-detect HTTP form fields (requires `beautifulsoup4`)
* `--username-field` / `--password-field` : form field names for `http-post-form`
* `--success-string` / `--failure-string` : custom success/failure indicators for HTTP
* `--tls` : use STARTTLS for SMTP or force TLS when building HTTP URL
* `--disable-ssl` : disable SSL verification for HTTP requests
* `-v, --verbose` : verbose output (prints failed attempts)
* `--yes` : skip interactive confirmation

---

## Examples

SSH brute-force (use only with permission):

```bash
python3 hydraforge.py -L users.txt -P passwords.txt -M ssh --target ssh://10.0.0.5:22 -t 20 -o found.csv
```

HTTP form brute-force (manual field names):

```bash
python3 hydraforge.py -l admin -P passwords.txt -M http-post-form --target http://example.com/login.php --username-field user --password-field pass -t 10
```

HTTP form brute-force with auto-detection:

```bash
python3 hydraforge.py -L users.txt -P passwords.txt -M http-post-form --target http://example.com/login.php --auto-form -t 10
```

FTP brute-force:

```bash
python3 hydraforge.py -L users.txt -P passwords.txt -M ftp --target ftp://ftp.example.com:21 -t 15
```

SMTP AUTH brute-force (with STARTTLS):

```bash
python3 hydraforge.py -L users.txt -P passwords.txt -M smtp-auth --target smtp://mail.example.com:587 --tls -t 10
```

---

## Output

HydraForge prints Hydra-style lines for found credentials and (optionally) failed attempts in verbose mode. Example found line:

```
[22][ssh] host: 10.0.0.5    login: root    password: toor
```

If an output file is provided with `-o`, discovered credentials are appended in CSV format like:

```
module,host,port,username,password,reason
ssh,10.0.0.5,22,root,toor,Authentication successful
```

---

## Limitations and differences compared to THC-Hydra

HydraForge reproduces core Hydra behavior but is not the official THC-Hydra binary. Key differences include:

* Performance: THC-Hydra is written in C and is significantly faster. HydraForge is Python-based and generally slower.
* Modules: THC-Hydra implements many more services. HydraForge includes a limited set by default.
* Advanced features: resume, proxy/SOCKS, and numerous hydra-specific options are not implemented yet.
* Reliability: THC-Hydra has many battle-tested protocol handlers. HydraForge handlers are simplified and may need tuning per target.

---

## Extending and contributing

HydraForge is designed to be easy to extend. Contributions are welcome.

To contribute:

1. Fork the repository.
2. Create a branch for your feature or fix.
3. Implement and test your changes.
4. Submit a pull request with a clear description and test notes.

Guidelines:

* Keep changes focused and well-documented.
* Add tests where appropriate.
* Respect the legal disclaimer in any examples or documentation.

---

## Roadmap ideas

* Implement additional modules (MySQL, PostgreSQL, SMB, RDP, VNC, Telnet)
* Add proxy and SOCKS support
* Add resume functionality and job files
* Implement rules-based password mangling (Hydra-style)
* Improve speed via async libraries or Cython modules

---

## License

This project is provided under the MIT License. See the `LICENSE` file for details.
