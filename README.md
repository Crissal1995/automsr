# AutoMSR
[![Checks](https://github.com/Crissal1995/automsr/actions/workflows/checks.yaml/badge.svg)](https://github.com/Crissal1995/automsr/actions/workflows/checks.yaml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

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
$ pip install automsr  # this will install the binaries `automsr` and `automsr-profiles`
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
$ automsr

# config.yaml is somewhere else than current directory
$ automsr --config path/to/a/config.yaml
```

### Retrieve local Chrome profiles

```shell
$ automsr-profiles
# [{"name": "<profileName>", "path": "<absolutePathToProfileDirectory>"}]
```
