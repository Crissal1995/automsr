# AutoMSR
[![Linters](https://github.com/Crissal1995/auto_msrewards/actions/workflows/linters.yaml/badge.svg)](https://github.com/Crissal1995/auto_msrewards/actions/workflows/linters.yaml)
[![Tests](https://github.com/Crissal1995/auto_msrewards/actions/workflows/tests.yaml/badge.svg)](https://github.com/Crissal1995/auto_msrewards/actions/workflows/tests.yaml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

README languages: **EN** [IT](README.IT.md)

## Description
**AutoMSR** is an automation tool created for educational purpose, 
intending to show how to use Selenium as an automation driver
for the Microsoft Rewards service.

### What it does
This tool is intended to show how to collect automatically daily points for
Microsoft Rewards.

It does:
- Completes daily activities
- Completes other activities
- Completes free punchcards
- Searches with a desktop User Agent (Edge on Windows)
- Searches with a mobile User Agent (Chrome on Android)

### Warning
Before using this software, read carefully [Microsoft Terms of Service][1],
section _Microsoft Rewards_.

## Usage

### Chromedriver
Download the correct [Chromedriver][2] matching your Chrome version.

### Credentials and Profiles
Create your `credentials.json` following the example file. 
The file is structured as a list of entries, where each entry represent a different
profile to use with AutoMSR.

There are two types of usage: via Login and via Profiles.

#### Login
*This is the old method, available for consistency.*

Each entry must provide `email` and `password`, and then the login will be performed in
a new Chrome session.

#### Profiles
*This is the new method.*

Each entry must provide `email` and `profile`, and then the corresponding
Chrome profile will be used. 

**This method assumes that your profile is correctly set**, so that:
- You are logged in your [Rewards homepage][rewards]
- You are logged in your [Bing homepage][bing] (upper right corner should
report your name, not Login) 

To get your profile name, you must head to [chrome://version](chrome://version)
and check *Profile Path*.

If both `profile` and `password` are found, this method is preferred. 

### Configuration
All configuration parameters are listed below in more detail. 
However, there are a few points worth noting, namely:
1. `automsr/email`: Email (or list of emails, comma separated) where to receive the 
status execution of AutoMSR.
2. `selenium/headless`: Displays (`false`) or not (`true`) the Chrome window during
execution. It has been empirically proven that a `false`
value gives greater stability to the system.
3. `selenium/path`: Full path to the chromedriver executable, if not found
in PATH environment variable.
4. `selenium/profile_root`: If used with Profiles (instead of Login), it must point to
the root of Chrome profiles.

### Python
Python version must be 3.7+.

You need to install the requirements with the command: 
```bash
python3 -m pip install -r requirements.txt
```

### Execution
Once you're done with configuration, you can execute AutoMSR with the command:
```bash
python3 main.py
```

*Note that, when running with Profiles, all Chrome process should be terminated.
You can however use other Chromium browsers, like Edge.*

## Configuration
The behaviour of the tool can be configured within `automsr.cfg`.

There are two main sections used in AutoMSR: **automsr** and **selenium**.

### automsr
#### credentials
The json file of credentials (should be a list of objects; see example file).

Defaults to `credentials.json`.

#### skip
AutoMSR can skip Rewards activities or Bing searches (or both). 
This value can be one of 
`no` (don't skip anything), 
`yes`, `all` (skip everything),
`search`, `searches` (skip Bing searches), 
`activity`, `activities` (skip Rewards activities).

Defaults to `no`.

#### retry
The number of times AutoMSR should retry missing or failed Rewards activities.

Defaults to `3`.

#### search_type
How to perform Bing searches. 
Can be either `random` 
(generate a random word, and then perform a search removing
one character at the end of the string at time) or `takeout` 
(uses Google searches, parsed from a Takeout Action).

Defaults to `random`.

#### email
The recipient email to send information regards the execution status; success if 
all points are redeemed, failure otherwise. 
The sender email is the one AutoMSR is currently working with.

If it's missing, no email will be sent.

Defaults to empty string.

#### verbose
Wether to increase console output verbosity or not; log files' verbosity is immutable.

Defaults to `False`.

### selenium
#### env
Wether the environment is using a chromedriver executable found in PATH (`local`), 
or a Selenium hub listening on a port, default 4444 (`remote`).

Defaults to `local`.

#### headless
Choose to start the Chrome session in headless mode or not.

Defaults to `true`.

#### path
Ignored when `env` is `remote`. The path to the chromedriver executable.

If missing, Selenium will search for the chromedriver in the PATH.

#### url
Ignored when `env` is `local`. Override of the url of the Selenium hub.

Defaults to `http://localhost:4444/wd/hub`.

#### logging
Enable or disable Selenium server logging.

Defaults to `true`.

#### profile_root
Root of the Chromium User Data directory (i.e. where Profiles are stored).
An example is:
```
C:\Users\<USER>\AppData\Local\Google\Chrome\User Data
```

Defaults to null.

[1]: https://www.microsoft.com/servicesagreement
[2]: https://chromedriver.chromium.org/downloads
[rewards]: https://rewards.microsoft.com/
[bing]: https://www.bing.com/
