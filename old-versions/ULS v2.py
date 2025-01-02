import datetime
import random as rd
import tkinter as tk
from datetime import datetime as dt
from tkinter import ttk

import pandas as pd
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg)
from matplotlib.figure import Figure


class Engine():
    def __init__(self):
        self.read_files()
        self.update_cards()

    pipeline = [[]]

    def read_files(self):
        self.forecast = pd.read_csv('availability.csv')
        self.cards = pd.read_csv('cards.csv')
        self.reviews = pd.read_csv('reviews.csv')

    def update_cards(self):
        self.cards['last_record'] = 0
        self.cards['next_due'] = 0
        self.cards['current_interval'] = 0
        for index, row in self.cards.iterrows():
            card_id = row['card_id']
            self.cards.loc[index, 'last_record'] = self.find_last_record(card_id)
            self.cards.loc[index, 'next_due'] = self.find_next_due(card_id)
            self.cards.loc[index, 'current_interval'] = self.find_next_due(card_id)
        print(self.cards)

    def find_last_record(self,card_id):
        instances = self.reviews[self.reviews['card_id'] == card_id]
        if instances.empty:
            return [None, None, None]
        else:
            instances = instances.sort_values(by='next_due').tail(1)
            return instances.iloc[0]['date']

    def find_next_due(self,card_id):
        instances = self.reviews[self.reviews['card_id'] == card_id]
        if instances.empty:
            return None
        else:
            instances = instances.sort_values(by='next_due').tail(1)
            return instances.iloc[0]['next_due']

    def calculate_interval_old(self, card_id):
        instances = self.reviews[self.reviews['card_id'] == card_id]
        instances = instances.sort_values(by='date').tail(2)
        print(card_id, len(instances.index))
        if len(instances.index) == 2:
            date1 = dt.strptime(instances.loc[0, 'date'], '%Y-%m-%d').date()
            date2 = dt.strptime(instances.loc[1, 'date'], '%Y-%m-%d').date()
            last_code = instances.loc[1, 'rating']
            match last_code:
                case 'f':
                    multiplier = 2
                case 'm':
                    multiplier = 1.5
                case 'h':
                    multiplier = 1
                case 'l':
                    multiplier = 0.5
            current_interval = (date2 - date1).days
            next_interval = current_interval * multiplier * (
                        0.8 + rd.random() * 0.4)
            next_due = date2 + next_interval
            current_interval = next_due = overdue_ratio = 1
        elif len(instances.index) == 1:
            current_interval = 1
            next_due = dt.strptime(instances.iloc[0]['date'],
                                   '%Y-%m-%d').date() + datetime.timedelta(
                days=current_interval)
            overdue_ratio = (
                                        dt.today().date() - next_due).days / current_interval
        else:
            current_interval = next_due = overdue_ratio = 1
        current_interval = len(instances.index)
        return [current_interval, next_due, overdue_ratio]

    def decode_date(self,string):
        return dt.strptime(string, '%Y-%m-%d').date()

class GUI(Engine):
    def __init__(self, window):
        Engine.__init__(self)
        # tkinter settings
        s = ttk.Style()
        self.font = ('Segoe UI', 24)
        s.configure('.', font=self.font)

        # Set up tabs
        tabControl = ttk.Notebook(window)
        self.set_up_tabs(tabControl)
        self.input_visuals(self.tab_input)
        self.forecast_visuals(self.tab_forecast)
        self.study_visuals(self.tab_study)

    def nextline(self, r):
        r += 1
        c = 0
        return r, c

    def submit_card(self):
        # append new card to 'cards' dataframe
        self.cards.loc[len(self.cards), :] = [int(self.ent_ID.get()),
                                              int(self.ent_duration.get())]
        self.reviews.loc[len(self.cards), :] = [dt.today().date(),
                                                int(self.ent_ID.get()), 's']
        # trim dataframes for writing
        cards_to_write = self.cards.loc[:, ['card_id', 'duration']]
        cards_to_write = cards_to_write.astype('int')
        reviews_to_write = self.reviews.loc[:, ['date', 'card_id', 'rating', 'next_due']]
        reviews_to_write['card_id'] = reviews_to_write['card_id'].astype(int)
        # write to files
        with open("cards.csv", "w+", newline='') as file:
            cards_to_write.to_csv(file, encoding='utf-8',
                                  index=False)
        with open("reviews.csv", "w+", newline='') as file:
            reviews_to_write.to_csv(file, encoding='utf-8', index=False)
        # clear entry widgets
        self.ent_ID.delete(0, 'end')
        self.ent_ID.insert(0, self.cards.loc[:, 'card_id'].max() + 1)
        self.ent_duration.delete(0, 'end')

    def set_up_tabs(self, notebook):
        self.tab_input = ttk.Frame(notebook)
        self.tab_forecast = ttk.Frame(notebook)
        self.tab_study = ttk.Frame(notebook)

        notebook.add(self.tab_input, text='Input')
        notebook.add(self.tab_forecast, text='Forecast')
        notebook.add(self.tab_study, text='Study')
        notebook.pack(expand=1, padx=10, fill="both")

    def input_visuals(self, frame):
        # create widgets
        self.lab_ID = ttk.Label(frame, text="ID")
        self.ent_ID = ttk.Entry(frame, font=self.font, width=7)
        self.ent_ID.insert(0, self.cards.loc[:, 'card_id'].max() + 1)
        self.lab_duration = ttk.Label(frame, text="Duration (mins)")
        self.ent_duration = ttk.Entry(frame, font=self.font, width=7)
        self.but_submit = ttk.Button(frame, text='Submit',
                                     command=self.submit_card)

        # pack widgets
        r = c = 0
        self.lab_ID.grid(row=r, column=c, padx=10, pady=10)
        c += 1
        self.ent_ID.grid(row=r, column=c)
        # (r, c) = self.nextline(r, c)
        c += 1
        self.lab_duration.grid(row=r, column=c, padx=10, pady=10)
        c += 1
        self.ent_duration.grid(row=r, column=c)
        c += 1
        self.but_submit.grid(row=r, column=c)

    def forecast_visuals(self, frame):
        # create widgets
        fig = Figure(figsize=(10, 4), dpi=100)
        self.subplot = fig.add_subplot(111)
        self.subplot.bar(self.forecast.loc[0:30, 'date'],
                         self.forecast.loc[0:30, 'capacity'],
                         tick_label=[s[:2] for s in
                                     self.forecast.loc[0:30, 'date']])
        # pack widgets
        self.img_plot = FigureCanvasTkAgg(fig, master=frame)
        self.img_plot.get_tk_widget().grid(row=0, column=0)

    def study_visuals(self, frame):
        # create widgets
        pass
        # pack widgets


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Ultimate Learning System v2")
    GUI(root)
    root.mainloop()
