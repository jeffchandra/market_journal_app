# app.py
import streamlit as st
from datetime import date
from storage import init_db, save_weekly, get_weekly_history, get_avg_scores
from evaluator import analyze
from fetcher import fetch_news, fetch_price_summary, extract_ticker

init_db()

st.title("Market Intuition Journal")

tab1, tab2 = st.tabs(["Entry", "Progress"])

with tab1:
    st.subheader("Deep Dive")
    event = st.text_input("Market event")
    analysis = st.text_area("Your analysis", height=200)
    
    if st.button("Submit and Evaluate"):
        if not event or not analysis:
            st.error("Fill in both fields.")
        else:
            news = fetch_news(event)
            ticker = extract_ticker(event)
            price_summary = fetch_price_summary(ticker)
            history = get_weekly_history(3)
            result = analyze({"analysis": analysis}, history, news, price_summary)
            if "error" not in result:
                save_weekly({
                    "date": str(date.today()),
                    "news": news,
                    "analysis": analysis,
                    "score": result["score"],
                    "assessment": result["assessment"]
                })
                st.metric("Intuition Score", f"{result['score']} / 10")
                st.markdown("### Feedback")
                st.write(result["assessment"])

with tab2:
    st.subheader("History")
    history = get_weekly_history(1)
    max_id = history[0]['id'] if history else 0
    if max_id == 0:
        st.caption("No recorded history yet!")
    else:
        past_week = st.number_input("Past Weeks", value=3)
        
        if st.button("Find History"):
            if past_week < 1 or past_week > max_id:
                st.error(f"Number of entries should be positive and below {max_id}")
            else:
                st.json(get_weekly_history(past_week))
    
