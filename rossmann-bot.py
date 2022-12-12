import pandas as pd
import json
import requests
from flask import Flask, request, Response

# CONSTANTS
TOKEN = '5824921864:AAFFW8yuir8632tnbntFqnXXvhIvsmYVNbQ'



# # Info about the bot
# 'https://api.telegram.org/bot5824921864:AAFFW8yuir8632tnbntFqnXXvhIvsmYVNbQ/getMe'

# # Get updates
# 'https://api.telegram.org/bot5824921864:AAFFW8yuir8632tnbntFqnXXvhIvsmYVNbQ/getUpdates'

# # Webhoot
# 'https://api.telegram.org/bot5824921864:AAFFW8yuir8632tnbntFqnXXvhIvsmYVNbQ/setWebhook?url='

# # Send Message
# 'https://api.telegram.org/bot5824921864:AAFFW8yuir8632tnbntFqnXXvhIvsmYVNbQ/sendMessage?chat_id=918273580&text=Hello, how is going?'

def send_message(chat_id, text):
    url = 'https://api.telegram.org/bot{}/'.format(TOKEN)
    url = url+'sendMessage?chat_id={}'.format(chat_id)

    r = requests.post(url, json={'text': text})
    print('Status Code: {}'.format(r.status_code))

    return None


def load_dataset(store_id):
    # Loading test dataset
    df10 = pd.read_csv('test.csv', low_memory=False)
    df_store = pd.read_csv('store.csv', low_memory=False)

    # Merge test dataset + store
    df_test = pd.merge(df10, df_store, how='left', on='Store')

    # Choose store for prediction
    df_test = df_test[df_test['Store'].isin([store_id])]

    if not df_test.empty:
        #remove closed days 
        df_test = df_test[df_test['Open'] != 0]
        df_test = df_test[~df_test['Open'].isnull()]
        df_test = df_test.drop('Id', axis=1)

        # Convert dataframe to json
        data = json.dumps(df_test.to_dict(orient='records'))
    else:
        data = 'error'

    return data

def predict(data):
    # API Call
    url = 'https://teste-rossmann.onrender.com/rossmann/predict'
    header = {'Content-type':'application/json'}
    data = data

    r = requests.post(url, data=data, headers=header)
    print('Status Code {}'.format(r.status_code))

    d1 = pd.DataFrame(r.json(), columns=r.json()[0].keys())

    return d1

def parse_message(message):
    chat_id = message['message']['chat']['id']
    store_id = message['message']['chat']['text']

    store_id.replace('/', '')

    try:
        store_id = int(store_id)
    except ValueError:
        store_id = 'error'
    
    return chat_id, store_id

    # d2 = d1[['Store', 'prediction']].groupby('Store').sum().reset_index()

    # for i in range(len(d2)):
    #     print('Store Number {} will sell R${:,.2f} in the next 6 weeks'.format(d2.loc[i, 'Store'], d2.loc[i, 'prediction'] ))

# API Initialize
app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        message = request.get_json()

        chat_id, store_id = parse_message()

        if store_id != 'error':
            # loading data
            data = load_dataset(store_id)
            
            if data != 'error':
                # prediction
                d1 = predict(data)
                # calculation
                d2 = d1[['Store', 'prediction']].groupby('Store').sum().reset_index()
                # send message
                msg = 'Store Number {} will sell €{:,.2f} in the next 6 weeks'.format(d2['Store'].values[0], d2['prediction'].values[0])
                send_message(chat_id, msg)
                return Response('OK', status=200)
            else:
                send_message(chat_id, 'Store id not available!')
                return Response('OK', status=200)
        else:
            send_message(chat_id, 'Store id is wrong!')
            return Response('OK', status=200)

    else:
        return '<h1> Rossmann Telegram Bot </h1>'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
