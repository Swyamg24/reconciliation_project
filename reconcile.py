import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime
import os
def generate_sample_ledgers():
    print("Generating sample ledger data...")
    fake = Faker()
    if not os.path.exists('data'):
        os.makedirs('data')

    num_base_transactions = 100
    data = []
    for i in range(num_base_transactions):
        data.append({
            'TransactionID':f'TXN{1000+i}',
            'Date':fake.date_between(start_date='-30d',end_date='today'),
            'Description':fake.catch_phrase(),
            'Amount':round(random.uniform(10.50,500.99),2)
        })
    base_df = pd.DataFrame(data)
