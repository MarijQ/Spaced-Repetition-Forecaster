import datetime
import random as rd
import tkinter as tk
from datetime import datetime as dt
from tkinter import ttk

import pandas as pd
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg)
from matplotlib.figure import Figure

# import settings
pd.set_option('display.min_rows', 20)
pd.set_option('display.max_columns', 20)


class Engine():
    def __init__(self):
        self.read_files()
        self.update_cards()
        self.generate_forecast()

    pipeline = [[]]
    next_day = False
    new_dur = 0
    max_blend = 0
    max_blend_allowed = 7

    def read_files(self):
        self.forecast = pd.read_csv('forecast.csv')
        self.cards = pd.read_csv('cards.csv')
        self.history = pd.read_csv('history.csv')

    def update_cards(self):
        self.cards['next_interval'] = 0
        self.cards['next_due'] = 0
        for index, row in self.cards.iterrows():
            card_id = row['card_id']
            self.cards.loc[
                index, ['next_interval', 'next_due']] = self.find_last_record(
                card_id)
            self.cards['next_interval'] = self.cards['next_interval'].astype(
                'int')

    def generate_pipeline(self, active_cards):
        if active_cards:
            for index, row in self.cards.iterrows():
                card_id = row['card_id']
                next_interval = row['next_interval']
                next_due = row['next_due']
                duration = row['duration']
                instances = self.generate_future_cards(card_id, next_interval,
                                                       next_due, duration)
                self.pipeline += instances
        self.pipeline = [x for x in self.pipeline if x]
        # convert pipeline to dataframe
        columns = ['card_id', 'next_interval', 'next_due', 'duration']
        self.pipeline = pd.DataFrame(self.pipeline, columns=columns)
        self.pipeline = self.pipeline.sort_values(by='next_due')
        self.pipeline['next_due'] = self.pipeline['next_due'].apply(
            lambda x: self.decode_date(x))

    def update_pipeline(self, card_id, next_interval, next_due, duration):
        print('dropped', card_id)
        self.pipeline = self.pipeline.drop(
            self.pipeline[self.pipeline['card_id'] == card_id].index)
        instances = self.generate_future_cards(card_id, next_interval,
                                               next_due, duration)
        temp_pipeline = [[]]
        temp_pipeline += instances
        temp_pipeline = [x for x in temp_pipeline if x]
        columns = ['card_id', 'next_interval', 'next_due', 'duration']
        temp_pipeline = pd.DataFrame(temp_pipeline, columns=columns)
        self.pipeline['next_due'] = self.pipeline['next_due'].apply(
            lambda x: self.encode_date(x))
        self.pipeline = pd.concat([self.pipeline, temp_pipeline], axis=0,
                                  ignore_index=True)
        self.pipeline = self.pipeline.sort_values(by='next_due')
        self.pipeline['next_due'] = self.pipeline['next_due'].apply(
            lambda x: self.decode_date(x))

    def allocate_pipeline(self, active_cards):
        for index, row in self.forecast.iterrows():
            date = self.decode_date(row['date'])
            capacity = row['capacity']
            if active_cards:
                remaining = capacity
            else:
                remaining = row['unused']
            while remaining > 0 and self.next_day == False:
                for index2, row2 in self.pipeline.iterrows():
                    date_diff = (date - row2['next_due']).days
                    if date_diff < 0:
                        self.next_day = True
                        break
                    if row2['duration'] <= remaining:
                        row['allocated'] += [
                            [row2['card_id'], row2['duration']]]
                        remaining -= row2['duration']
                        self.pipeline.drop(index2, inplace=True)
                        self.max_blend = max(self.max_blend, date_diff)
                    if date_diff > 0:
                        updated_next_interval = int(
                            (row2['next_interval'] + date_diff) * 1.5 * (
                                    0.8 + 0.4 * rd.random())) + 1
                        updated_next_due = date + datetime.timedelta(
                            days=updated_next_interval)
                        self.update_pipeline(row2['card_id'],
                                             updated_next_interval,
                                             self.encode_date(updated_next_due),
                                             row2['duration'])
                self.next_day = True
            row['allocated'] = [x for x in row['allocated'] if x]
            row['unused'] = remaining
            self.forecast.loc[index, :] = row
            self.next_day = False
            print(date, capacity, remaining, row['allocated'], self.max_blend)
        forecast_end = self.decode_date(self.forecast.max()[0])
        self.pipeline = self.pipeline[self.pipeline.next_due <= forecast_end]
        # print(self.forecast)

    def generate_forecast(self):
        # prepare forecast columns
        self.forecast['allocated'] = [[[]] for _ in range(len(self.forecast))]
        self.forecast['overdue'] = 0
        self.forecast['active'] = 0
        self.forecast['new'] = 0
        self.forecast['unused'] = 0
        # generate active cards pipeline
        self.generate_pipeline(True)
        # allocate current card instances (overdue + active)
        self.allocate_pipeline(True)
        # add in new cards
        self.pipeline = [[]]
        for index, row in self.forecast.iterrows():
            date = self.decode_date(row['date'])
            capacity = row['capacity']
            remaining = capacity
            if remaining == 0:
                continue
            self.new_dur = 8
            instances = self.generate_future_cards(-index - 1, 1,
                                                   self.encode_date(
                                                       date + datetime.timedelta(
                                                           days=1)),
                                                   self.new_dur)
            self.pipeline += instances
            self.generate_pipeline(False)
            print(self.pipeline)
            self.allocate_pipeline(False)
            exit()

        # print(self.pipeline)
        # print(self.forecast)

    # helper functions
    def generate_future_cards(self, card_id, next_interval, next_due, duration):
        next_due = self.decode_date(next_due)
        result = [[]]
        result.append(
            [card_id, next_interval, self.encode_date(next_due), duration])
        i = 0
        while i < 20:
            next_interval = int(
                next_interval * 1.5 * (0.8 + 0.4 * rd.random())) + 1
            next_due += datetime.timedelta(days=next_interval)
            duration *= 1
            result.append(
                [card_id, next_interval, self.encode_date(next_due), duration])
            i += 1
        result = [x for x in result if x]
        return result

    def find_last_record(self, card_id):
        instances = self.history[self.history['card_id'] == card_id]
        if instances.empty:
            return [0, 0]
        else:
            instances = instances.sort_values(by='next_due').tail(1)
            result = instances.loc[:, ['next_interval', 'next_due']]
            result = list(result.itertuples(index=False, name=None))[0]
            return result

    def decode_date(self, string):
        return dt.strptime(string, '%Y-%m-%d').date()

    def encode_date(self, date):
        return dt.strftime(date, '%Y-%m-%d')


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
        self.history.loc[len(self.cards), :] = [dt.today().date(),
                                                int(self.ent_ID.get()), 's']
        # trim dataframes for writing
        cards_to_write = self.cards.loc[:, ['card_id', 'duration']]
        cards_to_write = cards_to_write.astype('int')
        history_to_write = self.history.loc[:,
                           ['date', 'card_id', 'rating', 'next_interval',
                            'next_due']]
        history_to_write['card_id'] = history_to_write['card_id'].astype(int)
        history_to_write['next_interval'] = history_to_write[
            'next_interval'].astype(int)
        # write to files
        with open("cards.csv", "w+", newline='') as file:
            cards_to_write.to_csv(file, encoding='utf-8',
                                  index=False)
        with open("history.csv", "w+", newline='') as file:
            history_to_write.to_csv(file, encoding='utf-8', index=False)
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
