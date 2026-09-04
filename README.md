# Async Network Monitor

A small asynchronous network reachability monitoring project written in Python.

The application stores network nodes in SQLite, checks their reachability concurrently using `asyncio`, updates node status through SQLAlchemy, and prints the monitoring results.

This project was created as a practical exercise for entry-level NOC, System Administration, and DevOps roles.

## Features

- Real host reachability checks using the system `ping` command
- Concurrent monitoring with `asyncio`
- SQLAlchemy ORM
- Async SQLite access with `aiosqlite`
- Persistent node statuses
- Cross-platform ping support for Windows and Linux
- Custom host list from the command line
- Basic latency measurement
- Simple CLI output

## Technologies

- Python
- asyncio
- SQLAlchemy
- SQLite
- aiosqlite
- ICMP / ping

## Project Structure

```text
async-network-monitor/
├── main.py
├── README.md
├── requirements.txt
├── .gitignore
└── screenshots/
    └── example-output.png
```

`network.db` is created automatically at runtime and is intentionally excluded from Git.

## Installation

Clone the repository:

```bash
git clone <repository-url>
cd async-network-monitor
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\activate
```

Or on Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run with the default home-lab hosts:

```bash
python main.py
```

Default hosts:

```text
127.0.0.1
192.168.56.101
192.168.56.102
```

Monitor custom hosts:

```bash
python main.py 192.168.1.1 8.8.8.8 example.com
```

Change the ping timeout:

```bash
python main.py --timeout 2 192.168.56.101 192.168.56.102
```

## How It Works

```text
               +----------------+
               |   Node list    |
               |     SQLite     |
               +-------+--------+
                       |
                       v
               SQLAlchemy ORM
                       |
                       v
            asyncio monitoring tasks
              /        |        \
             v         v         v
          Host 1     Host 2     Host 3
             |         |         |
            ping      ping      ping
             |         |         |
             +---------+---------+
                       |
                       v
                active/offline
                       |
                       v
                  SQLite DB
```

The program:

1. creates the SQLite database and `nodes` table;
2. adds the hosts to be monitored;
3. creates asynchronous reachability checks;
4. runs the checks concurrently;
5. measures approximate check latency;
6. marks each node as `active` or `offline`;
7. stores the updated status in SQLite.

## Example Output

```text
[System] Added 3 node(s) with status 'unknown'.

--- Node list BEFORE monitoring ---
ID: 1   | IP/Host: 127.0.0.1            | Status: unknown
ID: 2   | IP/Host: 192.168.56.101       | Status: unknown
ID: 3   | IP/Host: 192.168.56.102       | Status: unknown

[Monitoring] Starting asynchronous reachability checks...
[ACTIVE ] 127.0.0.1            | 8.4 ms
[ACTIVE ] 192.168.56.101       | 15.7 ms
[ACTIVE ] 192.168.56.102       | 17.1 ms
[Monitoring] Statuses saved to the database.

--- Node list AFTER monitoring ---
ID: 1   | IP/Host: 127.0.0.1            | Status: active
ID: 2   | IP/Host: 192.168.56.101       | Status: active
ID: 3   | IP/Host: 192.168.56.102       | Status: active
```

Actual latency values depend on the system and network.

## Screenshot

Add a terminal screenshot after running the project:

```text
screenshots/example-output.png
```

Then it can be displayed here:

[Monitoring output](screenshots/example-output.png)

## What This Project Demonstrates

- basic network troubleshooting concepts;
- asynchronous Python programming;
- concurrent network checks;
- working with relational databases;
- SQLAlchemy ORM;
- Linux/Windows networking tools;
- monitoring workflow: check → status → store → report.

## Limitations

- Reachability is checked with ICMP only.
- Some hosts or firewalls may block ping even when their services are available.
- The measured time includes process startup overhead and is not a precise ICMP RTT measurement.
- Monitoring history is not stored yet; only the current node status is saved.

## Future Improvements

- TCP port availability checks
- Per-node service/port configuration
- Monitoring history table
- Accurate response-time parsing
- Periodic monitoring loop
- Structured logging
- Export metrics
- Docker support
- Zabbix integration
- Web dashboard
