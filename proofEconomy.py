
# I could make it so applying something multiple times decreases the time it takes to produce, to simulate specialization


# todo: humany market weirdness (non-optimal stuff)
# only can buy things they've heard about via word of mouth


# a few options:
#  - everyone potentially sells their inventory at every step
# multiple steps:
# 1. Everyone says how much they'd be willing to pay for every item that is known to exist
# 2. Seller computes difference in price to determine if selling is best action

from collections import defaultdict
import random
import numpy as np


# Learnings:
'''
Having 1/n as discount leads to a few that buy up everything, go broke, and can't do anything because no one is willing to buy (since they value their good more than anyone else)

Also, for those that mine, they just keep mining. Some of them will craft, but eventually everyone that could buy their crafted good goes out of business or would rather make it themselves (because it's cheaper)



'''



def getNames():
    from names_dataset import NameDataset
    names = list(NameDataset().first_names.keys())
    names = list(set([x.encode("ascii", "ignore").decode("ascii", "ignore") for x in names if len(x.encode("ascii", "ignore").decode("ascii", "ignore")) > 0]))
    return names
    
class Statement(object):
    def __init__(self, val, parent1=None, parent2=None):
        self.val = val
        self.parent1 = parent1
        self.parent2 = parent2
        
    def compose(self, other):
        return Statement(self.val + other.val, parent1=self, parent2=other)

    # Loops through this and everything in the ingredient tree needed to make this
    def loopThroughObjectAndComponentParts(self):
        yield self
        if not self.parent1 is None:
            for x in self.parent1.loopThroughObjectAndComponentParts(): yield x
        if not self.parent2 is None:
            for x in self.parent2.loopThroughObjectAndComponentParts(): yield x
    
    def __hash__(self):
        return hash(self.val)
    
    def __eq__(self, other):
        return self.val == other.val
    
    def __repr__(self):
        return "{" + self.val + "}"

MINE = 'mine'
BUY_MARKET = 'buy_market'
SELL_MARKET = 'sell_market'
CRAFT = 'craft'

TYPE_INDEX = 0
DATA_INDEX = 1
VALUE_INDEX = 2
DOER_INDEX = 3

class ProofWorker(object):
    def __init__(self, name):
        self.name = name
        self.producedCounts = defaultdict(int)
        # each item has a random additional value
        self.additionalValues = defaultdict(lambda: random.random())
        self.inventory = defaultdict(int)
        self.coins = 20
     
    def itemsHolding(self):
        totalCount = sum([count for (item, count) in self.inventory.items()])
            
    def getPersonalValuation(self, product):
        # total price it would cost us to make this from scratch
        totalPrice = 0.0
        for componentPart in product.loopThroughObjectAndComponentParts():
            totalPrice += self.costToProduce(componentPart)+self.additionalValues[componentPart]
        
        # additional value we give to this product
        if not product in self.additionalValues:
            self.additionalValues[product] = random.random()*len(product.val)
        totalPrice += self.additionalValues[product]
        
        return totalPrice
        
    def getValuations(self, products):
        return dict([(product, self.getPersonalValuation(product)) for product in products])
        
    # Return all market activities we'd rather do than anything else
    def getMarketPreferences(self, miningSpots, sellPrices, purchasePrices, debug=False):
        preferences = self.getPreferences(miningSpots, sellPrices, purchasePrices, debug=debug)
        firstNonMarketSpot = len(preferences)
        for i, (kind, data, value, unit) in enumerate(preferences):
            if kind != BUY_MARKET and kind != SELL_MARKET:
                firstNonMarketSpot = i
                break
        return preferences[:firstNonMarketSpot]
        
    def getPreferences(self, miningSpots, sellPrices, purchasePrices, debug=False):
        
        preferencesMining = [(MINE, i, self.getPersonalValuation(product)-self.costToProduce(product), self) for (i, product) in enumerate(miningSpots) if self.costToProduce(product) < self.coins]
        
        # The first sell price is the lowest, use that one
        preferencesBuyMarket = [(BUY_MARKET, (product, self.getPersonalValuation(product), sell[0]), self.getPersonalValuation(product)-sell[0][0], self) for (product, sell) in sellPrices.items() \
            if self.getPersonalValuation(product) < self.coins] # can't buy if no coins
        
        preferencesSellMarket = []
        for product, c in self.inventory.items():
            if c > 0 and product in purchasePrices: # this in test is so we can pass in empty dict when we don't care
                buy = purchasePrices[product]
                # the first buy price is the highest, use that one
                preferencesSellMarket.append((SELL_MARKET, (product, self.getPersonalValuation(product), buy[0]), buy[0][0] - self.getPersonalValuation(product), self))
        
        preferencesCrafting = []
        for item1, count1 in self.inventory.items():
            if count1 > 0:
                for item2, count2 in self.inventory.items():
                    if count2 > 0:
                        # if they are both the same item, we need at least two
                        if item1 == item2 and count1 < 2: continue
                        resItem = item1.compose(item2)
                        # can't afford to craft
                        if self.costToProduce(resItem) > self.coins: continue
                        lostValue = self.getPersonalValuation(item1) + \
                                        self.getPersonalValuation(item2) + \
                                        self.costToProduce(resItem)
                        newValue = self.getPersonalValuation(resItem)
                        netValue = newValue - lostValue
                        preferencesCrafting.append((CRAFT, (item1, item2, resItem), netValue, self))
                
        allPreferences = preferencesMining + preferencesBuyMarket + preferencesSellMarket + preferencesCrafting
        allPreferences.sort(key=lambda x: -x[VALUE_INDEX])
        if debug:
            print("agent", self, "preferences")
            for pref in allPreferences:
                print(pref)
        return allPreferences
        
    # Things cost less the longer you work on them
    def costToProduce(self, product):
        return 1.0/(1.0+np.log(1.0+float(self.producedCounts[product])))
        
        
    def __repr__(self):
        return self.name
            
class ProofEconomy(object):
    def __init__(self, names, nWorkers, initialObjects, maxMined):
        random.seed(27)
        np.random.seed(27)
        unitNames = np.random.choice(names, nWorkers, replace=False)
        self.units = [ProofWorker(unitNames[i]) for i in range(nWorkers)]
        self.miningSpots = initialObjects
        self.maxMined = maxMined
        self.prevMinePr = dict([(product, 1.0) for product in initialObjects])
        self.minePrMomentum = 0.4
        
    def step(self, debug=False):
        
        
        unitsNotDoneAnythingYet = [unit for unit in self.units]
        
        # We start by resolving the market
        # The market happens in rounds:
        # find the seller and buyer that want to do selling/buying the most
        # pair them up, and remove them from the list of people
        # (pairing can be a "buyers market" (favor favorite buyer first), a "sellers market" (favor favorite seller first), or other things)
        # repeat until everyone left would rather do other things than participate in market
        t = 0
        while len(unitsNotDoneAnythingYet) >= 2: # need at least two units to do a transaction
            if debug: print("running iter", t, " of market with ", len(unitsNotDoneAnythingYet), " units remaining")
            t += 1
            # Get all held items with count > 0
            knownItems = set()
            for unit in unitsNotDoneAnythingYet:
                knownItems = knownItems | set([x for (x,c) in unit.inventory.items() if c > 0])
                
                
            # Get all sell prices for every held item
            sellPrices = defaultdict(list)
            for unit in unitsNotDoneAnythingYet:
                for product,c in unit.inventory.items():
                    if c > 0:
                        # they won't sell it for less than they think it's worth
                        sellPrice = unit.getPersonalValuation(product)
                        sellPrices[product].append((sellPrice, unit))
            # Sort sell prices so we can see lowest sell price first
            for unit, prices in sellPrices.items():
                prices.sort(key=lambda x: x[0])
            
            # Get all purchase prices for every held item
            purchasePrices = defaultdict(list)
            for unit in unitsNotDoneAnythingYet:
                for product, purchasePrice in unit.getValuations(knownItems).items():
                    purchasePrices[product].append((purchasePrice, unit))
            # sort purchase prices so we see highest purchase price first
            for unit, prices in purchasePrices.items():
                prices.sort(key=lambda x: -x[0])
            
            # Get market preferences for each agent
            # Note, this ignores any market preferences that are lower than taking other non-market actions
            agentPreferences = []
            for unit in unitsNotDoneAnythingYet:
                agentPreferences += unit.getMarketPreferences(self.miningSpots, sellPrices, purchasePrices, debug=debug)
            
            if len(agentPreferences) == 0:
                if debug: print("no one prefers being in market")
                break
            
            if debug:
                print("unsorted preferences")
                for pref in agentPreferences:
                    print(pref)
            
            agentPreferences.sort(key=lambda x: -x[VALUE_INDEX])
            
            if debug:
                print("sorted preferences")
                for pref in agentPreferences:
                    print(pref)
            
            # go down list, looking for first matchup
            desiredSell = defaultdict(list)
            desiredBuy = defaultdict(list)
            matchedBuyer = None
            matchedBuyPrice = None
            matchedSeller = None
            matchedSellPrice = None
            matchedProduct = None
            for (kind, (product, myPrice, (theirPrice, otherUnit)), value, unit) in agentPreferences:
                if kind == BUY_MARKET:
                    if product in desiredSell:
                        for seller, sellPrice in desiredSell[product]:
                            if seller == unit: continue # don't buy from self
                            matchedProduct = product
                            matchedBuyer = unit
                            matchedBuyPrice = myPrice
                            matchedSeller, matchedSellPrice = seller, sellPrice
                            break
                        if not matchedProduct is None: break
                    desiredBuy[product].append((unit, myPrice))
                elif kind == SELL_MARKET:
                    if product in desiredBuy:
                        for buyer, buyPrice in desiredBuy[product]:
                            if buyer == unit: continue # don't sell to self
                            matchedProduct = product
                            matchedBuyer, matchedBuyPrice = buyer, buyPrice
                            matchedSeller = unit
                            matchedSellPrice = myPrice
                            break
                        if not matchedProduct is None: break
                    desiredSell[product].append((unit, myPrice))
            
            
            if matchedBuyer is None:
                if debug: print("failed to find match")
                break
            
            print("found match: buyer", matchedBuyer, " at price ", matchedBuyPrice, " seller ", matchedSeller, " at price ", matchedSellPrice, " for product ", matchedProduct)
            # do transaction
            matchedBuyer.coins -= matchedBuyPrice
            matchedSeller.coins += matchedBuyPrice
            matchedBuyer.inventory[matchedProduct] += 1
            matchedSeller.inventory[matchedProduct] -= 1
            unitsNotDoneAnythingYet.remove(matchedBuyer)
            unitsNotDoneAnythingYet.remove(matchedSeller)
        
        spentCoins = 0.0
        # now that we've matched the market, everyone else just wants to do non-market stuff
        miners = defaultdict(list)
        for unit in unitsNotDoneAnythingYet:
            prefs = unit.getPreferences(self.miningSpots, {}, {})
            if debug:
                print("unit", unit, "preferences")
                for p in prefs: print(p)
            if len(prefs) == 0: continue # can't do anything, too poor
            chosenAction = prefs[0]
            if debug: print("doing", unit, chosenAction)
            (kind, data, value, unit) = chosenAction
            if kind == MINE:
                miners[data].append(unit)
            elif kind == CRAFT:
                (item1, item2, outItem) = data
                if debug: print("crafting")
                unit.inventory[item1] -= 1
                unit.inventory[item2] -= 1
                unit.coins -= unit.costToProduce(outItem)
                spentCoins += unit.costToProduce(outItem)
                unit.producedCounts[outItem] += 1
                unit.inventory[outItem] += 1
        
        self.prevMinePr = {}
        for i, product in enumerate(self.miningSpots):
            numMiners = len(miners[product])
            chanceOfGetting = float(self.maxMined[i])/max(numMiners, self.maxMined[i], 1)
            self.prevMinePr[product] = chanceOfGetting
            
        
        
        for i, unitsMining in miners.items():
            if debug: print("these units wanted to mine", self.miningSpots[i], unitsMining)
            itemsGot = min(self.maxMined[i], len(unitsMining))
            # sample without replacement so each unit mines a maximum of one time 
            unitsGot = np.random.choice(unitsMining, itemsGot, replace=False)
            product = self.miningSpots[i]
            for unitMined in unitsGot:
                costToMine = unitMined.costToProduce(product)
                if debug: print("unit", unitMined, "mined", product, "at cost", costToMine)
                unitMined.coins -= costToMine
                spentCoins += costToMine
                unitMined.inventory[product] += 1
                unitMined.producedCounts[product] += 1
        
        for unit in self.units:
            unit.coins += spentCoins/len(self.units)
        
        
        if debug:
            for unit in self.units:
                print( unit.inventory, unit, unit.coins)