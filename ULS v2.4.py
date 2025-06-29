## Next ideas
# comment code
# reducing duration (overwrite cards database with latest review)
# max blend allowed based on % overdue e.g. 50%
# automatically refresh forecast + study labels on button presses
# study visuals - buttons + explanatory text for each difficulty level
# info page - front page with explanations (improve overdue score / increase capacity / increase interval rating scores)
# settings page - generation horizon / max blend allowed / rating scores / forecast assumed rating score
# large card spillover to next days (maybe? not sure if good to allow this)
# performance improvements

## Long term ideas
# Chart for historical performance
# Reducing duration curves applied to forecast
# Port to web


import datetime
import random as rd
import tkinter as tk
from datetime import datetime as dt
from tkinter import ttk

import matplotlib

matplotlib.use('TkAgg')

import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
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
    new_dur = 0
    max_blend = 0
    max_blend_allowed = 7
    NEW_CARD_GENERATION_HORIZON = 30

    def reforecast(self):
        self.read_files()
        self.update_cards()
        self.generate_forecast()

    def decode_series_date(self, date):
        return self.decode_date(date)

    def read_files(self):
        self.forecast = pd.read_csv('forecast.csv')
        self.cards = pd.read_csv('cards.csv')
        self.history = pd.read_csv('history.csv')

        # trim and extrapolate forecast
        self.forecast['date'] = self.forecast['date'].apply(
            lambda x: self.decode_date(x))
        self.forecast = self.forecast[
            self.forecast['date'] >= dt.today().date()]
        average_capacity = int(self.forecast['capacity'].mean()) + 1
        last_date = self.forecast['date'].max()
        extrapolated = pd.DataFrame({"date": pd.date_range(
            self.encode_date(last_date + datetime.timedelta(days=1)),
            dt.today().date() + datetime.timedelta(days=1000),
            freq='D')})
        extrapolated['capacity'] = average_capacity
        extrapolated['date'] = extrapolated['date'].apply(lambda x: x.date())
        self.forecast = pd.concat([self.forecast, extrapolated]).reset_index(
            drop=True)
        self.forecast['date'] = self.forecast['date'].apply(
            lambda x: self.encode_date(x))

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
            self.pipeline = [[]]
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
        self.pipeline.reset_index(drop=True, inplace=True)

    def update_pipeline(self, card_id, next_interval, next_due, duration):
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
        self.pipeline.reset_index(drop=True, inplace=True)

    def allocate_pipeline(self, active_cards):
        # loop through forecast days
        for index, row in self.forecast.iterrows():
            date = self.decode_date(row['date'])
            capacity = row['capacity']
            if active_cards:
                remaining = capacity
            else:
                remaining = row['unused']
            # keep trying to allocate cards until capacity is used up
            index2 = 0
            row2 = self.pipeline.loc[index2]
            date_diff = (date - row2['next_due']).days
            while remaining > 0 and date_diff >= 0:
                if row2['duration'] <= remaining:
                    # update totals
                    if active_cards:
                        if row2['next_due'] < dt.today().date():
                            row['overdue'] += row2['duration']
                        else:
                            row['active'] += row2['duration']
                    # allocate card
                    row['allocated'] += [
                        [row2['card_id'], row2['duration'], date_diff]]
                    remaining -= row2['duration']
                    if not active_cards:
                        row['new'] += row2['duration']
                    self.pipeline.drop(self.pipeline.head(1).index[0],
                                       inplace=True)
                    self.max_blend = max(self.max_blend, date_diff)
                    self.pipeline.reset_index(drop=True, inplace=True)
                    # update pipeline for all instances of card if late
                    if date_diff > 0:
                        updated_next_interval = int(
                            (row2['next_interval']) * 1.5 * (
                                    0.8 + 0.4 * rd.random())) + 1
                        updated_next_due = date + datetime.timedelta(
                            days=updated_next_interval)
                        self.update_pipeline(row2['card_id'],
                                             updated_next_interval,
                                             self.encode_date(updated_next_due),
                                             row2['duration'])
                else:
                    index2 += 1
                # next card
                if self.pipeline.empty or len(self.pipeline.index) < index2 + 1:
                    break
                else:
                    row2 = self.pipeline.loc[index2]
                    date_diff = (date - row2['next_due']).days
            # clean up forecast day row
            row['allocated'] = [x for x in row['allocated'] if x]
            row['unused'] = remaining
            self.forecast.loc[index, :] = row
            self.next_day = False
            # print(date, remaining, row['allocated'], self.max_blend)
        forecast_end = self.decode_date(self.forecast.max()[0])
        self.pipeline = self.pipeline[self.pipeline.next_due <= forecast_end]

    def generate_forecast(self):
        # prepare forecast columns
        self.forecast['allocated'] = [[[]] for _ in range(len(self.forecast))]
        self.forecast['overdue'] = 0
        self.forecast['active'] = 0
        self.forecast['brand_new'] = 0
        self.forecast['new'] = 0
        self.forecast['unused'] = 0
        # overdue + active
        self.generate_pipeline(True)
        self.allocate_pipeline(True)
        # new
        for index in range(self.NEW_CARD_GENERATION_HORIZON):
            date = self.decode_date(self.forecast.loc[index, 'date'])
            remaining = self.forecast.loc[index, 'unused']
            self.new_dur = 1
            self.max_blend = 0
            if remaining == 0:
                print(self.forecast.loc[index, 'date'],
                      [-index - 1, self.new_dur - 1], self.max_blend)
                continue
            kill_switch = False
            while True:
                print('try', [-index - 1, self.new_dur])
                self.max_blend = 0
                self.pipeline = [[]]
                self.delete_allocations(-index - 1)
                self.forecast.at[index, 'brand_new'] = min(0, self.forecast.at[
                    index, 'brand_new'] + self.new_dur)
                instances = self.generate_future_cards(-index - 1, 1,
                                                       self.encode_date(
                                                           date + datetime.timedelta(
                                                               days=1)),
                                                       self.new_dur)
                self.pipeline += instances
                self.generate_pipeline(False)
                self.allocate_pipeline(False)
                self.forecast.at[index, 'allocated'] += [
                    [-index - 1, self.new_dur, 0]]
                self.forecast.at[index, 'brand_new'] += self.new_dur
                if kill_switch:
                    break
                if self.max_blend <= self.max_blend_allowed:
                    if remaining >= self.new_dur + 1:
                        self.new_dur += 1
                        continue
                    else:
                        break
                elif self.new_dur > 1:
                    self.new_dur -= 1
                    kill_switch = True
                    continue
                else:
                    self.delete_allocations(-index - 1)
                    self.forecast.at[index, 'brand_new'] -= self.new_dur
                    break
            print(self.forecast.loc[index, 'date'], [-index - 1, self.new_dur],
                  self.max_blend)
        self.forecast['unused'] = self.forecast.apply(
            lambda x: x['capacity'] - x['overdue'] - x['active'] - x[
                'brand_new'] - x['new'], axis=1)
        print(self.forecast)

    def clean_allocated_list(self, allocated, card_id):
        return [x for x in allocated if x[0] != card_id]

    def calculate_new(self, allocated):
        return sum([x[1] for x in allocated if x[0] < 0])

    def delete_allocations(self, card_id):
        self.forecast['allocated'] = self.forecast.apply(
            lambda x: self.clean_allocated_list(x['allocated'], card_id),
            axis=1)
        self.forecast['new'] = self.forecast.apply(
            lambda x: self.calculate_new(x['allocated']), axis=1)
        self.forecast['new'] = self.forecast.apply(
            lambda x: x['new'] - x['brand_new'], axis=1)
        self.forecast['unused'] = self.forecast.apply(
            lambda x: x['capacity'] - x['overdue'] - x['active'] - x[
                'brand_new'] - x['new'], axis=1)

    # helper functions
    def generate_future_cards(self, card_id, next_interval, next_due,
                              duration):
        next_due = self.decode_date(next_due)
        result = [[]]
        result.append(
            [card_id, next_interval, self.encode_date(next_due), duration])
        i = 0
        while i < 27:
            next_interval = min(1500, int(
                next_interval * 1.5 * (0.8 + 0.4 * rd.random())) + 1)
            next_due += datetime.timedelta(days=next_interval)
            duration *= 1
            result.append(
                [card_id, next_interval, self.encode_date(next_due),
                 duration])
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
        # tkinter settings
        s = ttk.Style()
        self.font = ('Segoe UI', 24)
        s.configure('.', font=self.font)

        # Set up tabs
        tabControl = ttk.Notebook(window)
        self.set_up_tabs(tabControl)
        Engine.__init__(self)
        self.input_visuals(self.tab_input)
        self.forecast_visuals(self.tab_forecast)
        self.study_visuals(self.tab_study)

        # self.ent_duration.insert(0, 1)
        # self.submit_card()
        # self.ent_studyID.insert(0, 2)
        # self.ent_rating.insert(0, 'f')
        # self.submit_review()
        pass

    def nextline(self, r):
        r += 1
        c = 0
        return r, c

    def submit_card(self):
        # append new card to 'cards'+'history' dataframes
        next_interval = 1
        next_due = dt.today().date() + datetime.timedelta(days=next_interval)
        new_row = pd.DataFrame([[int(self.ent_ID.get()),
                                 int(self.ent_duration.get()),
                                 next_interval,
                                 self.encode_date(next_due)]],
                               columns=self.cards.columns)
        self.cards = pd.concat([self.cards, new_row]).reset_index(drop=True)
        new_row = pd.DataFrame([[dt.today().date(),
                                 int(self.ent_ID.get()), 's',
                                 next_interval,
                                 self.encode_date(next_due)]],
                               columns=self.history.columns)
        self.history = pd.concat([self.history, new_row]).reset_index(drop=True)
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
        # reforecast
        # self.reforecast()
        # self.forecast_visuals()

    def submit_review(self):
        card_id = int(self.ent_studyID.get())
        rating = self.ent_rating.get()
        prev_date = self.decode_date(
            self.find_last_record(card_id)[1]) - datetime.timedelta(
            days=self.find_last_record(card_id)[0])
        last_interval = (dt.today().date() - prev_date).days
        next_interval = min(1500,
                            int(last_interval * self.decode_rating(rating) * (
                                    0.8 + 0.4 * rd.random())) + 1)
        next_due = dt.today().date() + datetime.timedelta(days=next_interval)
        new_row = pd.DataFrame([[dt.today().date(),
                                 card_id,
                                 self.ent_rating.get(),
                                 next_interval,
                                 self.encode_date(next_due)]],
                               columns=self.history.columns)
        self.history = pd.concat([self.history, new_row]).reset_index(drop=True)
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
        self.ent_studyID.delete(0, 'end')
        self.ent_rating.delete(0, 'end')
        self.lab_review_info.config(
            text=f'You will see card {card_id} again in {next_interval} days on {self.encode_date(next_due)}')

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
        x = self.forecast.loc[0:30, 'date']
        y1 = self.forecast.loc[0:30, 'overdue']
        y2 = self.forecast.loc[0:30, 'active']
        y3 = self.forecast.loc[0:30, 'brand_new']
        y4 = self.forecast.loc[0:30, 'new']
        y5 = self.forecast.loc[0:30, 'unused']
        self.subplot.bar(x, y1, label='Overdue', color='r',
                         tick_label=[s[-2:] for s in x])
        self.subplot.bar(x, y2, label='Active', bottom=y1, color='m')
        self.subplot.bar(x, y3, label='Brand New', bottom=y1 + y2, color='b')
        self.subplot.bar(x, y4, label='New', bottom=y1 + y2 + y3, color='g')
        self.subplot.bar(x, y5, label='Unused', bottom=y1 + y2 + y3 + y4,
                         color='k')
        self.subplot.legend()
        self.subplot.set_xlabel('date')
        self.subplot.set_ylabel('minutes')
        # pack widgets
        self.img_plot = FigureCanvasTkAgg(fig, master=frame)
        self.img_plot.draw()
        self.img_plot.get_tk_widget().grid(row=0, column=0)

    def study_visuals(self, frame):
        # calculate instructions
        today_row = self.forecast.loc[0]
        date = today_row['date']
        allocation = today_row['allocated']
        today_new = today_row['brand_new']
        instructions = (str(date) + '\n' + str(allocation)
                        + '\n' + 'key: [card_id, duration, days overdue]'
                        + '\n' + f'You can then add {today_new} minutes of new cards today'
                        + '\n' + 'Rating key: f (100%), m (80%), h (50%), l (<50%)')
        # create widgets
        self.lab_instructions = ttk.Label(frame, text=instructions)
        self.lab_studyID = ttk.Label(frame, text="ID")
        self.ent_studyID = ttk.Entry(frame, font=self.font, width=7)
        self.lab_rating = ttk.Label(frame, text="Rating")
        self.ent_rating = ttk.Entry(frame, font=self.font, width=7)
        self.but_study_submit = ttk.Button(frame, text='Submit',
                                           command=self.submit_review)
        self.lab_review_info = ttk.Label(frame, text="")

        # pack widgets
        r = c = 0
        self.lab_instructions.grid(row=r, column=c, columnspan=5, padx=10,
                                   pady=10)
        r += 1
        self.lab_studyID.grid(row=r, column=c)
        c += 1
        self.ent_studyID.grid(row=r, column=c)
        c += 1
        self.lab_rating.grid(row=r, column=c, padx=10, pady=10)
        c += 1
        self.ent_rating.grid(row=r, column=c)
        c += 1
        self.but_study_submit.grid(row=r, column=c)
        (r, c) = self.nextline(r)
        self.lab_review_info.grid(row=r, column=c, columnspan=5)

    def decode_rating(self, rating):
        match rating:
            case 'f':
                return 2.0
            case 'm':
                return 1.5
            case 'h':
                return 1.0
            case 'l':
                return 0.5


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Ultimate Learning System v2")
    GUI(root)
    root.mainloop()
