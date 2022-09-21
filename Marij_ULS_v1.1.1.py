import random as rd
from copy import deepcopy


class SystemState():
    def __init__(self):
        self.forecast = [[]]
        self.maxPerDay = 3
        self.maxBlendDays = 7
        self.numCards = 0
        self.lastForecastDate = 0
        self.cardRejected = 0
        self.perfData = [[]]

    def addCard(self, date):
        deferral = 0
        # while date + deferral <= self.lastForecastDate and len(
        #         self.forecast[date + deferral]) >= self.maxPerDay:
        #     deferral += 1
        # if date + deferral > self.lastForecastDate:
        #     return
        if len(self.forecast[date]) < self.maxPerDay:
            newCard = Card(self.numCards + 1, date)
            self.forecast[date].append(newCard)
            self.numCards += 1
            return newCard
        else:
            return

    def removeFullCard(self, targetID, date=0):
        self.forecast = [[card for card in day if card.cardID != targetID or
                          card.studyDate < date] for day in self.forecast]
        self.numCards -= sum(1 for day in self.forecast for card in day if
                             card.cardID == targetID)

    def addDay(self):
        self.forecast.append([])

    def promoteCardFull(self, card):
        activeCard = card
        nextDate = activeCard.studyDate + int(activeCard.nextInterval)
        while nextDate <= self.lastForecastDate:
            deferral = 0
            while len(self.forecast[
                          nextDate + deferral]) >= self.maxPerDay:
                deferral += 1
            if deferral <= self.maxBlendDays:
                if nextDate + deferral + 1 > self.lastForecastDate:
                    return
                newCard = deepcopy(activeCard)
                newCard.nextInterval *= newCard.multiplier
                newCard.deferral = deferral
                newCard.studyDate = nextDate + deferral
                self.forecast[nextDate + deferral].append(newCard)
                activeCard = newCard
                nextDate = activeCard.studyDate + int(activeCard.nextInterval)
            else:
                self.removeFullCard(card.cardID, date=card.studyDate)
                print(
                    f"Card {card.cardID} on date {activeCard.studyDate} rejected with deferral {deferral}")
                self.cardRejected = 1
                return

    def submitCard(self, day):
        newCard = self.addCard(day)
        if newCard is not None:
            self.promoteCardFull(newCard)
            s.updatePerfData()
        else:
            self.cardRejected = 1

    def updatePerfData(self):
        self.perfData = [[(card.cardID, card.deferral) \
                          for card in day] for day in self.forecast]

    def printArray(self):
        latestCard = 0
        for day in range(len(self.perfData)):
            if len(self.perfData[day]) == 0:
                cardsAdded = -1
            else:
                cardsAdded = max(x[0] for x in self.perfData[day]) - latestCard
                latestCard = max(latestCard,
                                 max(x[0] for x in self.perfData[day]))
            if cardsAdded <= 0:
                cardsAdded = ""
            else:
                cardsAdded = "\t added " + str(cardsAdded)
            print(day, self.perfData[day], cardsAdded)


class Card():
    def __init__(self, cardID, studyDate):
        self.multiplier = 2.5
        self.studyTime = 1
        self.cardID = cardID
        self.nextInterval = 1
        self.deferral = 0
        self.studyDate = studyDate


s = SystemState()
day = 0
forecastDays = 100
for i in range(forecastDays - 1):
    s.addDay()
s.lastForecastDate = len(s.forecast) - 1
while day < forecastDays:
    while s.cardRejected == 0 and rd.random() <= 1:
        s.submitCard(day)
    s.cardRejected = 0
    day += 1
s.printArray()
