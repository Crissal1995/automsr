# AutoMSR

[![PyPI - Version](https://img.shields.io/pypi/v/automsr)](https://pypi.org/project/automsr/#history)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/automsr)](https://pypi.org/project/automsr)
[![Checks](https://github.com/Crissal1995/automsr/actions/workflows/checks.yaml/badge.svg)](https://github.com/Crissal1995/automsr/actions/workflows/checks.yaml)

## Description

**AutoMSR** is an automation tool created for educational purpose,
intending to show how to use Selenium as an automation driver
for the Microsoft Rewards service.

### What it does

This tool is intended to show how to collect automatically daily points for
Microsoft Rewards.

What is included:
- Daily promotions completed.
- Other activities completed.
- Free punchcards completed.
- Searches with a desktop User Agent completed.
- Searches with a mobile User Agent completed.

### Warning

Before using this software, read carefully the [Microsoft Terms of Service](https://www.microsoft.com/servicesagreement),
section _Microsoft Rewards_.

TL;DR: the usage of AutoMSR could lead in a ban.

## Setup

### Installation

```shell
$ pip install automsr  # this will install the binary `automsr`
```

### Configuration

AutoMSR behaviour can be configured using a `config.yaml` file.

An example with every input described in detail is found here: [link](https://github.com/Crissal1995/automsr/blob/main/tests/configs/config.example.yaml).

### Chromedriver
Download the correct [Chromedriver](https://chromedriver.chromium.org/downloads) matching your Chrome version.

## Usage

### Help

```shell
$ automsr --help
```

### Execute AutoMSR

```shell
$ automsr run

# config.yaml is somewhere else than current directory
$ automsr run --config path/to/a/config.yaml
```

### Retrieve local Chrome profiles

```shell
$ automsr profiles
# ChromeProfile(displayed_name='yourProfileName', path=Path('generic/profile/dir'))

$ automsr profiles --format pretty-json
# [
#     {
#         "displayed_name": "yourProfileName",
#         "path": generic/profile/dir"
#     }
# ]
```

### Check that email sending works

```shell
$ automsr email
```
