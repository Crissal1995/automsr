# AutoMSR
[![Linters](https://github.com/Crissal1995/auto_msrewards/actions/workflows/linters.yaml/badge.svg)](https://github.com/Crissal1995/auto_msrewards/actions/workflows/linters.yaml)

## Description
**AutoMSR** is an automation tool created for educational purpose, 
intending to show how to use selenium as an automation driver
for the Microsoft Rewards referral program.

### What it does
This tool is intended to show how to collect automatically daily points for
Microsoft Rewards.

What it does:
- Completes daily activities
- Completes other activities
- Completes free punchcards
- Searches with a desktop User Agent (Edge on Windows)
- Searches with a mobile User Agent (Chrome on Android)

### Warning
Before using this software, read carefully [Microsoft Terms of Service][1],
section _Microsoft Rewards_.

## Usage
### Local
1. Place the chromedriver executable in your PATH
2. Create your `credentials.json` following the example file
3. Install requirements
4. Run `python main.py`
### Docker
1. Set the environment as `remote` ([refers to Selenium section](#selenium))
2. Build the image with `docker-compose build`
3. Run the containers with `docker-compose up`

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

### selenium
#### env
Wether the environment is using a chromedriver executable found in PATH (`local`), 
or a Selenium hub listening on a port, default 4444 (`remote`).

On a Docker setup, the environment should be `remote`.

Defaults to `local`.

#### headless
Choose to start the Chrome session in headless mode or not.

Defaults to `true`.

#### path
Ignored when `env` is `remote`. The path to the chromedriver executable.

If missing, Selenium will search for the chromedriver in the PATH.

#### url
Ignored when `env` is `local`. Override of the url of the Selenium hub.

Defaults to `http://selenium-hub:4444/wd/hub` (convenience url for Docker setup).

#### logging
Enable or disable Selenium server logging.

Defaults to `true`.

[1]: https://www.microsoft.com/servicesagreement
