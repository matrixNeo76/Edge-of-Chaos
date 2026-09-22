# Security Policy

## Scope

This repository contains research/metrology software, including drivers for lab
instrumentation (Keithley DMM, PicoScope via PyVISA/SCPI, `hardware_driver_v2.py`).
By default the driver runs in **mock mode** — no network
services are exposed, and no credentials or secrets are stored or required anywhere
in this codebase.

If you use the non-mock (`mock=False`) hardware paths against real lab equipment on a
GPIB/USB-connected instrument, treat that as you would any lab-network software:
standard PyVISA/SCPI usage, no additional attack surface introduced by this project
beyond what PyVISA itself exposes.

## Reporting a Vulnerability

If you find a security issue (e.g., unsafe deserialization, path traversal in the
packaging scripts, or anything that could execute untrusted code), please **do not**
open a public issue. Instead, use GitHub's private vulnerability reporting
(*Security* tab → *Report a vulnerability*) on this repository, or contact the
maintainer directly through their GitHub profile.

Please include:
- A description of the issue and its potential impact
- Steps to reproduce
- The affected file(s)/commit

We'll acknowledge reports within a reasonable timeframe; this is an independent
research project, not a funded/staffed security team, so response times may vary.

## Supported Versions

This project does not yet have tagged releases with a formal support policy. Security
fixes, when applicable, are made against the `main` branch.
