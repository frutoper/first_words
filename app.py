import streamlit as st
import json
import os
from datetime import datetime
from typing import Dict, List
from collections import defaultdict
import pandas as pd
import plotly.graph_objects as go

DATA_FILE = "data.json"
TYPICAL_WORDS_FILE = "typical_baby_words.csv"

def load_data() -> Dict:
    """Load data from JSON file."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {"user": None, "children": {}}

def save_data(data: Dict):
    """Save data to JSON file."""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def load_typical_words() -> pd.DataFrame:
    """Load typical baby words from CSV file."""
    if os.path.exists(TYPICAL_WORDS_FILE):
        return pd.read_csv(TYPICAL_WORDS_FILE)
    return pd.DataFrame(columns=["Word", "Typical Age (Months)"])

def get_practice_words(child_data: Dict) -> List[Dict]:
    """Get 5 words to practice based on low confidence and typical word order."""
    practice_words = []

    # Load typical words reference
    typical_words_df = load_typical_words()
    typical_words_order = {row['Word'].lower(): row['Typical Age (Months)']
                          for _, row in typical_words_df.iterrows()}
    typical_words_strategies = {row['Word'].lower(): row.get('Learning Strategy', '')
                               for _, row in typical_words_df.iterrows()}

    # Get low confidence words (< 50%) from child's vocabulary
    low_confidence_words = []
    for word_entry in child_data.get("words", []):
        if word_entry.get("confidence", 0) < 50:
            word_lower = word_entry["word"].lower()
            typical_age = typical_words_order.get(word_lower, 999)  # High number if not in typical list
            strategy = typical_words_strategies.get(word_lower, "Practice this word regularly with your child.")
            low_confidence_words.append({
                "word": word_entry["word"],
                "confidence": word_entry.get("confidence", 0),
                "typical_age": typical_age,
                "in_vocab": True,
                "strategy": strategy
            })

    # Sort by typical age (most common/earliest words first)
    low_confidence_words.sort(key=lambda x: x["typical_age"])

    # Add low confidence words to practice list
    practice_words.extend(low_confidence_words[:5])

    # If we need more words, add from typical words list
    if len(practice_words) < 5:
        # Get words already in child's vocabulary
        child_words_lower = {w["word"].lower() for w in child_data.get("words", [])}

        # Add typical words not yet in vocabulary
        for _, row in typical_words_df.iterrows():
            if len(practice_words) >= 5:
                break

            word_lower = row['Word'].lower()
            if word_lower not in child_words_lower:
                practice_words.append({
                    "word": row['Word'],
                    "confidence": 0,
                    "typical_age": row['Typical Age (Months)'],
                    "in_vocab": False,
                    "strategy": row.get('Learning Strategy', 'Practice this word regularly with your child.')
                })

    return practice_words[:5]

def create_csv_download(child_data: Dict, child_name: str) -> str:
    """Create a CSV string from child's word data."""
    if not child_data["words"]:
        return None

    # Prepare data for CSV
    csv_data = []
    for word_entry in child_data["words"]:
        csv_data.append({
            "Word": word_entry["word"],
            "Date First Used": word_entry["date_added"],
            "Speaks": "Yes" if word_entry.get("speaks", False) else "No",
            "ASL": "Yes" if word_entry.get("asl", False) else "No",
            "Confidence %": word_entry.get("confidence", 0)
        })

    # Create DataFrame and convert to CSV
    df = pd.DataFrame(csv_data)
    return df.to_csv(index=False)

def calculate_age_in_months(birthdate: str, target_date: str) -> int:
    """Calculate age in months between two dates."""
    birth = datetime.strptime(birthdate, "%Y-%m-%d")
    target = datetime.strptime(target_date, "%Y-%m-%d")

    months = (target.year - birth.year) * 12 + target.month - birth.month
    return months

def create_vocabulary_chart(child_data: Dict, child_name: str):
    """Create a bar chart showing vocabulary growth over time by age in months."""
    if not child_data["words"] or "birthday" not in child_data:
        return None

    birthday = child_data["birthday"]

    # Group words by age in months
    words_by_age = defaultdict(list)
    for word_entry in child_data["words"]:
        date = word_entry["date_added"]
        age_months = calculate_age_in_months(birthday, date)
        words_by_age[age_months].append(word_entry["word"])

    # Sort ages and calculate cumulative word count
    sorted_ages = sorted(words_by_age.keys())
    cumulative_count = []
    cumulative_total = 0
    age_labels = []
    words_per_period = []
    word_lists = []

    for age in sorted_ages:
        words_at_age = words_by_age[age]
        cumulative_total += len(words_at_age)
        cumulative_count.append(cumulative_total)
        age_labels.append(f"{age} months")
        words_per_period.append(len(words_at_age))
        word_lists.append("<br>".join(words_at_age))

    # Create bar chart with Plotly
    fig = go.Figure()

    # Add bars for cumulative word count
    fig.add_trace(go.Bar(
        x=age_labels,
        y=cumulative_count,
        text=cumulative_count,
        textposition='outside',
        marker=dict(color='#5DCCB4'),
        hovertemplate='<b>Age: %{x}</b><br>' +
                      'Total Words: %{y}<br>' +
                      'New Words: %{customdata[0]}<br>' +
                      '<b>Words added:</b><br>%{customdata[1]}<br>' +
                      '<extra></extra>',
        customdata=list(zip(words_per_period, word_lists)),
        name='Total Words'
    ))

    # Update layout
    fig.update_layout(
        title=f"{child_name}'s Vocabulary Growth",
        xaxis_title="Age (months)",
        yaxis_title="Total Words Known",
        showlegend=False,
        height=600,
        hovermode='closest',
        plot_bgcolor='white',
        font=dict(size=12)
    )

    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')

    return fig

def main():
    st.set_page_config(page_title="First Words Tracker", page_icon="👶", layout="wide")

    # Initialize session state
    if 'data' not in st.session_state:
        st.session_state.data = load_data()

    data = st.session_state.data

    # Header
    st.title("👶 First Words Tracker")

    # User Registration
    if data["user"] is None:
        st.subheader("Welcome! Please register to get started")
        with st.form("register_form"):
            user_name = st.text_input("Your Name")
            submit = st.form_submit_button("Register")

            if submit and user_name:
                data["user"] = user_name
                save_data(data)
                st.rerun()
            elif submit:
                st.error("Please enter your name")
    else:
        # Show logged in user
        st.sidebar.write(f"**Logged in as:** {data['user']}")

        if st.sidebar.button("Logout"):
            data["user"] = None
            save_data(data)
            st.rerun()

        st.sidebar.markdown("---")

        # Add New Child
        st.sidebar.subheader("Add New Child")
        with st.sidebar.form("add_child_form"):
            child_name = st.text_input("Child's Name")
            child_birthday = st.date_input("Birthday")
            add_child = st.form_submit_button("Add Child")

            if add_child and child_name:
                if child_name not in data["children"]:
                    data["children"][child_name] = {
                        "words": [],
                        "birthday": child_birthday.strftime("%Y-%m-%d")
                    }
                    save_data(data)
                    st.rerun()
                else:
                    st.error("Child already exists")
            elif add_child:
                st.error("Please enter a name")

        # Page Navigation
        page = st.sidebar.radio("Navigate", ["Track Words", "View Chart", "Practice Words"])

        # Main Content
        if not data["children"]:
            st.info("👈 Add your first child using the sidebar to get started!")
        else:
            # Select Child
            st.subheader("Select a Child")
            selected_child = st.selectbox(
                "Choose a child to track words for:",
                options=list(data["children"].keys())
            )

            if selected_child:
                child_data = data["children"][selected_child]

                # Show birthday if available
                if "birthday" in child_data:
                    st.write(f"**Birthday:** {child_data['birthday']}")

                st.markdown("---")

                # Page content based on selection
                if page == "View Chart":
                    # Chart Page
                    if child_data["words"] and "birthday" in child_data:
                        chart = create_vocabulary_chart(child_data, selected_child)
                        if chart:
                            st.plotly_chart(chart, use_container_width=True)
                    elif not child_data["words"]:
                        st.info(f"No words yet! Add some words to {selected_child}'s vocabulary first.")
                    else:
                        st.warning(f"Please add a birthday for {selected_child} to view the chart by age.")
                        with st.form("add_birthday_form"):
                            new_birthday = st.date_input("Birthday")
                            if st.form_submit_button("Add Birthday"):
                                child_data["birthday"] = new_birthday.strftime("%Y-%m-%d")
                                save_data(data)
                                st.rerun()

                elif page == "Practice Words":
                    # Practice Words Page
                    st.subheader("Practice Words")
                    st.write("Focus on these 5 words to help your child build their vocabulary!")

                    practice_words = get_practice_words(child_data)

                    if practice_words:
                        st.markdown("---")

                        for idx, word_info in enumerate(practice_words, 1):
                            with st.container():
                                col1, col2 = st.columns([3, 1])

                                with col1:
                                    st.markdown(f"### {idx}. {word_info['word'].upper()}")

                                    if word_info['in_vocab']:
                                        st.write(f"**Status:** In vocabulary (Confidence: {word_info['confidence']}%)")
                                    else:
                                        st.write(f"**Status:** Not yet learned")

                                    st.write(f"**Typical age:** {word_info['typical_age']} months")

                                    # Display learning strategy in info box
                                    if word_info.get('strategy'):
                                        st.info(f"💡 **Learning strategy:** {word_info['strategy']}")

                                with col2:
                                    st.write("")  # Spacer
                                    if word_info['in_vocab']:
                                        st.success("✓ Known")
                                    else:
                                        st.warning("New")

                                st.markdown("---")
                    else:
                        st.info("Add some words to your child's vocabulary to get personalized practice suggestions!")

                elif page == "Track Words":
                    # Track Words Page
                    # Two columns: Add word and Word list
                    col1, col2 = st.columns([1, 2])

                    with col1:
                        st.subheader(f"Add Word for {selected_child}")
                        with st.form("add_word_form", clear_on_submit=True):
                            new_word = st.text_input("New Word")
                            word_date = st.date_input("Date first used", value=datetime.now())

                            st.write("**How does the child know this word?**")
                            speaks = st.checkbox("Speaks", value=False)
                            asl = st.checkbox("ASL (Sign Language)", value=False)

                            confidence = st.slider("Confidence %", 0, 100, 50, 5,
                                                 help="How likely is the child to demonstrate this word when not distracted?")

                            add_word = st.form_submit_button("Add Word")

                            if add_word and new_word:
                                word_entry = {
                                    "word": new_word.strip(),
                                    "date_added": word_date.strftime("%Y-%m-%d"),
                                    "speaks": speaks,
                                    "asl": asl,
                                    "confidence": confidence
                                }
                                child_data["words"].append(word_entry)
                                save_data(data)
                                st.success(f"Added '{new_word}' to {selected_child}'s vocabulary!")
                                st.rerun()
                            elif add_word:
                                st.error("Please enter a word")

                    with col2:
                        st.subheader(f"{selected_child}'s Vocabulary")

                        if child_data["words"]:
                            # Header with total and download button
                            col_header1, col_header2 = st.columns([2, 1])
                            with col_header1:
                                st.write(f"**Total Words: {len(child_data['words'])}**")
                            with col_header2:
                                csv_data = create_csv_download(child_data, selected_child)
                                if csv_data:
                                    st.download_button(
                                        label="Download CSV",
                                        data=csv_data,
                                        file_name=f"{selected_child}_vocabulary.csv",
                                        mime="text/csv"
                                    )

                            # Display words in a nice format
                            for idx, word_entry in enumerate(reversed(child_data["words"])):
                                actual_idx = len(child_data["words"]) - 1 - idx

                                # Build display summary
                                methods = []
                                if word_entry.get("speaks", False):
                                    methods.append("Speaks")
                                if word_entry.get("asl", False):
                                    methods.append("ASL")
                                methods_str = ", ".join(methods) if methods else "Not specified"
                                confidence_str = f"{word_entry.get('confidence', 0)}%"

                                with st.expander(f"**{word_entry['word']}** - {methods_str} ({confidence_str})"):
                                    st.write(f"**Date first used:** {word_entry['date_added']}")

                                    # Edit form for each word
                                    with st.form(key=f"edit_{selected_child}_{idx}"):
                                        edit_word = st.text_input("Word", value=word_entry['word'])
                                        edit_date = st.date_input(
                                            "Date first used",
                                            value=datetime.strptime(word_entry['date_added'], "%Y-%m-%d")
                                        )

                                        st.write("**How does the child know this word?**")
                                        edit_speaks = st.checkbox("Speaks", value=word_entry.get("speaks", False))
                                        edit_asl = st.checkbox("ASL (Sign Language)", value=word_entry.get("asl", False))

                                        edit_confidence = st.slider(
                                            "Confidence %",
                                            0, 100,
                                            word_entry.get("confidence", 50),
                                            5,
                                            help="How likely is the child to demonstrate this word when not distracted?"
                                        )

                                        col_save, col_del = st.columns(2)
                                        with col_save:
                                            save_changes = st.form_submit_button("Save Changes")
                                        with col_del:
                                            delete_word = st.form_submit_button("Delete Word", type="primary")

                                        if save_changes:
                                            child_data["words"][actual_idx] = {
                                                "word": edit_word.strip(),
                                                "date_added": edit_date.strftime("%Y-%m-%d"),
                                                "speaks": edit_speaks,
                                                "asl": edit_asl,
                                                "confidence": edit_confidence
                                            }
                                            save_data(data)
                                            st.success(f"Updated '{edit_word}'!")
                                            st.rerun()

                                        if delete_word:
                                            child_data["words"].pop(actual_idx)
                                            save_data(data)
                                            st.rerun()
                        else:
                            st.info(f"No words yet! Start adding {selected_child}'s first words using the form on the left.")

                    st.markdown("---")

                    # Delete Child Option
                    with st.expander("⚠️ Delete Child Profile"):
                        st.warning(f"This will permanently delete {selected_child}'s profile and all their words.")
                        if st.button(f"Delete {selected_child}", type="primary"):
                            del data["children"][selected_child]
                            save_data(data)
                            st.rerun()

if __name__ == "__main__":
    main()
