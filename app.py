"""View: collect inputs and display the presenter's booking information."""

import streamlit as st

from constants import BOOKLET_PRICE, GUIDE_PRICE, MAX_BOOKLETS, MAX_VISITORS, PERIODS, VISITOR_CATEGORIES
from presenter import (
    booking_changed, build_receipt_text, capacity_status, compare_periods, money,
    offer_comparison, pricing_guide, receipt_table, reset_booking, submit_booking,
)

st.set_page_config(page_title="Tales of Lanfang Tickets", page_icon="🎟️")
st.title("Tales of Lanfang Tickets")
st.write("Build your booking and calculate the cheapest eligible ticket price. All amounts are SGD.")

with st.expander("Prices and booking rules"):
    for line in pricing_guide():
        st.write(line)

st.subheader("1. Visitors")
st.caption("Enter how many people are in each age category. Infants count toward the 20-person booking limit.")
# Outside a form: each input change reruns the view and updates capacity.
for field, label, _ in VISITOR_CATEGORIES:
    st.number_input(label, min_value=0, max_value=MAX_VISITORS, step=1, key=field)

capacity = capacity_status(st.session_state)
st.progress(capacity["progress"], text=f"{capacity['total']} of {MAX_VISITORS} visitors selected")
if capacity["excess"]:
    st.error(capacity["message"])
elif capacity["remaining"] == 0:
    st.success(capacity["message"])
else:
    st.caption(capacity["message"])
st.caption("This is the limit for one booking, not live venue availability.")

st.subheader("2. Visit period and extras")
st.radio("Visit period", PERIODS, key="period")
st.number_input(f"Number of audio guides ({money(GUIDE_PRICE)} each)", min_value=0, max_value=MAX_VISITORS, step=1, key="guides",
                help="At most one guide per paying visitor (adult, child or senior).")
st.number_input(f"Number of souvenir booklets ({money(BOOKLET_PRICE)} each)", min_value=0, max_value=MAX_BOOKLETS, step=1, key="booklets")
st.caption("Extras stay at full price. At least one paying visitor is required to add extras.")
submitted = st.button("Calculate total", key="calculate", disabled=capacity["excess"] > 0)
st.button("Reset booking", key="reset", on_click=reset_booking, args=(st.session_state,))

if submitted:
    result, errors = submit_booking(st.session_state)
    if errors:
        st.session_state.pop("last_result", None)
        for message in errors:
            st.error(message)
    else:
        st.session_state.last_result = result

if "last_result" in st.session_state:
    result = st.session_state.last_result
    booking = result["booking"]
    st.subheader("Last calculated booking")
    if booking_changed(st.session_state, result):
        st.warning("Inputs have changed. Calculate again to update this receipt and its comparisons.")
    st.caption(f"Submitted booking: {booking['adults']} adults, {booking['children']} children, "
               f"{booking['seniors']} seniors, {booking['infants']} infants · {booking['period']} · "
               f"{booking['guides']} guides, {booking['booklets']} booklets")
    st.metric("Total to pay (SGD)", money(result["total_cents"]))
    admission, extras, savings = st.columns(3)
    admission.metric("Admission", money(result["admission_cents"]))
    extras.metric("Extras", money(result["extras_cents"]))
    savings.metric("Offer savings", money(result["offer_savings_cents"]))
    st.caption("Offer savings compare with standard admission for the submitted period; extras are excluded.")
    st.write(f"**Selected offer: {result['applied_offer']}** — {result['explanation']}")
    st.markdown(receipt_table(result))
    st.download_button("Download receipt (.txt)", data=build_receipt_text(result),
                       file_name="lanfang-ticket-receipt.txt", mime="text/plain", key="download_receipt")

    with st.expander("Why was this offer selected?"):
        for line in offer_comparison(result):
            st.write(line)
        st.caption("Prices above are admission only. Family and Group do not stack. "
                   "Off-Peak is already included; extras are added afterwards.")

    st.subheader("Compare visit periods")
    st.caption("Same submitted visitors and extras, with the best eligible offer recalculated for each period.")
    periods = compare_periods(result)
    rows = ["| Period | Best offer | Admission | Extras | Total |", "| --- | --- | ---: | ---: | ---: |"]
    for comparison in periods:
        rows.append(f"| {comparison['booking']['period']} | {comparison['applied_offer']} | "
                    f"{money(comparison['admission_cents'])} | {money(comparison['extras_cents'])} | "
                    f"{money(comparison['total_cents'])} |")
    st.markdown("\n".join(rows))
    difference = periods[0]["total_cents"] - periods[1]["total_cents"]
    if difference > 0:
        st.info(f"This booking costs {money(difference)} less during Off-Peak. Extras cost the same.")
    elif difference == 0:
        st.info("This booking costs the same in both periods.")
else:
    st.info("Enter at least one visitor and select Calculate total.")
