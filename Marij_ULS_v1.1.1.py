from copy import deepcopy


class SystemState():
    def __init__(self):
        self.forecast = [[]]
        self.maxPerDay = 2
        self.maxBlendDays = 1
        self.numCards = 0

    def addCard(self, date):
        while len(self.forecast) < date + 1:
            self.addDay()
        newCard = Card(self.numCards + 1, date)
        self.numCards += 1
        self.forecast[date].append(newCard)
        futureDeferrals = [card.deferral for day in self.forecast for card in day if
                           card.studyDay >= date]
        if max(futureDeferrals) > self.maxBlendDays:
            self.removeFullCard(newCard.cardID)
            self.numCards -= 1
            print("card removed")

    def removeFullCard(self, cardID):
        self.forecast = [[x for x in day if x.cardID != cardID] for day in self.forecast]

    def addDay(self):
        self.forecast.append([])

    def promoteCards(self, day):
        for card in self.forecast[day]:
            nextDate = day + int(card.nextInterval)
            deferral = 0
            while len(self.forecast) >= nextDate + deferral + 1 and len(
                    self.forecast[nextDate + deferral]) >= self.maxPerDay:
                deferral += 1
            if len(self.forecast) >= nextDate + deferral + 1:
                newCard = deepcopy(card)
                newCard.nextInterval *= newCard.multiplier
                newCard.deferral = deferral
                self.forecast[nextDate + deferral].append(newCard)

    def printArray(self):
        data = [[(card.cardID, int(card.nextInterval), card.deferral) for card in day] for
                day
                in self.forecast]
        latestCard = 0
        for day in range(len(data)):
            cardsAdded = max(x[0] for x in data[day]) - latestCard
            latestCard = max(latestCard, max(x[0] for x in data[day]))
            if cardsAdded <= 0:
                cardsAdded = ""
            else:
                cardsAdded = "\t added " + str(cardsAdded)
            print(day, data[day], cardsAdded)
            if max(x[2] for x in data[day]) > self.maxBlendDays:
                print(max(x[2] for x in data[day]))


class Card():
    def __init__(self, cardID, studyday):
        self.multiplier = 2.5
        self.studyTime = 1
        self.cardID = cardID
        self.nextInterval = 1
        self.deferral = 0
        self.studyDay = studyday


s = SystemState()
day = 0
forecastDays = 30
for i in range(forecastDays - 1):
    s.addDay()
while day < forecastDays:
    if len(s.forecast[day]) < s.maxPerDay:
        s.addCard(day)
    s.promoteCards(day)
    day += 1
s.printArray()
