# First Words Tracker 👶

A simple Streamlit web app to track your child's vocabulary development.

## Features

- User registration with name
- Create profiles for multiple children
- Add words to each child's vocabulary
- Track when each word was added
- View complete word list for each child
- Delete words or entire child profiles
- Data persists between sessions (stored in `data.json`)

## Installation

1. Install Python (if not already installed)
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the App

```bash
streamlit run app.py
```

The app will open in your default web browser at `http://localhost:8501`

## How to Use

1. **Register**: Enter your name when you first open the app
2. **Add a Child**: Use the sidebar to add your child's profile
3. **Select Child**: Choose which child to track words for
4. **Add Words**: Enter new words your child has learned
5. **View Progress**: See the complete list of words with dates

## Data Storage

All data is stored locally in `data.json` in the same directory as the app.
