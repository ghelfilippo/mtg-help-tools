import numpy as np
import re
import random, json
from collections import Counter
import matplotlib.pyplot as plt
import pandas as pd
import time
##################################### CALCULATOR

def neededLands(avg_mana_value, ramp_number):
    '''Formula per calcolare le terre necessarie considerando il costo di mana medio e
    il numero di ramp economici (valore di mana 3 o minore)'''
    print('Suggested lands are', round(31.42 + 3.13*avg_mana_value - 0.28*ramp_number, 1))

def sampleAndRemove(deck, num):
    cards = random.sample(deck, num)
    for card in cards:
        deck.remove(card)
    return cards, deck

def createDeck(lands, ramp):
    decks = []
    for i in range(lands):
        decks.append('land' + str(i))
    for r in ramp:
        for q in range(r['quantity']):
            r['id'] = str(q)
            
            decks.append(r)
    for i in range(99 - len(decks)):
        decks.append('other' + str(i))
    return decks

def getLand(hands):
    return  [h for h in hands if isinstance(h, str) and  h.startswith('land')]

def getRamp(hands, mana_value):
    ramps = [h for h in hands if isinstance(h, dict) and  h['mv'] <= mana_value ]
    sorted_ramps = sorted(ramps, key=lambda x: x['ramp'], reverse=True)
    return sorted_ramps

def getPlot(dati):
    frequenze = dict(sorted(Counter(dati).items()))
    totale_elementi = sum(frequenze.values())
    # Calcola le percentuali
    percentuali = {k: (v / totale_elementi) * 100 for k, v in frequenze.items()}
    # Prepara i dati per il plotting
    labels, values = zip(*percentuali.items())
    # Calcola le percentuali cumulative
    percentuali_cumulative = np.cumsum(values)
    
    # Crea l'istogramma
    fig, ax1 = plt.subplots(figsize=(10,6))
    
    color = 'tab:blue'
    ax1.bar(labels, values, width=0.5, align='center', color=color)
    ax1.set_xlabel('Turno')
    ax1.set_ylabel('Percentuale (%)', color=color)
    ax1.tick_params(axis='y', labelcolor=color)
    
    # Aggiungi i valori delle percentuali sopra le barre
    for i, v in enumerate(values):
        ax1.text(labels[i], v + 0.5, f"{v:.2f}%", ha='center', color=color)
    
    # Crea un secondo asse per la percentuale cumulata
    ax2 = ax1.twinx()
    
    color = 'tab:red'
    ax2.plot(labels, percentuali_cumulative, color=color, marker='o', linestyle='-', linewidth=2, label='Cumulativo (%)')
    ax2.set_ylabel('Cumulativo (%)', color=color)
    ax2.tick_params(axis='y', labelcolor=color)
    
    # Aggiungi i valori delle percentuali cumulative
    for i, v in enumerate(percentuali_cumulative):
        ax2.text(labels[i], v, f"{v:.2f}%", ha='center', color=color)
    
    # Aggiungi una legenda
    fig.tight_layout()
    plt.title('Probabilità di raggiungere il target al turno n-esimo')
    plt.show()
    return percentuali_cumulative, labels

def runMatch(target, lands, ramp, min_ramp, min_land, max_mulligans):
    deck = createDeck(lands, ramp)
    mana_value = 0
    reached_target = False
    turn = 0

    ### mano iniziale
    hands, deck = sampleAndRemove(deck, 7)
    avg_lands_in_init_hand = len(getLand(hands))
    ramp_in_init_hand = len(getRamp(hands, 3))

    hand_is_ok = False

    remove = 0
    
    while(hand_is_ok == False):
        
        if (avg_lands_in_init_hand < min_land or ramp_in_init_hand < min_ramp) and  remove < max_mulligans:
            ### mulligan
            deck = createDeck(lands, ramp)
            hands, deck = sampleAndRemove(deck, 7 - remove)
            avg_lands_in_init_hand = len(getLand(hands))
            ramp_in_init_hand = len(getRamp(hands, 3))
            remove += 1
        else:
            hand_is_ok = True
        

    while(reached_target == False):
        #### numero di turno
        turn += 1
        ### pesca
        draw, deck = sampleAndRemove(deck, 1)
        hands += draw

        ### gioca terra se c'è
        land_in_hands = getLand(hands)
        if len(land_in_hands) > 0:
            hands.remove(land_in_hands[0])
            mana_value += 1

        if mana_value >= target:
            return turn, avg_lands_in_init_hand

        ### gioca ramp se c'è
        getAvailableRamp = getRamp(hands, mana_value)
        if len(getAvailableRamp):
            used_ramp = getAvailableRamp[0]
            hands.remove(used_ramp)
            mana_value += used_ramp['ramp']

def calculateDropPerTurn(target , lands , ramp ,  min_ramp = 1, min_land = 3, max_mulligans = 2, simulation = 1000):
    results = {'lands_init_hand' : [], 'turn_reached' : []}
    for s in range(simulation):
        turn, land_init = runMatch(target, lands, ramp, min_ramp, min_land, max_mulligans)
        results['lands_init_hand'].append(land_init)
        results['turn_reached'].append(turn)
    turns = results['turn_reached']
    perc_cumulative, labels = getPlot(turns)
    df = pd.DataFrame({'turno' : labels, 'percentuale cumulativa di successo' : perc_cumulative})
    return df


################## API

import requests

def getCardInfo(card_name):
    url = "https://api.scryfall.com/cards/named"
    query = {"exact": card_name}
    response = requests.get(url, params=query)
    if response.status_code == 200:
        return response.json()
    else:
        return f"Errore durante la ricerca della carta: HTTP {response.status_code}"
    
def parseRow(card):
    '''ottiene quantità, nome e carta'''
    quantity = int(card.split('x')[0])
    match = re.search(r"x (.*?) \(", card)
    name  = match.group(1)
    if '[' in card:
        category = card.split('[')[1].split(']')[0]
    else:
        category = 'Land'
    
    card_info = getCardInfo(name)
    if 'mana_cost' not in card_info.keys():
        if 'card_faces' in card_info.keys():
            mv = card_info['card_faces'][0]['mana_cost']
    else:
        mv = card_info['mana_cost']
        time.sleep(0.01)
    
    if category == 'Land':
        produced_mana = card_info['produced_mana']
    else:
        produced_mana = ''


    return quantity, name, category, mv, produced_mana



def initializeDeckList(path_input = 'deck/list.txt', path_output = 'deck/parsed.json'):


    with open('lib/known_cards.json') as rf:
        known_cards = json.load(rf)

    parsed = {}

    with open(path_input, 'r') as file:
        for card in file:
            quantity, name, category, mv , produced_mana = parseRow(card)
            if category not in parsed.keys():
                parsed[category] = []

            p = {'name' : name, 'quantity' : quantity, 'mv' : mv}

            if category == 'Land':
                p['produced_mana'] = produced_mana
            
            if category == 'Ramp':
                known_ramps = [f['name'] for f in known_cards['Ramp']]
                if name in known_ramps:
                    target = [f for f in known_cards['Ramp'] if f['name'] == name][0]
                    p['ramp'] = target['ramp']
                    p['tapped'] = target['tapped']
            
            parsed[category].append(p)

    with open(path_output, 'w') as wf:
        json.dump(parsed, wf, indent=4)