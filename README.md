
# 🤖 Shahrekord University (SESS) Registration Bot

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
</p>

This project is a Python script that fully automates the course registration process on the **SESS academic portal** for Shahrekord University. Using the Selenium library, the bot handles logging in, waiting for the registration window to open, and registering for a predefined list of courses automatically.

## ✨ Features

- **Automatic Login**: Securely logs into the SESS portal using your credentials.
- **Smart Retry Mechanism**: If the registration window isn't open, the bot intelligently retries every 10 seconds.
- **Batch Course Registration**: Reads a list of desired courses from a `.env` file and attempts to register them.
- **Subgroup Support**: Handles courses with and without subgroups (e.g., lab sections).
- **System Message Handling**: Intelligently processes system feedback messages, such as success, time conflicts, or credit limit errors.
- **Status Reporting**: Checks and reports the reasons why certain courses are unavailable for registration.

---

## ⚙️ Setup & Installation

Follow these steps to get the project up and running.

### 1. Prerequisites

- **Python 3.8** or higher
- **Google Chrome** browser

### 2. Installation

1.  First, clone the repository to your local machine:
    ```bash
    git clone [https://github.com/rashcode-com/Sess-Registration-Bot.git](https://github.com/rashcode-com/Sess-Registration-Bot.git) cd Sess-Registration-Bot
    ```

2.  Install the required dependencies using `pip`. It's highly recommended to do this within a virtual environment.
    ```bash
    pip install -r requirements.txt
    ```

### 3. Configuration

1.  Create a `.env` file by making a copy of the provided sample file.
    ```bash
    # On Windows
    copy .env.sample .env

    # On Linux or macOS
    cp .env.sample .env
    ```

2.  Open the `.env` file and edit it with your personal information.

| Variable | Description | Example |
| :--- | :--- | :--- |
| `SESS_USERNAME` | Your student ID number. | `s4011000000` |
| `SESS_PASSWORD` | Your password for the SESS portal. | `YourPassword` |
| `COURSES` | A comma-separated list of courses. Format: `unit_code:group_code` or `unit_code:group_code:subgroup_code`. | `"190200000:1,190100000:1:1"` |
| `SEMESTER` | The 5-digit code for the academic semester. | `"14041"` |

---

## 🚀 How to Run

Once you have configured your `.env` file, simply run the main script from your terminal:

```bash
python main.py
```
The bot will launch a Chrome browser and begin the automated registration process. A full report of its actions will be printed in the terminal.

---

## ⚖️ Disclaimer

This tool was developed for educational purposes and to facilitate the personal course registration process. The user is solely responsible for any misuse of this script.
