Install dependencies with `pip install -r requirements.txt`.
Use `pip install -r requirements-dev.txt` to add the testing tools.

Run the test suite with:

```
pytest --maxfail=1 --disable-warnings
```

Run the downloader:

```
python bot.py
```

Launch the full pipeline including training and backtesting:

```
python orchestrator.py --hyperopt --live
```

Run the research loop to periodically update the model without executing trades:

```
python research_loop.py
```

Start the Streamlit dashboard to monitor results:

```
streamlit run dashboard.py
```
