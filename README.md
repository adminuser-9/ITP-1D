# Tales of Lanfang Ticket Calculator

ITP 1D assignment extending the ticketing starter code

## Files Overview

| File | Role |
| --- | --- |
| `mylibrary.py` | **Model:** validates bookings, calculates admission and extras, returns a receipt dictionary |
| `app.py` | **View:** creates Streamlit widgets and displays results/errors |
| `presenter.py` | **Presenter:** handles submitted values, resets state, and formats the model's result for the view |
| `constants.py` | Fixed prices, discount percentages, limits, and visitor labels |
| `tests/` | Pricing examples, validation, presenter, and Streamlit checks |

## MVP Structure (Model-View-Presenter)
The View calls the Presenter, which calls the Model. Neither the Presenter nor the Model imports Streamlit. The pricing engine uses ordinary `if` statements; there is no strategy registry, class hierarchy, or separate pricing package.

## Run

From this folder in PowerShell, with Python 3.10 or newer:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Skip virtual-environment creation if `.venv` already exists. Open the URL printed by Streamlit (normally http://localhost:8501). Stop with Ctrl+C.

## Pricing rules

All prices are SGD; visitors select Peak or Off-Peak manually.

| Category / offer | Rule |
| --- | --- |
| Adults, 13-59 | $10 |
| Children, 4-12 | $5 |
| Seniors, 60+ | $7 |
| Infants, 0-3 | Free; included in visitor count |
| Audio guides | $3 each; maximum one per paying visitor |
| Souvenir booklets | $4 each; maximum 20 per booking |
| Off-Peak | 20% off standard admission rates and family bundles |
| Family | Each 2 adults + 2 children costs $25 Peak / $20 Off-Peak; remaining visitors pay period rates |
| Group | 10+ paying visitors receive 10% off period-adjusted standard admission |

Calculate Standard admission first. `calculate_family_cost(booking)` and `calculate_group_cost(booking)` each return admission cost in cents, receipt items, and an explanation, or `None` when ineligible. These helpers expect validated bookings; `calculate_booking` validates inputs and compares their independently calculated prices. Select the cheapest eligible offer; Family and Group never stack. Strict `<` comparisons retain Standard before Family before Group on a tie. Add full-price extras after selecting admission.

Bookings allow 1-20 visitors, including infants. Inputs must be nonnegative integers (not booleans). Infants do not count toward Group eligibility. Extras require a paying visitor; infant-only bookings without extras are valid. Missing fields and unknown periods are rejected.

Prices such as `ADULT_PRICE = 1000` are **integer cents**, avoiding floating-point currency errors. Period pricing is rounded half up per ticket/bundle; Group is rounded once on standard admission. The current rates divide exactly. The display formats two decimal places.

## Assignment functions and data

`calculate_total(adults, children)` returns the original adult and child subtotals in whole dollars. `audio_guides(items)` returns the original guide cost in dollars. Therefore 2 adults + 2 children + 2 guides costs $36 under the original rules.

The final app uses `calculate_booking(booking)` instead. Supply a dictionary with `adults`, `children`, `seniors`, `infants`, `guides`, `booklets`, and `period`. It returns a dictionary containing a copy of the booking, eligibility prices (`None` means ineligible), selected offer, receipt items, admission, savings, extras, and total. All money fields in this result end in `_cents`. Invalid bookings raise `ValueError`; the presenter uses `validate_booking` to display individual errors.

`st.number_input` collects quantities and `st.radio` selects the period. Inputs are outside a form so each change updates the live capacity indicator. The Calculate button submits values for pricing. Widget keys store their values in `st.session_state`; `last_result` retains the last submitted receipt across reruns. Editing inputs does not recalculate that receipt: a warning identifies changed inputs. Invalid submissions clear the previous receipt. Reset clears inputs and receipt. Session state is not permanent storage.

## User experience features

- Live visitor count, remaining places, and progress bar, including infants. At 20, show capacity reached; above 20, state how many visitors to remove and disable Calculate. This is a per-booking limit, not venue availability.
- Readable itemised receipt with total, admission, extras, and clearly labelled offer savings. Group discounts appear as negative receipt lines so charges reconcile.
- Explanations for selected, more expensive, tied, and ineligible offers. Family and Group never stack.
- Peak/Off-Peak comparison for the same submitted basket, repriced through the existing engine. Extras remain unchanged. Free infant-only bookings show equal totals.
- Downloadable plain-text receipt matching the saved calculation. This is a price estimate, not a completed reservation or payment.

The receipt, comparison, and download always refer to the submitted quantities shown above them. Click Calculate again after edits.

## Check correctness

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Streamlit AppTest checks actual reruns and state without a browser. It needs local event-loop sockets; use a normal terminal if a sandbox blocks them. To check only the engine, use `-p test_pricing.py`; original assignment tests use `-p test_baseline.py`.

| Example | Selected offer | Total |
| --- | --- | --- |
| 1 adult + 1 child, Peak | Standard | $15.00 |
| 2 adults + 2 children + 2 guides, Peak | Family | $31.00 |
| Same booking, Off-Peak | Family | $26.00 |
| 4 adults + 4 children, Peak | Family (2 bundles) | $50.00 |
| 10 adults, Peak | Group | $90.00 |
| 10 adults, Off-Peak | Group | $72.00 |
| 2 adults + 2 children + 6 seniors, Peak | Group | $64.80 |
| 1 senior + 1 infant + 1 guide, Off-Peak | Standard | $8.60 |
| 1 infant without extras | Standard | $0.00 |
| 4 adults + 12 children, Peak | Family (tie with Group) | $90.00 |

All 20 tests pass. They cover invalid types, negative quantities, capacity (empty, below cap, at cap, over cap), eligibility boundaries, receipt arithmetic, unchanged extras, saved input copies, presenter handling, and reset. Streamlit checks verify live capacity, disabled calculation above the cap, changed-input warnings, receipt metrics, and download content. Browser visual and keyboard checks should still be performed before submission. History, actual reservations, and payments are outside the current scope.
