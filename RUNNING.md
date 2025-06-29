Install dependencies with `pip install -r requirements.txt`.
Use `pip install -r requirements-dev.txt` to add the testing tools.

Run the downloader:

```
python bot.py
```

Launch the full pipeline including training and backtesting:

```
python orchestrator.py --hyperopt --live
```

Start the Streamlit dashboard to monitor results:

```
streamlit run dashboard.py
```
