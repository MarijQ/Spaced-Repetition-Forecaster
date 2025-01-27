# MindNest

MindNest is an advanced, custom-built Spaced Repetition System (SRS) tailored to optimise your learning and retention by dynamically prioritising reviews based on recall, ease, and stability of previously seen items. This system offers powerful data visualisations, fine-grained control of learning pipelines, and flexible integration with study habits.

---

## Features

- **Dynamic Spaced Repetition**  
  A robust pipeline adapts to your recall strength, review ease, and forget rates using fine-tuned algorithms.

- **Customisable Learning Workflow**
  - Supports adding brand new study cards based on your capacity.
  - Enables manual rating of card difficulty with options like `f` (100%), `m` (80%), `h` (50%), and `l` (<50%).

- **Forecasting & Data Visualisation**
  - Automatically extrapolates study patterns for the next 1000 days.
  - Visualises your study allocation in interactive bar charts.

- **Integrated Study Mode**  
  Offers real-time instructions for the day, including overdue tasks, active reviews, and new card opportunities.

- **Interactive GUI**
  Built with `Tkinter` and `Matplotlib`, combining user-friendly functionality with powerful data input and visualisation tools.

---

## Table of Contents

1. [Installation](#installation)
2. [Usage](#usage)
3. [Technical Overview](#technical-overview)
4. [Upcoming Features](#upcoming-features)
5. [Contributing](#contributing)
6. [License](#license)

---

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/username/mindnest.git
   cd mindnest
   ```

2. **Install dependencies**
   Ensure you're using Python 3.8+ and install the required libraries:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   Execute the GUI interface:
   ```bash
   python ULS_v2.4.py
   ```

---

## Usage

- **Input Cards**  
  Add new cards with a unique ID and a review duration in minutes.

- **Run Study Sessions**  
  Open the `Study` tab for guided reviews:
  - View overdue and scheduled items based on recall intervals.
  - Record your confidence (`f`, `m`, `h`, `l`) after reviewing each item.

- **View Forecast**  
  Monitor upcoming study distribution, active tasks, and forecasted capacity through detailed visual charts.

---

## Technical Overview

- **Core Algorithms**  
  The system leverages advanced recall modelling:
  - Stability and ease factor adjustments based on review quality.
  - Simulation of long-term recall curves using spaced repetition maths.

- **Backend**  
  - Card management handled via `Pandas` DataFrames.
  - Flexible CSV storage for review history and pipeline updates.

- **Frontend**  
  - `Tkinter` GUI for real-time interaction.
  - `Matplotlib` for graphical representation of forecasts and progress.

---

## Upcoming Features

- **Web Version**  
  Port the application to a browser-based interface.

- **Performance Metrics**  
  Add historical performance tracking charts.

- **Enhanced Study Visuals**  
  Introduce button-based difficulty ratings with tooltips explaining each option.

- **Settings Customisation**  
  Add the ability to set forecast parameters, durations, and rating scores via a dedicated settings page.

---

## Contributing

If you'd like to contribute:
1. Fork the repository
2. Create a feature branch
3. Open a pull request with detailed documentation of your changes

Contributions to improve performance, algorithms, and UX are highly welcome!
