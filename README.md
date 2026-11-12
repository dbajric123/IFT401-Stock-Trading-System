# Stock Trading System - IFT 401 Capstone

A Flask + MySQL web app where stockbroker trainees buy and sell simulated stocks,
and an administrator creates stocks and sets market hours. Built by hand following
the Capstone Project Handbook and deployed on AWS (EC2 + RDS).

Team: Dino Bajric, Nikolas Hooper-Torres, Vipra Mehta

## Who built what

| Page | URL | Template | Owner |
|---|---|---|---|
| Log In | /login | login.html | Nikolas |
| Create Account | /register | register.html | Nikolas |
| Manage Stocks (admin) | /admin/stocks | admin_stocks.html | Nikolas |
| Market Hours (admin) | /admin/market-hours | admin_market_hours.html | Nikolas |
| Price Monitor (admin) | /admin/prices | admin_prices.html | Nikolas |
| Buy Stock | /buy | buy.html | Dino |
| Sell Stock | /sell | sell.html | Dino |
| My Portfolio | / | dashboard.html | Vipra |
| Create Portfolio | /portfolio/new | create_portfolio.html | Vipra |
| Stock Inventory | /stocks | stocks.html | Vipra |
| Deposit Cash | /deposit | deposit.html | Vipra |
| Withdraw Cash | /withdraw | withdraw.html | Vipra |
| Transaction History | /history | history.html | Vipra |

Each person's code is in their own section of `app.py` (`# === NIKOLAS ===`,
`# === DINO ===`, `# === VIPRA ===`).

## Folder structure (handbook Chapter 0)

The `venv` folder goes next to the project folder, not inside it.

```
IFT401/                            <- root folder (you make this)
├── venv/
└── IFT401-Stock-Trading-System/   <- this repo (project folder)
    ├── .gitignore
    ├── README.md
    ├── requirements.txt
    ├── app.py
    ├── templates/
    │   ├── base.html
    │   └── ...one .html file per page
    └── static/
```

## Setup (one time)

1. Install Python, Visual Studio Code and GitHub Desktop (handbook Chapter 0).
2. Make a root folder, for example `IFT401`.
3. In GitHub Desktop click **File > Clone repository**, pick this repo, and set the
   local path to your root folder.
4. Open a terminal in the root folder and make the virtual environment:
   - Windows: `python -m venv venv`
   - Mac: `python3 -m venv venv`
5. Activate it (you will see `(venv)` at the start of the line):
   - Windows: `venv\Scripts\activate`
   - Mac: `source venv/bin/activate`
6. Install the packages: `pip install -r IFT401-Stock-Trading-System/requirements.txt`
   (use `pip3` on Mac).

## Run the app

1. Activate the virtual environment (step 5 above).
2. `cd IFT401-Stock-Trading-System`
3. `flask run`
4. Open http://127.0.0.1:5000

The app connects to our shared AWS RDS database (handbook Chapter 6), so everyone
sees the same data. Check the tables in MySQL Workbench with the "AWS RDS" connection.

To make someone an administrator, change their `role` to `admin` in the `users` table
in MySQL Workbench and click Apply (handbook Chapter 5).

## How we use GitHub (handbook Chapter 0)

We all work on the `main` branch in GitHub Desktop. Only one person pushes at a time.

Every time you work:

1. Click **Pull origin** first.
2. Write your code and test it with `flask run`.
3. Write a clear commit message (for example "Add buy confirm step"), click
   **Commit to main**, then **Push origin**.
4. Say "pushed" in the group chat so the next person pulls first.

The GitHub grade is per person (lines of code, commits, code frequency, business
functions), so commit small pieces and push on different days.

Only edit your own section of `app.py` and your own templates. Ask the group before
changing `base.html`, a table, or a shared helper.

## Deploy to AWS EC2 (handbook Chapter 7)

1. Before deploying, run `pip freeze > requirements.txt` in the activated venv and push it.
2. On the EC2 server:
   ```
   sudo apt update
   sudo apt upgrade -y
   sudo apt install python3 python3-pip python3-venv git screen -y
   git clone https://github.com/dbajric123/IFT401-Stock-Trading-System.git
   cd IFT401-Stock-Trading-System
   python3 -m venv venv
   source venv/bin/activate
   pip3 install -r requirements.txt
   screen
   flask run --host 0.0.0.0 --port 5000
   ```
3. Press CTRL+A then D to leave it running. Open `http://<EC2 public DNS>:5000`.
