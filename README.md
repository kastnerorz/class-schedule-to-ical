# Class Schedule to iCal

## How to Use

1. Install [Pipenv](https://pipenv.readthedocs.io/en/latest/install/)
2. Clone the project

```bash
git clone git@github.com:kastnerorz/class-schedule-to-ical.git
```

3. Install dependencies

```bash
cd class-schedule-to-ical
pipenv install
```
4. Set the params.
```python
url_index = url[i]  # i = 0 or 1
username = 'YOUR_ID'
password = 'YOUR_PASSWORD'
year = 2018, month = 11, day = 26 # term start date (Monday)
```
5. Run

```bash
pipenv run python main_v2.py
```

6. Import the `class_schedule.ics` to your calendar app.
7. Enjoy it!
