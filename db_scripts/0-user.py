import json

def populate(db, models, providers):
    UserProvider = providers.user_provider.UserProvider
    provider = UserProvider()
    with open('data/users.json') as file:
        data = json.load(file)
        for datum in data:
            provider.add(datum)
