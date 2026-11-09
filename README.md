# Stock Trading System - IFT 401 Capstone

A Flask + MySQL web app where stockbroker trainees buy and sell simulated stocks,
and an administrator creates stocks and sets market hours. Runs on AWS (EC2 + RDS).

Team: Dino Bajric, Nikolas Hooper-Torres, Vipra Mehta

## Run it locally

1. Create a MySQL database named `stock_trading`
2. `python -m venv venv`
3. `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux)
4. `pip install -r requirements.txt`
5. Put your own MySQL password in the database URI in `app.py`
6. `python -m flask --app app run` and open http://127.0.0.1:5000

## How we work

- Work on your own branch: `dino`, `nikolas` or `vipra`
- Only edit your own section of `app.py` and your own templates
- Run `git pull origin main` before you start
- Commit small steps every day you work
- Open a pull request into `main` when a feature works
- Ask the group before changing `base.html`, a table, or a shared helper
