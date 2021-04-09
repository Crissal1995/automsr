# AutoMSR
[![Linters](https://github.com/Crissal1995/auto_msrewards/actions/workflows/linters.yaml/badge.svg)](https://github.com/Crissal1995/auto_msrewards/actions/workflows/linters.yaml)

## Description
**AutoMSR** is an automation tool created for educational purpose, 
intending to show how to use selenium as an automation driver
for the Microsoft Rewards referral program.

### What it does
This tool is intended to show how to collect automatically daily points for
Microsoft Rewards.

What it does is:
- Completing daily activities
- Completing other activities
- Completing free punchcards
- Searching with a desktop User Agent (Edge on Windows)
- Searching with a mobile User Agent (Chrome on Android)

### Warning
Before using this software, read carefully [Microsoft Terms of Service][1],
section _Microsoft Rewards_.

## Usage
1. Create your `credentials.json` following the example file
2. Install requirements 
3. [Optional] Change headless state in `main()`
4. Run `python main.py`

[1]: https://www.microsoft.com/servicesagreement
