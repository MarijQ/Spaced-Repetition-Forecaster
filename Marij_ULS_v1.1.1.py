from copy import deepcopy


class SystemState():
    def __init__(self):
        self.forecast = [[]]
        self.maxPerDay = 2
        self.maxBlendDays = 1
        self.numCards = 0
        self.lastForecastDate = 0
        self.cardRejected = 0

    def addCard(self, date):
        newCard = Card(self.numCards + 1, date)
        deferral = 0
        while len(self.forecast[date + deferral]) >= self.maxPerDay:
            deferral += 1
        if date + deferral > self.lastForecastDate:
            return
        self.forecast[date + deferral].append(newCard)
        self.numCards += 1
        return newCard

    def removeFullCard(self, targetID, date=0):
        self.forecast = [[card for card in day if card.cardID != targetID or
                          card.studyDate <= date] for day in self.forecast]
        self.numCards -= sum(1 for day in self.forecast for card in day if
                             card.cardID == targetID)

    def addDay(self):
        self.forecast.append([])

    def promoteCardFull(self, card):
        activeCard = card
        nextDate = card.studyDate + int(activeCard.nextInterval)
        while nextDate <= self.lastForecastDate:
            deferral = 0
            while len(self.forecast[nextDate + deferral]) >= self.maxPerDay:
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
                print(f"Card {card.cardID} rejected with deferral {deferral}")
                self.cardRejected = 1
                return

    def submitCard(self, day):
        newCard = self.addCard(day)
        self.promoteCardFull(newCard)

    def printArray(self):
        data = [[(card.cardID, int(card.nextInterval), card.deferral) \
                 for card in day] for day in self.forecast]
        latestCard = 0
        for day in range(len(data)):
            if len(data[day]) == 0:
                cardsAdded = -1
            else:
                cardsAdded = max(x[0] for x in data[day]) - latestCard
                latestCard = max(latestCard, max(x[0] for x in data[day]))
            if cardsAdded <= 0:
                cardsAdded = ""
            else:
                cardsAdded = "\t added " + str(cardsAdded)
            print(day, data[day], cardsAdded)


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
forecastDays = 10
for i in range(forecastDays - 1):
    s.addDay()
s.lastForecastDate = len(s.forecast) - 1
# while day < forecastDays:
#     while s.cardRejected == 0:
#         s.submitCard(day)
#     s.cardRejected = 0
#     day += 1
s.submitCard(0)
s.submitCard(0)
s.submitCard(0)
s.printArray()
